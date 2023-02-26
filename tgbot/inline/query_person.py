import random

from telebot.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                           InlineQuery, InlineQueryResultArticle,
                           InputTextMessageContent)

from utils.config_vars import BOT_USERNAME, bgm


async def query_person_related_subjects(inline_query: InlineQuery, is_sender: bool):
    """PS + 人物ID 获取人物关联条目"""
    offset = int(inline_query.offset or 0)
    query_result_list: list[InlineQueryResultArticle] = []
    person_id = inline_query.query.split(" ")[1]

    person_related_subjects = await bgm.get_person_subjects(person_id)
    if person_related_subjects is None: return {"results": query_result_list}

    person_info = await bgm.get_person(person_id)
    switch_pm_text = person_info["name"] + " 关联条目"

    if is_sender:
        for subject in person_related_subjects[offset : offset + 50]:
            query_result_list.append(InlineQueryResultArticle(
                id=f"{subject['staff']}:{subject['id']}",
                title=(subject["name_cn"] if subject["name_cn"] else subject["name"]),
                input_message_content=InputTextMessageContent(
                    message_text=f"/info@{BOT_USERNAME} {subject['id']}", disable_web_page_preview=True
                ),
                description=(f"{subject['name']} | " if subject["name_cn"] else "") + (subject["staff"] if subject["staff"] else ""),
                thumb_url=subject["image"] if subject["image"] else None,
            ))
    else:
        for subject in person_related_subjects[offset : offset + 50]:
            text = f"*{subject['name_cn'] or subject['name']}*\n"
            text += f"{subject['name']}\n" if subject['name_cn'] else ''

            text += f"\n*BGM ID：*`{subject['id']}`"
            text += (
                f"\n📚 [简介](https://t.me/iv?url=https://bgm.tv/subject/{subject['id']}&rhash=ce4f44b013e2e8)"
                f"\n📖 [详情](https://bgm.tv/subject/{subject['id']})"
                f"\n💬 [吐槽箱](https://bgm.tv/subject/{subject['id']}/comments)"
            )

            button_list = [
                InlineKeyboardButton(text="巡礼", switch_inline_query_current_chat=f"anitabi {subject['id']}"),
                InlineKeyboardButton(text="角色", switch_inline_query_current_chat=f"SC {subject['id']}"),
                InlineKeyboardButton(text="人物", switch_inline_query_current_chat=f"SP {subject['id']}"),
                InlineKeyboardButton(text='去管理', url=f"t.me/{BOT_USERNAME}?start={subject['id']}"),
            ]
            query_result_list.append(InlineQueryResultArticle(
                id=f"{subject['staff']}:{subject['id']}",
                title=(subject["name_cn"] if subject["name_cn"] else subject["name"]),
                input_message_content=InputTextMessageContent(
                    text, parse_mode="markdown", disable_web_page_preview=False
                ),
                description=(f"{subject['name']} | " if subject["name_cn"] else '')
                + (subject['staff'] if subject["staff"] else ''),
                thumb_url=subject["image"] if subject["image"] else None,
                reply_markup=InlineKeyboardMarkup().add(*button_list),
            ))
    return {
        "results": query_result_list,
        "next_offset": str(offset + 50),
        "switch_pm_text": switch_pm_text,
        "switch_pm_parameter": "help",
        "cache_time": 3600,
    }


async def query_person_related_characters(inline_query: InlineQuery):
    """PC + 人物ID 获取人物关联角色"""
    offset = int(inline_query.offset or 0)
    query_result_list: list[InlineQueryResultArticle] = []
    person_id = inline_query.query.split(" ")[1]

    person_related_characters = await bgm.get_person_characters(person_id)
    if person_related_characters is None: return {"results": query_result_list}

    person_info = await bgm.get_person(person_id)
    switch_pm_text = person_info["name"] + " 关联角色"

    for character in person_related_characters[offset : offset + 49]:
        text = (
            f"*{character['name']}*"
            f"\n{character['subject_name_cn'] or character['subject_name']} | {character['staff']}\n"
            f"\n📚 [简介](https://t.me/iv?url=https://bangumi.tv/character/{character['id']}&rhash=48797fd986e111)"
            f"\n📖 [详情](https://bgm.tv/character/{character['id']})"
        )
        query_result_list.append(InlineQueryResultArticle(
            id = f"PC:{character['id']}:{str(random.randint(0, 1000000000))}",
            title = character["name"],
            description = f"{character['subject_name_cn'] or character['subject_name']} | {character['staff']}\n",
            input_message_content = InputTextMessageContent(
                text, parse_mode = "markdown", disable_web_page_preview = False
            ),
            thumb_url = character["images"]["grid"] if character["images"] else None,
        ))
    if len(person_related_characters) == 0:
        query_result_list.append(InlineQueryResultArticle(
            id="-1",
            title="这个人物没有关联角色QAQ",
            input_message_content=InputTextMessageContent(
                "点我干嘛!😡", parse_mode="markdown", disable_web_page_preview=False
            ),
            thumb_url=None,
        ))
    if len(person_related_characters) <= offset + 49:
        next_offset = None
    else:
        next_offset = offset + 49
    return {
        "results": query_result_list,
        "next_offset": next_offset,
        "switch_pm_text": switch_pm_text,
        "switch_pm_parameter": person_id,
        "cache_time": 3600,
    }