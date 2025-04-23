import json
import os
import asyncio
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import pytz
import matplotlib.pyplot as plt
import re

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TOKEN = os.getenv("BOT_TOKEN") or "your_token_here"
STATS_FILE = "stats.json"

# Экранирование MarkdownV2
def escape_markdown(text):
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!\\])', r'\\\1', str(text))

# Загрузка статистики
def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Сохранение статистики
def save_stats(data):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

stats = load_stats()

# Добавление сообщения в статистику
def increment_message_count(chat_id, user_id, username):
    today = datetime.now(pytz.timezone("Europe/Moscow")).date().isoformat()
    chat_id = str(chat_id)
    user_id = str(user_id)

    if chat_id not in stats:
        stats[chat_id] = {}
    if today not in stats[chat_id]:
        stats[chat_id][today] = {}
    if user_id not in stats[chat_id][today]:
        stats[chat_id][today][user_id] = {"username": username, "count": 0}
    stats[chat_id][today][user_id]["count"] += 1
    save_stats(stats)

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        chat_id = update.message.chat_id
        user = update.message.from_user
        increment_message_count(chat_id, user.id, user.username or user.full_name)

# Команда /stat
async def stat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id not in stats:
        await update.message.reply_text("Нет данных для этого чата.")
        return

    all_users = defaultdict(int)
    for day in stats[chat_id].values():
        for uid, data in day.items():
            all_users[uid] += data["count"]

    sorted_users = sorted(all_users.items(), key=lambda x: x[1], reverse=True)
    lines = ["🧾 *Общая статистика сообщений:*"]
    for uid, count in sorted_users:
        username = None
        for day in stats[chat_id].values():
            if uid in day:
                username = day[uid]["username"]
                break
        user_tag = f"@{escape_markdown(username)}" if username else f"ID\\:{uid}"
        lines.append(f"{user_tag} — {count} сообщений")

    await update.message.reply_text(escape_markdown("\n".join(lines)), parse_mode="MarkdownV2")

# Команда /top
async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id not in stats:
        await update.message.reply_text("Нет данных для этого чата.")
        return

    now = datetime.now(pytz.timezone("Europe/Moscow"))
    week_ago = now - timedelta(days=7)
    week_users = defaultdict(int)

    for date_str, users in stats[chat_id].items():
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        if date >= week_ago.date():
            for uid, data in users.items():
                week_users[uid] += data["count"]

    sorted_users = sorted(week_users.items(), key=lambda x: x[1], reverse=True)[:10]
    lines = ["🏆 *Топ 10 самых активных за неделю:*"]
    for i, (uid, count) in enumerate(sorted_users, 1):
        username = None
        for day in stats[chat_id].values():
            if uid in day:
                username = day[uid]["username"]
                break
        user_tag = f"@{escape_markdown(username)}" if username else f"ID\\:{uid}"
        lines.append(f"{i}. {user_tag} — {count} сообщений")

    await update.message.reply_text(escape_markdown("\n".join(lines)), parse_mode="MarkdownV2")

# Команда /graph
async def graph_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id not in stats:
        await update.message.reply_text("Нет данных для этого чата.")
        return

    now = datetime.now(pytz.timezone("Europe/Moscow"))
    week_ago = now - timedelta(days=6)
    user_daily = defaultdict(lambda: [0]*7)

    for i in range(7):
        day = (week_ago + timedelta(days=i)).date().isoformat()
        if day in stats[chat_id]:
            for uid, data in stats[chat_id][day].items():
                user_daily[data["username"]][i] = data["count"]

    plt.figure(figsize=(10, 6))
    for username, counts in user_daily.items():
        plt.plot(range(7), counts, label=username)

    days = [(week_ago + timedelta(days=i)).strftime("%a") for i in range(7)]
    plt.xticks(range(7), days)
    plt.title("Активность за последние 7 дней")
    plt.xlabel("Дни")
    plt.ylabel("Сообщения")
    plt.legend()
    plt.tight_layout()
    plt.savefig("graph.png")
    plt.close()

    with open("graph.png", "rb") as f:
        await update.message.reply_photo(f)

# Команда /motohelp
async def motohelp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📋 *Список доступных команд:*\n"
        "/stat — Общая статистика сообщений\n"
        "/top — Топ 10 активных участников за неделю\n"
        "/graph — График активности за неделю\n"
        "/motohelp — Список доступных команд"
    )
    await update.message.reply_text(escape_markdown(text), parse_mode="MarkdownV2")

# Планировщик еженедельной отправки
async def send_weekly_report(app):
    for chat_id in stats.keys():
        dummy_update = type("obj", (object,), {"effective_chat": type("chat", (), {"id": int(chat_id)})})()
        await top_command(dummy_update, None)
        await graph_command(dummy_update, None)

# Основной запуск
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CommandHandler("stat", stat_command))
    app.add_handler(CommandHandler("top", top_command))
    app.add_handler(CommandHandler("graph", graph_command))
    app.add_handler(CommandHandler("motohelp", motohelp_command))

    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(lambda: asyncio.create_task(send_weekly_report(app)), "cron", day_of_week="sun", hour=23, minute=59)
    scheduler.start()

    print("Бот запущен...")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
