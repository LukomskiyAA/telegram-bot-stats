
import random
from telegram.constants import ParseMode

def escape_markdown(text: str) -> str:
    """
    Экранирует специальные символы MarkdownV2
    """
    escape_chars = r"\\_*[]()~`>#+-=|{}.!"
    return ''.join(f'\\{c}' if c in escape_chars else c for c in text)

def get_top_users():
    """
    Возвращает список топ пользователей, отформатированный для MarkdownV2.
    Здесь имитируем фейковую статистику.
    """
    # Пример данных
    users = [
        {"username": "lukomskiy.aa", "count": 52},
        {"username": "cool_user", "count": 37},
        {"username": "test.user", "count": 29},
        {"username": "hello_world", "count": 21},
        {"username": "bot_fan_99", "count": 18}
    ]

    lines = ["*Топ активных пользователей:*"]
    for i, user in enumerate(users, 1):
        username = user["username"]
        escaped_username = escape_markdown(username)
        lines.append(f"{i}. [@{escaped_username}](https://t.me/{username}) — {user['count']} сообщений")

    return "\n".join(lines), ParseMode.MARKDOWN_V2
