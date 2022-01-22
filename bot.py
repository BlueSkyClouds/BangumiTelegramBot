#!/usr/bin/python
'''
https://bangumi.github.io/api/
'''

import datetime
import json
import logging

import requests
import telebot

import utils
from config import BOT_TOKEN, APP_ID, APP_SECRET, WEBSITE_BASE, BOT_USERNAME
from utils import requests_get
from utils import gender_week_message, gander_anime_message, grnder_rating_message, gender_anime_page_message, search_anime

logger = telebot.logger
# telebot.logger.setLevel(logging.DEBUG)  # Outputs debug messages to console.
logging.basicConfig(level=logging.INFO,
                    filename='run.log',
                    format='%(asctime)s - %(filename)s & %(funcName)s[line:%(lineno)d] - %(levelname)s: %(message)s')
# 请求TG Bot api
bot = telebot.TeleBot(BOT_TOKEN)

# 绑定 Bangumi
@bot.message_handler(commands=['start'])
def send_start(message):
    if message.chat.type == "private": # 当私人聊天
        test_id = message.from_user.id
        if data_seek_get(test_id):
            bot.send_message(message.chat.id, "已绑定", timeout=20)
        else:
            text = '请绑定您的Bangumi'
            url= f'{WEBSITE_BASE}oauth_index?tg_id={test_id}'
            markup = telebot.types.InlineKeyboardMarkup()
            markup.add(telebot.types.InlineKeyboardButton(text='绑定Bangumi',url=url))
            bot.send_message(message.chat.id, text=text, parse_mode='Markdown', reply_markup=markup ,timeout=20)
    else:
        if message.text == f'/start@{BOT_USERNAME}':
            bot.send_message(message.chat.id, '请私聊我进行Bangumi绑定', parse_mode='Markdown' ,timeout=20)
        else:
            pass

# 查询 Bangumi 用户收藏统计
@bot.message_handler(commands=['my'])
def send_my(message):
    message_data = message.text.split(' ')
    bgm_id = None
    access_token = None
    if len(message_data) == 1:
        # 未加参数 查询自己
        tg_id = message.from_user.id
        user_data = user_data_get(tg_id)
        if user_data is None:
            # 如果未绑定 直接报错
            bot.send_message(message.chat.id,
                             f"未绑定Bangumi，请私聊使用[/start](https://t.me/{BOT_USERNAME}?start=none)进行绑定",
                             parse_mode='Markdown', timeout=20)
            return
        bgm_id = user_data.get('user_id')
        access_token = user_data.get('access_token')
    else:
        # 加了参数 查参数中的人
        bgm_id = message_data[1]
        access_token = ''
    # 开始查询数据
    msg = bot.send_message(message.chat.id, "正在查询请稍候...", reply_to_message_id=message.message_id, parse_mode='Markdown', timeout=20)
    params = {'app_id': APP_ID}
    url = f'https://api.bgm.tv/user/{bgm_id}/collections/status'
    try:
        startus_data = requests_get(url=url, params=params, access_token=access_token)
        if startus_data is None:
            # Fixme 会有这种情况吗？
            bot.send_message(message.chat.id, text='出错了,没有获取到您的统计信息', parse_mode='Markdown', timeout=20)
            return
        if isinstance(startus_data, dict) and startus_data.get('code') == 404:
            bot.edit_message_text(text="出错了，没有查询到该用户", chat_id=message.chat.id, message_id=msg.message_id)
            return
        # 查询用户名
        user_data = requests_get(url=f'https://api.bgm.tv/user/{bgm_id}')
        if user_data is None:
            bot.edit_message_text(text="出错了,无法获取到您的个人信息", chat_id=message.chat.id, message_id=msg.message_id)
            return
        if isinstance(user_data, dict) and user_data.get('code') == 404:
            bot.edit_message_text(text="出错了，没有查询到该用户", chat_id=message.chat.id, message_id=msg.message_id)
            return
        nickname = user_data.get('nickname')
        bgm_id = user_data.get('id')
        ##### 开始处理数据
        book_do, book_collect, anime_do, anime_collect \
            , music_do, music_collect, game_do, game_collect = 0, 0, 0, 0, 0, 0, 0, 0
        for i in startus_data:
            if i.get('name') == 'book':
                for book in i.get('collects'):
                    if book.get('status').get('type') == 'do':
                        book_do = book.get('count')
                    if book.get('status').get('type') == 'collect':
                        book_collect = book.get('count')
            elif i.get('name') == 'anime':
                for anime in i.get('collects'):
                    if anime.get('status').get('type') == 'do':
                        anime_do = anime.get('count')
                    if anime.get('status').get('type') == 'collect':
                        anime_collect = anime.get('count')
            elif i.get('name') == 'music':
                for music in i.get('collects'):
                    if music.get('status').get('type') == 'do':
                        music_do = music.get('count')
                    if music.get('status').get('type') == 'collect':
                        music_collect = music.get('count')
            elif i.get('name') == 'game':
                for game in i.get('collects'):
                    if game.get('status').get('type') == 'do':
                        game_do = game.get('count')
                    if game.get('status').get('type') == 'collect':
                        game_collect = game.get('count')
        text = f'*Bangumi 用户数据统计：\n\n{nickname}*\n' \
               f'➤ 动画：`{anime_do}在看，{anime_collect}看过`\n' \
               f'➤ 图书：`{book_do}在读，{book_collect}读过`\n' \
               f'➤ 音乐：`{music_do}在听，{music_collect}听过`\n' \
               f'➤ 游戏：`{game_do}在玩，{game_collect}玩过`\n\n' \
               f'[🏠 个人主页](https://bgm.tv/user/{bgm_id})\n'
        img_url = f'https://bgm.tv/chart/img/{bgm_id}'
    except:
        bot.edit_message_text(text="系统错误，请查看日志", chat_id=message.chat.id, message_id=msg.message_id)
        raise
    bot.delete_message(message.chat.id, message_id=msg.message_id, timeout=20)
    bot.send_photo(chat_id=message.chat.id, photo=img_url, caption=text, parse_mode='Markdown')

# 动画条目搜索/查询 Bangumi 用户在看动画 重写
@bot.message_handler(commands=['anime'])
def send_anime(message):
    message_data = message.text.split(' ')
    if len(message_data) != 1:
        search_anime(message_data[1], message, bot)
        return
        pass  # TODO 条目搜索
    # 未加参数 查询自己
    tg_id = message.from_user.id
    offset = 0
    user_data = user_data_get(tg_id)
    if user_data is None:
        # 如果未绑定 直接报错
        bot.send_message(message.chat.id,
                         "未绑定Bangumi，请私聊使用[/start](https://t.me/" + BOT_USERNAME + "?start=none)进行绑定",
                         parse_mode='Markdown', timeout=20)
        return
    msg = bot.send_message(message.chat.id, "正在查询请稍候...", reply_to_message_id=message.message_id,
                           parse_mode='Markdown', timeout=20)
    try:
        page = gender_anime_page_message(user_data, offset, tg_id)
    except:
        bot.edit_message_text(text="出错了!请看日志", chat_id=message.chat.id, message_id=msg.message_id)
        raise
    bot.edit_message_text(text=page['text'], chat_id=msg.chat.id, message_id=msg.message_id, parse_mode='Markdown', reply_markup=page['markup'])

# 每日放送查询
@bot.message_handler(commands=['week'])
def send_week(message):
    data = message.text.split(' ')
    day = None
    if len(data) == 1:
        # 如果未传参数
        now_week = int(datetime.datetime.now().strftime("%w"))
        day = 7 if now_week == 0 else now_week
    else:
        if data[1].isdecimal() and 1 <= int(data[1]) <= 7:
            day = data[1]
        else:
            bot.send_message(message.chat.id, "输入错误 请输入：`/week 1~7`", parse_mode='Markdown', timeout=20)
            return
    msg = bot.send_message(message.chat.id, "正在搜索请稍候...", reply_to_message_id=message.message_id, parse_mode='Markdown',
                           timeout=20)
    week_data = gender_week_message(day)
    text = week_data['text']
    markup = week_data['markup']
    bot.edit_message_text(chat_id=message.chat.id, message_id=msg.id, text=text, parse_mode='Markdown', reply_markup=markup)

def data_seek_get(test_id):
    """ 判断是否绑定Bangumi """
    with open('bgm_data.json') as f:                        # 打开文件
        data_seek = json.loads(f.read())                    # 读取
    data_li = [i['tg_user_id'] for i in data_seek]          # 写入列表
    return int(test_id) in data_li                          # 判断列表内是否有被验证的UID

def user_data_get(test_id):
    """ 返回用户数据,如果过期则更新 """
    with open('bgm_data.json') as f:
        data_seek = json.loads(f.read())
    for i in data_seek:
        if i.get('tg_user_id') == test_id:
            expiry_time = i.get('expiry_time')
            now_time = datetime.datetime.now().strftime("%Y%m%d")
            if now_time >= expiry_time:   # 判断密钥是否过期
                return expiry_data_get(test_id)
            else:
                return i.get('data',{})

# 更新过期用户数据
def expiry_data_get(test_id):
    with open('bgm_data.json') as f:
        data_seek = json.loads(f.read())
    refresh_token = None
    for i in data_seek:
        if i.get('tg_user_id') == test_id:
            refresh_token = i.get('data',{}).get('refresh_token')
    CALLBACK_URL = f'{WEBSITE_BASE}oauth_callback'
    resp = requests.post(
        'https://bgm.tv/oauth/access_token',
        data={
            'grant_type': 'refresh_token',
            'client_id': APP_ID,
            'client_secret': APP_SECRET,
            'refresh_token': refresh_token,
            'redirect_uri': CALLBACK_URL,
        },
        headers = {
        "User-Agent": "",
        }
    )
    access_token = json.loads(resp.text).get('access_token')    #更新access_token
    refresh_token = json.loads(resp.text).get('refresh_token')  #更新refresh_token
    expiry_time = (datetime.datetime.now()+datetime.timedelta(days=7)).strftime("%Y%m%d")#更新过期时间

    # 替换数据
    if access_token or refresh_token != None:
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
            user_data = i.get('data',{})
    return user_data

# 获取BGM用户信息 TODO 存入数据库
def bgmuser_data(test_id):
    user = user_data_get(test_id)
    access_token = user['access_token']
    url = f"https://api.bgm.tv/user/{user['user_id']}"
    user_data = requests_get(url, access_token=access_token)
    user_data = {
        'nickname': user_data.get('nickname'), # 用户昵称 str
        'username': user_data.get('username')  # 用户username 没有设置则返回 uid str
    }
    return user_data

# 获取用户观看eps数据
def eps_get(test_id, subject_id):
    user_data = user_data_get(test_id)
    access_token = user_data['access_token']
    params = {
        'subject_id': subject_id,
        'type': 0}
    url = 'https://api.bgm.tv/v0/episodes'
    data_eps = requests_get(url, params, access_token)
    epsid_li = [i['id'] for i in data_eps['data']] # 所有eps_id

    params = {'subject_id': subject_id}
    url = f"https://api.bgm.tv/user/{user_data['user_id']}/progress"
    data_watched = requests_get(url, params, access_token)
    if data_watched is not None:
        watched_id_li = [i['id'] for i in data_watched['eps']] # 已观看 eps_id
    else:
        watched_id_li = [0] # 无观看集数
    eps_n = len(set(epsid_li)) # 总集数
    watched_n = len(set(epsid_li) & set(watched_id_li)) # 已观看了集数
    unwatched_id = epsid_li # 去除已观看过集数的 eps_id
    try:
        for watched_li in watched_id_li:
            unwatched_id.remove(watched_li)
    except ValueError:
        pass
    # 输出
    eps_data = {'progress': str(watched_n) + '/' + str(eps_n),   # 已观看/总集数 进度 str
                'watched': watched_n,                            # 已观看集数 int
                'eps_n': str(eps_n),                             # 总集数 str
                'unwatched_id': unwatched_id}                    # 未观看 eps_di list
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
    if rating == None or rating == 0:
        params = {"status": (None, status)}
    else:
        params = {"status": (None, status),"rating": (None, rating)}
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

# 条目搜索 不需Access Token
def search_get(keywords, type, start):
    """条目搜索 不需Access Token"""
    params = {
        'type': type,
        'start': start,
        'max_results': 5} # 每页最大条数 5 个
    url = f'https://api.bgm.tv/search/subject/{keywords}'
    data_search = requests_get(url, params=params)
    if data_search is not None:
        search_results_n = data_search['results']
        subject_id_li = [i['id'] for i in data_search['list']]
        name_li = [i['name'] for i in data_search['list']]
    else:
        search_results_n, subject_id_li, name_li = 0, 0, 0
    # 输出
    search_data = {'search_results_n': search_results_n, # 搜索结果数量 int
                   'subject_id_li': subject_id_li,       # 所有查询结果id列表 list
                   'name_li': name_li}                   # 所有查询结果名字列表 list
    return search_data

# 空按钮回调处理
@bot.callback_query_handler(func=lambda call: call.data == 'None')
def callback_None(call):
    bot.answer_callback_query(call.id)

# 动画在看详情
@bot.callback_query_handler(func=lambda call: call.data.split('|')[0] == 'anime_do')
def anime_do_callback(call):
    call_tg_id = call.from_user.id
    call_data = call.data.split('|')
    tg_id = int(call_data[1]) # 被请求用户 Telegram ID
    subject_id = call_data[2] # 剧集ID
    back = int(call_data[3])  # 是否是从其它功能页返回 是则为1 否则为2
    back_page = call_data[4]  # 返回在看列表页数
    if call_tg_id == tg_id:
        img_url = utils.anime_img(subject_id)
        user_collection_data = user_collection_get(tg_id, subject_id)
        eps_data = eps_get(tg_id, subject_id)
        anime_do_message = gander_anime_message(call_tg_id, subject_id, tg_id=tg_id, back_page=back_page, user_rating=user_collection_data, eps_data=eps_data)
        if back == 1:
            if call.message.content_type == 'photo':
                bot.edit_message_caption(caption=anime_do_message['text'], chat_id=call.message.chat.id , message_id=call.message.message_id, parse_mode='Markdown', reply_markup=anime_do_message['markup'])
            else:
                bot.edit_message_text(text=anime_do_message['text'], parse_mode='Markdown', chat_id=call.message.chat.id , message_id=call.message.message_id, reply_markup=anime_do_message['markup'])
        else:
            bot.delete_message(chat_id=call.message.chat.id , message_id=call.message.message_id, timeout=20) # 删除用户在看动画列表消息
            if img_url == 'None__' or not img_url: # 是否有动画简介图片
                bot.send_message(chat_id=call.message.chat.id, text=anime_do_message['text'], parse_mode='Markdown', reply_markup=anime_do_message['markup'], timeout=20)
            else:
                bot.send_photo(chat_id=call.message.chat.id, photo=img_url, caption=anime_do_message['text'], parse_mode='Markdown', reply_markup=anime_do_message['markup'])
        bot.answer_callback_query(call.id)
    else:
        bot.answer_callback_query(call.id, text='和你没关系，别点了~', show_alert=True)

# 评分
@bot.callback_query_handler(func=lambda call: call.data.split('|')[0] == 'rating')
def rating_callback(call):
    call_tg_id = call.from_user.id
    call_data = call.data.split('|')
    tg_id = int(call_data[1]) # 被请求更新用户 Telegram ID
    if call_tg_id == tg_id:
        rating_data = int(call_data[2]) # 用户请求评分 初始进入评分页为0
        subject_id = call_data[3] # 剧集ID
        back_page = call_data[4] # 返回在看列表页数
        eps_data = eps_get(tg_id, subject_id)
        user_collection_data = user_collection_get(tg_id, subject_id)
        user_now_rating = user_collection_data['rating']
        if rating_data != 0:
            user_startus = user_collection_data.get('status',{}).get('type')
            if user_startus is None:
                user_startus = 'collect'
            collection_post(tg_id, subject_id, user_startus, str(rating_data))
            bot.answer_callback_query(call.id, text="已成功更新评分,稍后更新当前页面...")
            user_collection_data = user_collection_get(tg_id, subject_id)
        rating_message = grnder_rating_message(tg_id, subject_id, eps_data, user_collection_data, back_page)
        if rating_data == 0 or user_now_rating != user_collection_data['rating']: # 当用户当前评分请求与之前评分不一致时
            if call.message.content_type == 'photo':
                bot.edit_message_caption(caption=rating_message['text'], chat_id=call.message.chat.id , message_id=call.message.message_id, parse_mode='Markdown', reply_markup=rating_message['markup'])
            else:
                bot.edit_message_text(text=rating_message['text'], parse_mode='Markdown', chat_id=call.message.chat.id , message_id=call.message.message_id, reply_markup=rating_message['markup'])
        bot.answer_callback_query(call.id)
    else:
        bot.answer_callback_query(call.id, text='和你没关系，别点了~', show_alert=True)

# 已看最新
@bot.callback_query_handler(func=lambda call: call.data.split('|')[0] == 'anime_eps')
def anime_eps_callback(call):
    call_tg_id = call.from_user.id
    call_data = call.data.split('|')
    tg_id = int(call_data[1]) # 被请求更新用户 Telegram ID
    if call_tg_id == tg_id:
        eps_id = int(call_data[2]) # 更新的剧集集数 ID
        if len(call_data) > 5:
            remove = call_data[5] # 撤销
            if remove == 'remove':
                eps_status_get(tg_id, eps_id, 'remove')  # 更新观看进度为撤销
                bot.send_message(chat_id=call.message.chat.id, text='已撤销最新观看进度', parse_mode='Markdown', timeout=20)
                bot.answer_callback_query(call.id, text='已撤销最新观看进度')
        else:
            eps_status_get(tg_id, eps_id, 'watched') # 更新观看进度为看过
            bot.answer_callback_query(call.id, text='已更新观看进度为看过')
        subject_id = int(call_data[3]) # 剧集ID
        back_page = call_data[4] # 返回在看列表页数
        user_collection_data = user_collection_get(tg_id, subject_id)
        eps_data = eps_get(tg_id, subject_id)
        anime_do_message = gander_anime_message(call_tg_id, subject_id, tg_id=tg_id, user_rating=user_collection_data, eps_data=eps_data, eps_id=eps_id, back_page=back_page)
        if eps_data['unwatched_id'] == []:
            status = 'collect'
            collection_post(tg_id, subject_id, status, str(user_collection_data['rating'])) # 看完最后一集自动更新收藏状态为看过
        if call.message.content_type == 'photo':
            bot.edit_message_caption(caption=anime_do_message['text'], chat_id=call.message.chat.id , message_id=call.message.message_id, parse_mode='Markdown', reply_markup=anime_do_message['markup'])
        else:
            bot.edit_message_text(text=anime_do_message['text'], parse_mode='Markdown', chat_id=call.message.chat.id , message_id=call.message.message_id, reply_markup=anime_do_message['markup'])
    else:
        bot.answer_callback_query(call.id, text='和你没关系，别点了~', show_alert=True)

# 动画在看列表 翻页
@bot.callback_query_handler(func=lambda call: call.data.split('|')[0] == 'anime_do_page')
def anime_do_page_callback(call):
    # call_tg_id = call.from_user.id
    msg = call.message
    call_data = call.data.split('|')
    tg_id = int(call_data[1]) # 被查询用户 Telegram ID
    # if str(call_tg_id) != tg_id:
    #     bot.answer_callback_query(call.id, text='和你没关系，别点了~', show_alert=True)
    #     return
    offset = int(call_data[2]) # 当前用户所请求的页数
    user_data = user_data_get(tg_id)
    page = gender_anime_page_message(user_data,offset,tg_id)
    if call.message.content_type == 'text':
        bot.edit_message_text(text=page['text'], chat_id=msg.chat.id, message_id=msg.message_id, parse_mode='Markdown', reply_markup=page['markup'])
    else:
        bot.delete_message(chat_id=msg.chat.id, message_id=msg.message_id)
        bot.send_message(text=page['text'], chat_id=msg.chat.id, parse_mode='Markdown', reply_markup=page['markup'])
    bot.answer_callback_query(call.id)

# 搜索翻页
@bot.callback_query_handler(func=lambda call: call.data.split('|')[0] == 'spage')
def spage_callback(call):
    call_data = call.data.split('|')
    anime_search_keywords = call_data[1] # 用户搜索关键字
    start = int(call_data[2]) # 当前用户所请求页数
    subject_type = 2 # 条目类型 1 = book 2 = anime 3 = music 4 = game 6 = real
    search_results_n = search_get(anime_search_keywords, subject_type, start)['search_results_n'] # 搜索结果数量
    markup = telebot.types.InlineKeyboardMarkup()
    if search_results_n == 0:
        text= '已经没有了'
    else:
        search_subject_id_li = search_get(anime_search_keywords, subject_type, start)['subject_id_li'] # 所有查询结果id列表
        search_name_li = search_get(anime_search_keywords, subject_type, start)['name_li'] # 所有查询结果名字列表
        for item in list(zip(search_name_li,search_subject_id_li)):
            markup.add(telebot.types.InlineKeyboardButton(text=item[0],callback_data='animesearch'+'|'+str(anime_search_keywords)+'|'+str(item[1])+'|'+str(start)+'|0'))

        if search_results_n <= 5:
            markup.add()
        elif start == 0:
            markup.add(telebot.types.InlineKeyboardButton(text='下一页',callback_data='spage'+'|'+str(anime_search_keywords)+'|'+str(start+5)))
        elif start+5 >= search_results_n:
            markup.add(telebot.types.InlineKeyboardButton(text='上一页',callback_data='spage'+'|'+str(anime_search_keywords)+'|'+str(start-5)))
        else:
            markup.add(telebot.types.InlineKeyboardButton(text='上一页',callback_data='spage'+'|'+str(anime_search_keywords)+'|'+str(start-5)),telebot.types.InlineKeyboardButton(text='下一页',callback_data='spage'+'|'+str(anime_search_keywords)+'|'+str(start+5)))

        text = {'*关于您的 “*`'+ str(anime_search_keywords) +'`*” 搜索结果*\n\n'+

                '🔍 共'+ str(search_results_n) +'个结果'}

    if call.message.content_type == 'photo':
        bot.delete_message(chat_id=call.message.chat.id , message_id=call.message.message_id, timeout=20)
        bot.send_message(chat_id=call.message.chat.id, text=text, parse_mode='Markdown', reply_markup=markup, timeout=20)
    else:
        bot.edit_message_text(text=text, parse_mode='Markdown', chat_id=call.message.chat.id , message_id=call.message.message_id, reply_markup=markup)
    bot.answer_callback_query(call.id)

# 搜索动画详情页 重写
@bot.callback_query_handler(func=lambda call: call.data.split('|')[0] == 'animesearch')
def animesearch_callback(call):
    call_tg_id = call.from_user.id
    call_data = call.data.split('|')
    anime_search_keywords = call_data[1] # 用户搜索关键字 如是从week请求则此参数为week
    subject_id = call_data[2] # 剧集ID
    start = int(call_data[3]) # 搜索时用户所在搜索页页数 如是从week请求则为week day
    back = int(call_data[4])  # 是否是从收藏页返回 是则为1 否则为2
    img_url = utils.anime_img(subject_id)
    anime_do_message = gander_anime_message(call_tg_id, subject_id, start=start, anime_search_keywords=anime_search_keywords)
    if back == 1:
        if call.message.content_type == 'photo':
                bot.edit_message_caption(caption=anime_do_message['text'], chat_id=call.message.chat.id , message_id=call.message.message_id, parse_mode='Markdown', reply_markup=anime_do_message['markup'])
        else:
            bot.edit_message_text(text=anime_do_message['text'], parse_mode='Markdown', chat_id=call.message.chat.id , message_id=call.message.message_id, reply_markup=anime_do_message['markup'])
    else:
        bot.delete_message(chat_id=call.message.chat.id , message_id=call.message.message_id, timeout=20)
        if img_url == 'None__' or not img_url:
            bot.send_message(chat_id=call.message.chat.id, text=anime_do_message['text'], parse_mode='Markdown', reply_markup=anime_do_message['markup'], timeout=20)
        else:
            bot.send_photo(chat_id=call.message.chat.id, photo=img_url, caption=anime_do_message['text'], parse_mode='Markdown', reply_markup=anime_do_message['markup'])
    bot.answer_callback_query(call.id)

# 收藏
@bot.callback_query_handler(func=lambda call: call.data.split('|')[0] == 'collection')
def collection_callback(call):
    call_tg_id = call.from_user.id
    call_data = call.data.split('|')
    tg_id = int(call_data[1]) # 被更新用户 Telegram ID
    subject_id = call_data[2] # 剧集ID
    anime_search_keywords = call_data[3] # 用户搜索关键字 如是从anime do请求则为anime_do
    start = call_data[4] # 搜索时用户所在搜索页页数 如是从week请求则为week day
    status = call_data[5] # 用户请求收藏状态 初始进入收藏页则为 null
    name = utils.get_subject_info(subject_id)['name']
    if status == 'null':
        if not data_seek_get(call_tg_id):
            bot.send_message(chat_id=call.message.chat.id, text=f'您未绑定Bangumi，请私聊使用[/start](https://t.me/{BOT_USERNAME}?start=none)进行绑定', parse_mode='Markdown', timeout=20)
        else:
            text = f'*您想将 “*`{name}`*” 收藏为*\n\n'
            markup = telebot.types.InlineKeyboardMarkup()
            button_list = []
            if anime_search_keywords == 'anime_do':
                back_page = call_data[6] # 返回在看列表页数
                button_list.append(telebot.types.InlineKeyboardButton(text='返回',callback_data=f'anime_do|{tg_id}|{subject_id}|1|{back_page}'))
            else:
                button_list.append(telebot.types.InlineKeyboardButton(text='返回',callback_data=f'animesearch|{anime_search_keywords}|{subject_id}|{start}|1'))
            button_list.append(telebot.types.InlineKeyboardButton(text='想看',callback_data=f'collection|{call_tg_id}|{subject_id}|{anime_search_keywords}|{start}|wish'))
            button_list.append(telebot.types.InlineKeyboardButton(text='看过',callback_data=f'collection|{call_tg_id}|{subject_id}|{anime_search_keywords}|{start}|collect'))
            button_list.append(telebot.types.InlineKeyboardButton(text='在看',callback_data=f'collection|{call_tg_id}|{subject_id}|{anime_search_keywords}|{start}|do'))
            button_list.append(telebot.types.InlineKeyboardButton(text='搁置',callback_data=f'collection|{call_tg_id}|{subject_id}|{anime_search_keywords}|{start}|on_hold'))
            button_list.append(telebot.types.InlineKeyboardButton(text='抛弃',callback_data=f'collection|{call_tg_id}|{subject_id}|{anime_search_keywords}|{start}|dropped'))
            markup.add(*button_list, row_width=3)
            if call.message.content_type == 'photo':
                bot.edit_message_caption(caption=text, chat_id=call.message.chat.id , message_id=call.message.message_id, parse_mode='Markdown', reply_markup=markup)
            else:
                bot.edit_message_text(text=text, parse_mode='Markdown', chat_id=call.message.chat.id , message_id=call.message.message_id, reply_markup=markup)
            bot.answer_callback_query(call.id)
    if call_tg_id == tg_id:
        rating = str(user_collection_get(tg_id, subject_id).get('rating'))
        if status == 'wish':    # 想看
            collection_post(tg_id, subject_id, status, rating)
            bot.send_message(chat_id=call.message.chat.id, text=f'已将 “`{name}`” 收藏更改为想看', parse_mode='Markdown', timeout=20)
            bot.answer_callback_query(call.id, text='已将收藏更改为想看')
        if status == 'collect': # 看过
            collection_post(tg_id, subject_id, status, rating)
            bot.send_message(chat_id=call.message.chat.id, text=f'已将 “`{name}`” 收藏更改为看过', parse_mode='Markdown', timeout=20)
            bot.answer_callback_query(call.id, text='已将收藏更改为看过')
        if status == 'do':      # 在看
            collection_post(tg_id, subject_id, status, rating)
            bot.send_message(chat_id=call.message.chat.id, text=f'已将 “`{name}`” 收藏更改为在看', parse_mode='Markdown', timeout=20)
            bot.answer_callback_query(call.id, text='已将收藏更改为在看')
        if status == 'on_hold': # 搁置
            collection_post(tg_id, subject_id, status, rating)
            bot.send_message(chat_id=call.message.chat.id, text=f'已将 “`{name}`” 收藏更改为搁置', parse_mode='Markdown', timeout=20)
            bot.answer_callback_query(call.id, text='已将收藏更改为搁置')
        if status == 'dropped': # 抛弃
            collection_post(tg_id, subject_id, status, rating)
            bot.send_message(chat_id=call.message.chat.id, text=f'已将 “`{name}`” 收藏更改为抛弃', parse_mode='Markdown', timeout=20)
            bot.answer_callback_query(call.id, text='已将收藏更改为抛弃')
    else:
         bot.answer_callback_query(call.id, text='和你没关系，别点了~', show_alert=True)

# week 返回
@bot.callback_query_handler(func=lambda call: call.data.split('|')[0] == 'back_week')
def back_week_callback(call):
    day = int(call.data.split('|')[1]) # week day
    week_data = gender_week_message(day)
    bot.delete_message(chat_id=call.message.chat.id , message_id=call.message.message_id, timeout=20)
    bot.send_message(chat_id=call.message.chat.id, text=week_data['text'], parse_mode='Markdown', reply_markup=week_data['markup'], timeout=20)
    bot.answer_callback_query(call.id)


# 开始启动
if __name__ == '__main__':
    bot.infinity_polling()
