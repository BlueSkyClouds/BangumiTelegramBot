"""api 调用"""
import time
import json
import redis
import random
import logging
import requests

import datetime
import schedule
import threading

from typing import Optional

from config import APP_ID, APP_SECRET, WEBSITE_BASE, REDIS_HOST, REDIS_PORT, REDIS_DATABASE
# FIXME 似乎不应该在这里创建对象
redis_cli = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DATABASE)


def data_seek_get(test_id):
    """ 判断是否绑定Bangumi """
    with open('bgm_data.json') as f:  # 打开文件
        data_seek = json.loads(f.read())  # 读取
    data_li = [i['tg_user_id'] for i in data_seek]  # 写入列表
    return int(test_id) in data_li  # 判断列表内是否有被验证的UID


def user_data_get(test_id):
    """ 返回用户数据,如果过期则更新 """
    with open('bgm_data.json') as f:
        data_seek = json.loads(f.read())
    for i in data_seek:
        if i.get('tg_user_id') == test_id:
            expiry_time = i.get('expiry_time')
            now_time = datetime.datetime.now().strftime("%Y%m%d")
            if now_time >= expiry_time:  # 判断密钥是否过期
                return expiry_data_get(test_id)
            else:
                return i.get('data', {})


def expiry_data_get(test_id):
    """更新过期用户数据"""
    with open('bgm_data.json') as f:
        data_seek = json.loads(f.read())
    refresh_token = None
    for i in data_seek:
        if i.get('tg_user_id') == test_id:
            refresh_token = i.get('data', {}).get('refresh_token')
    callback_url = f'{WEBSITE_BASE}oauth_callback'
    resp = requests.post(
        'https://bgm.tv/oauth/access_token',
        data={
            'grant_type': 'refresh_token',
            'client_id': APP_ID,
            'client_secret': APP_SECRET,
            'refresh_token': refresh_token,
            'redirect_uri': callback_url,
        },
        headers={
            "User-Agent": "",
        }
    )
    access_token = json.loads(resp.text).get('access_token')  # 更新access_token
    refresh_token = json.loads(resp.text).get(
        'refresh_token')  # 更新refresh_token
    expiry_time = (datetime.datetime.now() +
                   datetime.timedelta(days=7)).strftime("%Y%m%d")  # 更新过期时间

    # 替换数据
    if access_token or refresh_token is not None:
        with open("bgm_data.json", 'r+', encoding='utf-8') as f:
            data = json.load(f)
            for i in data:
                if i['tg_user_id'] == test_id:
                    i['data']['access_token'] = access_token
                    i['data']['refresh_token'] = refresh_token
                    i['expiry_time'] = expiry_time
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=4)
            f.truncate()

    # 读取数据
    with open('bgm_data.json') as f:
        data_seek = json.loads(f.read())
    user_data = None
    for i in data_seek:
        if i.get('tg_user_id') == test_id:
            user_data = i.get('data', {})
    return user_data


# 获取BGM用户信息 TODO 存入数据库
def bgmuser_data(test_id):
    user = user_data_get(test_id)
    access_token = user['access_token']
    url = f"https://api.bgm.tv/user/{user['user_id']}"
    user_data = requests_get(url, access_token=access_token)
    return user_data


@schedule.repeat(schedule.every().day)
def check_expiry_user():
    """检查是否有过期用户"""
    data_seek = []
    with open('bgm_data.json') as f:
        data_seek = json.loads(f.read())
    for i in data_seek:
        expiry_time = i.get('expiry_time')
        now_time = datetime.datetime.now().strftime("%Y%m%d")
        if now_time >= expiry_time:  # 判断密钥是否过期
            expiry_data_get(i.get('tg_user_id'))


def run_continuously(interval=1):
    """Continuously run, while executing pending jobs at each
    elapsed time interval.
    @return cease_continuous_run: threading. Event which can
    be set to cease continuous run. Please note that it is
    *intended behavior that run_continuously() does not run
    missed jobs*. For example, if you've registered a job that
    should run every minute and you set a continuous run
    interval of one hour then your job won't be run 60 times
    at each interval but only once.
    https://schedule.readthedocs.io/en/stable/background-execution.html
    """
    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            while not cease_continuous_run.is_set():
                schedule.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread()
    continuous_thread.start()
    return cease_continuous_run


def requests_get(url, params: Optional[dict] = None, access_token: Optional[str] = None, max_retry_times: int = 3):
    """requests_get 请求"""
    r = None
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'}
    if access_token is not None:
        headers.update({'Authorization': 'Bearer ' + access_token})
    for num in range(max_retry_times):  # 如api请求错误 重试3次
        try:
            r = requests.get(url=url, params=params, headers=headers)
        except requests.ConnectionError as err:
            if num + 1 >= max_retry_times:
                raise
            else:
                logging.warning(f'api请求错误，重试中...{str(err)}')
    if r.status_code != 200:
        raise requests.exceptions.BaseHTTPError(r.status_code)
    else:
        try:
            return json.loads(r.text)
        except json.JSONDecodeError:
            raise


def eps_get(test_id, subject_id):
    """获取用户观看eps数据"""
    user_data = user_data_get(test_id)
    access_token = user_data['access_token']
    params = {
        'subject_id': subject_id,
        'type': 0}
    url = 'https://api.bgm.tv/v0/episodes'
    data_eps = requests_get(url, params, access_token)
    epsid_li = [i['id'] for i in data_eps['data']]  # 所有eps_id

    params = {'subject_id': subject_id}
    url = f"https://api.bgm.tv/user/{user_data['user_id']}/progress"
    data_watched = requests_get(url, params, access_token)
    if data_watched is not None:
        watched_id_li = [i['id'] for i in data_watched['eps']]  # 已观看 eps_id
    else:
        watched_id_li = [0]  # 无观看集数
    eps_n = len(set(epsid_li))  # 总集数
    watched_n = len(set(epsid_li) & set(watched_id_li))  # 已观看了集数
    unwatched_id = epsid_li  # 去除已观看过集数的 eps_id
    try:
        for watched_li in watched_id_li:
            unwatched_id.remove(watched_li)
    except ValueError:
        pass
    # 输出
    eps_data = {'progress': str(watched_n) + '/' + str(eps_n),  # 已观看/总集数 进度 str
                'watched': watched_n,  # 已观看集数 int
                'eps_n': str(eps_n),  # 总集数 str
                'unwatched_id': unwatched_id}  # 未观看 eps_di list
    return eps_data


# 更新收视进度状态
def eps_status_get(test_id, eps_id, status):
    """更新收视进度状态"""
    access_token = user_data_get(test_id).get('access_token')
    url = f'https://api.bgm.tv/ep/{eps_id}/status/{status}'
    return requests_get(url, access_token=access_token)


# 更新收藏状态
def collection_post(test_id, subject_id, status, rating):
    """更新收藏状态"""
    access_token = user_data_get(test_id).get('access_token')
    if not rating:
        params = {"status": (None, status)}
    else:
        params = {"status": (None, status), "rating": (None, rating)}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36',
        'Authorization': 'Bearer ' + access_token}
    url = f'https://api.bgm.tv/collection/{subject_id}/update'
    r = requests.post(url=url, files=params, headers=headers)
    return r


# 获取指定条目收藏信息
def user_collection_get(test_id, subject_id):
    """获取指定条目收藏信息"""
    access_token = user_data_get(test_id).get('access_token')
    url = f'https://api.bgm.tv/collection/{subject_id}'
    return requests_get(url, access_token=access_token)


def post_collection(tg_id, subject_id, status, comment=None, tags=None, rating=None, private=None):
    r"""管理收藏

    :param tg_id: Telegram 用户id
    :param subject_id: 条目id
    :param status: 状态 wish collect do on_hold dropped
    :param comment: 简评
    :param tags: 标签 以半角空格分割
    :param rating: 评分 1-10 不填默认重置为未评分
    :param private: 收藏隐私 0 = 公开 1 = 私密 不填默认为0
    :return 请求结果
    """
    access_token = user_data_get(tg_id).get('access_token')
    params = {"status": status}  #
    if comment is not None:
        params['comment'] = comment
    if tags is not None:
        params['tags'] = tags
    if rating is not None:
        params['rating'] = rating
    if private is not None:
        params['private'] = private
    headers = {'Authorization': f'Bearer {access_token}'}
    url = f'https://api.bgm.tv/collection/{subject_id}/update'
    return requests.post(url=url, data=params, headers=headers)


def get_calendar() -> dict:
    """获取每日放送动漫"""
    data = redis_cli.get("calendar")
    if data:
        return json.loads(data)
    else:
        calendar = requests_get(url='https://api.bgm.tv/calendar')
        redis_cli.set("calendar", json.dumps(calendar), ex=3600)
        return calendar


def get_subject_info(subject_id, t_dict=None):
    """获取指定条目信息 并使用Redis缓存"""
    subject = redis_cli.get(f"subject:{subject_id}")
    if subject:
        loads = json.loads(subject)
    elif subject == "None__":
        raise FileNotFoundError(f"subject_id:{subject_id}获取失败_缓存")
    else:
        url = f'https://api.bgm.tv/v0/subjects/{subject_id}'
        loads = requests_get(url=url)
        if loads is None:
            redis_cli.set(f"subject:{subject_id}",
                          "None__", ex=60 * 10)  # 不存在时 防止缓存穿透
            raise FileNotFoundError(f"subject_id:{subject_id}获取失败")
        loads['_air_weekday'] = None
        for info in loads['infobox']:
            if info['key'] == '放送星期':
                loads['_air_weekday'] = info['value']  # 加一个下划线 用于区别
                break
        redis_cli.set(f"subject:{subject_id}", json.dumps(
            loads), ex=60 * 60 * 24 + random.randint(-3600, 3600))
    if t_dict:
        t_dict["subject_info"] = loads
    return loads


def anime_img(subject_id):
    """动画简介图片获取 不需Access Token 并使用Redis缓存"""
    img_url = redis_cli.get(f"anime_img:{subject_id}")
    if img_url:
        return img_url.decode()
    if img_url == "None__":
        return None
    anime_name = get_subject_info(subject_id)['name']
    query = '''
    query ($id: Int, $page: Int, $perPage: Int, $search: String) {
        Page (page: $page, perPage: $perPage) {
            media (id: $id, search: $search) {
                id
            }
        }
    }
    '''
    variables = {
        'search': anime_name,
        'page': 1,
        'perPage': 1
    }
    url = 'https://graphql.anilist.co'
    try:
        r = requests.post(url, json={'query': query, 'variables': variables})
    except requests.ConnectionError:
        r = requests.post(url, json={'query': query, 'variables': variables})
    anilist_data = json.loads(r.text).get('data').get('Page').get('media')
    if len(anilist_data) > 0:
        img_url = f'https://img.anili.st/media/{anilist_data[0]["id"]}'
        redis_cli.set(f"anime_img:{subject_id}", img_url,
                      ex=60 * 60 * 24 + random.randint(-3600, 3600))
        return img_url
    else:
        redis_cli.set(f"anime_img:{subject_id}",
                      "None__", ex=60 * 10)  # 不存在时 防止缓存穿透
        return None


def search_subject(keywords: str,
                   type_: int = None,
                   response_group: str = 'small',
                   start: int = 0,
                   max_results: int = 25) -> dict:
    """搜索条目

    :param keywords: 关键词
    :param type_: 条目类型 1=book 2=anime 3=music 4=game 6=real
    :param response_group: 返回数据大小 small medium
    :param start: 开始条数
    :param max_results: 每页条数 最多 25
    """
    params = {"type": type_, "responseGroup": response_group,
              "start": start, "max_results": max_results}
    url = f'https://api.bgm.tv/search/subject/{keywords}'
    try:
        r = requests.get(url=url, params=params)
    except requests.ConnectionError:
        r = requests.get(url=url, params=params)
    try:
        j = json.loads(r.text)
    except:
        return {"results": 0, 'list': []}
    return j


def get_collection(subject_id: str, token: str = "", tg_id=""):
    """获取用户指吧定条目收藏信息 token 和tg_id须传一个"""
    if token == "":
        if tg_id == "":
            raise ValueError("参数错误,token 和tg_id须传一个")
        from bot import user_data_get
        token = user_data_get(tg_id).get('access_token')
    if subject_id is None or subject_id == "":
        raise ValueError("subject_id不能为空")
    url = f"https://api.bgm.tv/collection/{subject_id}"
    return requests_get(url=url, access_token=token)


def get_user(bgm_id: str) -> dict:
    """通过bgm_id 获取用户名"""
    data = redis_cli.get(f"bgm_user:{bgm_id}")
    if data:
        if data != "None__":
            return json.loads(data)
        else:
            raise FileNotFoundError
    user_data = requests_get(f'https://api.bgm.tv/user/{bgm_id}')
    if isinstance(user_data, dict) and user_data.get('code') == 404:
        redis_cli.set(f"bgm_user:{bgm_id}", "None__", ex=3600)
        raise FileNotFoundError
    else:
        redis_cli.set(f"bgm_user:{bgm_id}", json.dumps(
            user_data), ex=3600 * 24 * 7)
        return user_data