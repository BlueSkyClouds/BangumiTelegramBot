"""类型转换"""
from typing import Literal


def subject_type_to_emoji(type_: Literal[1, 2, 3, 4, 6]) -> str:
    """将subject_type转emoji"""
    if type_ == 1:
        return "📚"
    elif type_ == 2:
        return "🌸"
    elif type_ == 3:
        return "🎵"
    elif type_ == 4:
        return "🎮"
    elif type_ == 6:
        return "📺"


def number_to_week(num: int) -> str:
    """将week day转换成星期"""
    if num == 1:
        return "星期一"
    if num == 2:
        return "星期二"
    if num == 3:
        return "星期三"
    if num == 4:
        return "星期四"
    if num == 5:
        return "星期五"
    if num == 6:
        return "星期六"
    if num == 7:
        return "星期日"
    else:
        return "未知"


def parse_markdown_v2(text: str) -> str:
    """markdown_v2 转译"""
    return text.translate(str.maketrans(
        {'_': '\\_',
         '*': '\\*',
         '[': '\\[',
         ']': '\\]',
         '(': '\\(',
         ')': '\\)',
         '~': '\\~',
         '`': '\\`',
         '>': '\\>',
         '#': '\\#',
         '+': '\\+',
         '-': '\\-',
         '=': '\\=',
         '|': '\\|',
         '{': '\\{',
         '}': '\\}',
         '.': '\\.',
         '!': '\\!'}))


def number_to_episode_type(type_: Literal[0, 1, 2, 3]) -> str:
    if type_ == 0:
        return "ep"
    if type_ == 1:
        return "sp"
    if type_ == 2:
        return "op"
    if type_ == 3:
        return "ed"


def collection_type_subject_type_str(subject_type: Literal[1, 2, 3, 4, 6],
                                     collection_type: Literal[1, 2, 3, 4, 5, None]):
    if collection_type is None:
        return "收藏"
    if collection_type == 5:
        return "抛弃"
    if collection_type == 4:
        return "搁置"
    if collection_type == 3:
        if subject_type == 1:
            return "在读"
        if subject_type == 2:
            return "在看"
        if subject_type == 3:
            return "在听"
        if subject_type == 4:
            return "在玩"
        if subject_type == 6:
            return "在看"
    if collection_type == 2:
        if subject_type == 1:
            return "读过"
        if subject_type == 2:
            return "看过"
        if subject_type == 3:
            return "听过"
        if subject_type == 4:
            return "玩过"
        if subject_type == 6:
            return "看过"
    if collection_type == 1:
        if subject_type == 1:
            return "想读"
        if subject_type == 2:
            return "想看"
        if subject_type == 3:
            return "想听"
        if subject_type == 4:
            return "想玩"
        if subject_type == 6:
            return "想看"
    return "????"


def subject_type_to_str(type_: Literal[1, 2, 3, 4, 6]) -> str:
    """将subject_type转文字"""
    if type_ == 1:
        return "书籍"
    elif type_ == 2:
        return "动画"
    elif type_ == 3:
        return "音乐"
    elif type_ == 4:
        return "游戏"
    elif type_ == 6:
        return "剧集"
    else:
        return "???"


def remove_duplicate_newlines(text: str) -> str:
    """删除重行 够用就行 懒的搞正则"""
    return text.translate(str.maketrans({'\n\n': '\n', '\n\n\n': '\n'}))
