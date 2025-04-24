import json
from telegram.constants import ParseMode

def escape_markdown(text: str) -> str:
    """
    Экранирует специальные символы MarkdownV2
    """
    escape_chars = r"\\_*[]()~`>#+-=|{}.!"
    return ''.join(f'\\{c}' if c in escape_chars else c for c in text)

def get_top_users():
    """
    Возвращает топ пользователей из файла stats.json.
    Если файл не найден — возвращает фейковые данные.
    """
    try:
        with open("stats.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return sorted(data, key=lambda x: x["message_count"], reverse=True)[:10]
    except Exception as e:
        # Фейковые данные
        users = [
            {"username": "lukomskiy.aa", "user_id": 123, "message_count": 52},
            {"username": "cool_user", "user_id": 124, "message_count": 37},
            {"username": "test.user", "user_id": 125, "message_count": 29},
            {"username": "hello_world", "user_id": 126, "message_count": 21},
            {"username": "bot_fan_99", "user_id": 127, "message_count": 18}
        ]
        return users
