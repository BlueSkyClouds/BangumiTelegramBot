"""评分页"""
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from ..model.page_model import (BackRequest, DoEditRatingRequest,
                                EditRatingPageRequest)


def do(request: DoEditRatingRequest, tg_id: int) -> DoEditRatingRequest:  # 返回在看列表页数
    user_status = request.user_collection.get('status', {}).get('type')
    if user_status is None:
        user_status = 'collect'
    # post_collection(tg_id, subject_info["id"], status=user_status, rating=str(request.rating_num)) TODO
    if request.rating_num == 0:
        request.callback_text = "已成功撤销评分"
    else:
        request.callback_text = f"已成功更新评分为{request.rating_num}分"
    return request


def generate_page(request: EditRatingPageRequest) -> EditRatingPageRequest:
    session_uuid = request.session.uuid
    subject_info = request.user_collection["subject"]
    text = (
        f"*{subject_info['name_cn']}*\n"
        f"{subject_info['name']}\n\n"
        f"*BGM ID：*`{subject_info['id']}`\n"
        f"*➤ BGM 平均评分：*`{subject_info['score']}`🌟\n"
         "*➤ 您的评分：*"
    )
    text += f"`{request.user_collection['rate']}`🌟\n" if request.user_collection['rate'] != 0 else "暂未评分\n"
    text += f"*➤ 观看进度：*`{request.user_collection['ep_status']}/{subject_info['eps']}`\n"
    text += f"\n💬 [吐槽箱](https://bgm.tv/subject/{subject_info['id']}/comments)\n请点按下列数字进行评分"
    markup = InlineKeyboardMarkup()
    nums = range(1, 11)
    button_list = []
    for num in nums:
        button_list.append(InlineKeyboardButton(text=str(num), callback_data=f'{session_uuid}|{num}'))
        do_edit_rating_request = DoEditRatingRequest(request.session, subject_info["id"], num)
        do_edit_rating_request.user_collection = request.user_collection
        request.possible_request[str(num)] = do_edit_rating_request
    markup.add(*button_list, row_width=5)
    markup.add(
        InlineKeyboardButton(text='返回', callback_data=f'{session_uuid}|back'),
        InlineKeyboardButton(text='删除评分', callback_data=f"{session_uuid}|0")
    )
    request.possible_request['back'] = BackRequest(request.session)
    do_edit_rating_request = DoEditRatingRequest(request.session, subject_info["id"], 0)
    do_edit_rating_request.user_collection = request.user_collection
    request.possible_request['0'] = do_edit_rating_request

    request.page_text = text
    request.page_markup = markup
    return request
