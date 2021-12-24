#!/usr/bin/python
import json
import telebot
import requests
from config import BOT_TOKEN, APP_ID, WEBSITE_BASE

# 请求TG Bot api
bot = telebot.TeleBot(BOT_TOKEN)

# 检测命令
@bot.message_handler(commands=['start'])
def send_hideit(message):
    if message.chat.type == "private": # 当私人聊天
        test_id = message.from_user.id
        if data_seek_get(test_id) == 'yes':
            bot.send_message(message.chat.id, "已绑定", timeout=20)
        else:
            text = {'请绑定您的Bangumi'}
            url= f'{WEBSITE_BASE}oauth_index?tg_id='+ str(test_id)
            markup = telebot.types.InlineKeyboardMarkup()    
            markup.add(telebot.types.InlineKeyboardButton(text='绑定Bangumi',url=url))
            bot.send_message(message.chat.id, text=text, parse_mode='Markdown', reply_markup=markup ,timeout=20)
    else:
        bot.send_message(message.chat.id, '请私聊我进行Bangumi绑定', parse_mode='Markdown' ,timeout=20)

@bot.message_handler(commands=['my'])
def send_hideit(message):
    test_id = message.from_user.id
    if data_seek_get(test_id) == 'no':
        bot.send_message(message.chat.id, "未绑定Bangumi，请使用 /start 进行绑定", parse_mode='Markdown', timeout=20)
    else:
        access_token = user_data_get(test_id).get('access_token')
        params = {'app_id': APP_ID}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36',
            'Authorization': 'Bearer ' + access_token}
        url = 'https://api.bgm.tv/user/' + str(user_data_get(test_id).get('user_id')) + '/collections/status'
        r = requests.get(url=url, params=params, headers=headers)

        startus_data = json.loads(r.text)
        book_do = 0
        book_collect = 0
        for i in startus_data:
            if i.get('name') == 'book':
                book_do = i.get('collects',{})[0].get('count')
                book_collect = i.get('collects',{})[1].get('count')
        anime_do = 0
        anime_collect = 0
        for i in startus_data:
            if i.get('name') == 'anime':
                anime_do = i.get('collects',{})[0].get('count')
                anime_collect = i.get('collects',{})[1].get('count')
        music_do = 0
        music_collect = 0
        for i in startus_data:
            if i.get('name') == 'music':
                music_do = i.get('collects',{})[0].get('count')
                # music_collect = i.get('collects',{})[1].get('count')
        game_do = 0
        game_collect = 0
        for i in startus_data:
            if i.get('name') == 'music':
                game_do = i.get('collects',{})[0].get('count')
                # game_collect = i.get('collects',{})[1].get('count')

        url2 = 'https://api.bgm.tv/user/' + str(user_data_get(test_id).get('user_id'))
        r2 = requests.get(url=url2, headers=headers)
        nickname = json.loads(r2.text).get('nickname')

        text = {'*'+ nickname +'*\n\n'
                '动画：'+ str(anime_do) +'在看，'+ str(anime_collect) +'看过\n'
                '图书：'+ str(book_do)  +'在读，'+ str(book_collect)  +'读过\n'
                '音乐：'+ str(music_do) +'在听，'+ str(music_collect) +'听过\n'
                '游戏：'+ str(game_do)  +'在玩，'+ str(game_collect)  +'玩过'
                }

        bot.send_message(message.chat.id, text=text, parse_mode='Markdown', timeout=20)
        
# 判断是否授权
def data_seek_get(test_id):
    with open('bgm_data.json') as f:                        # 打开文件
        data_seek = json.loads(f.read())                    # 读取
    data_li = [i['tg_user_id'] for i in data_seek]          # 写入列表
    if int(test_id) in data_li:                             # 判断列表内是否有被验证的UID
        data_back = 'yes'
    else:
        data_back = 'no'
    return data_back                                        # 返回是否重复验证

# 获取用户数据
def user_data_get(test_id):
    with open('bgm_data.json') as f:
        data_seek = json.loads(f.read())
    user_data = None
    for i in data_seek:
        if i.get('tg_user_id') == test_id:
            user_data = i.get('data',{})
    return user_data

# 开始启动
if __name__ == '__main__':
    bot.polling()