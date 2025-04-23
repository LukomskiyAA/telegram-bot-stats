
import json
import os
import asyncio
import logging
from datetime import datetime, timedelta
import pytz
from collections import defaultdict
import matplotlib.pyplot as plt

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("BOT_TOKEN") or "8164071818:AAFCBZTKBXcCbxLdmN1uyjRT26X_w4abjVY"
STATS_FILE = "stats.json"

# Загрузка и сохранение статистики
def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_stats(stats):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

# Глобальная переменная для хранения статистики
stats = load_stats()

# Обработка сообщений
def increment_message_count(chat_id, user_id, username):
    today = datetime.now(pytz.timezone("Europe/Moscow")).date().isoformat()
    if chat_id not in stats:
        stats[chat_id] = {}
    if today not in stats[chat_id]:
        stats[chat_id][today] = {}
    if str(user_id) not in stats[chat_id][today]:
        stats[chat_id][today][str(user_id)] = {"username": username, "count": 0}
    stats[chat_id][today][str(user_id)]["count"] += 1
    save_stats(stats)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        user = update.message.from_user
        chat_id = str(update.message.chat_id)
        increment_message_count(chat_id, user.id, user.username or user.full_name)

# Команды
async def stat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    all_users = defaultdict(int)
    chat_stats = stats.get(chat_id, {})
    for day in chat_stats.values():
        for uid, data in day.items():
            all_users[uid] += data["count"]

    sorted_users = sorted(all_users.items(), key=lambda x: x[1], reverse=True)
    lines = ["🧾 *Общая статистика сообщений:*"]
    for uid, count in sorted_users:
        username = None
        for day in chat_stats.values():
            if uid in day:
                username = day[uid]["username"]
                break
        user_tag = f"@{username}" if username else f"ID:{uid}"
        lines.append(f"{user_tag} — {count} сообщений")

    await update.message.reply_text("
".join(lines), parse_mode="Markdown")

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    now = datetime.now(pytz.timezone("Europe/Moscow"))
    week_ago = now - timedelta(days=7)
    week_users = defaultdict(int)
    chat_stats = stats.get(chat_id, {})
    for date_str, users in chat_stats.items():
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
        if date >= week_ago.date():
            for uid, data in users.items():
                week_users[uid] += data["count"]

    sorted_users = sorted(week_users.items(), key=lambda x: x[1], reverse=True)[:10]
    lines = ["🏆 *Топ 10 самых активных за неделю:*"]
    for i, (uid, count) in enumerate(sorted_users, 1):
        username = None
        for day in chat_stats.values():
            if uid in day:
                username = day[uid]["username"]
                break
        user_tag = f"@{username}" if username else f"ID:{uid}"
        lines.append(f"{i}. {user_tag} — {count} сообщений")

    await update.message.reply_text("
".join(lines), parse_mode="Markdown")

async def graph_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    now = datetime.now(pytz.timezone("Europe/Moscow"))
    week_ago = now - timedelta(days=6)
    user_daily = defaultdict(lambda: [0]*7)
    chat_stats = stats.get(chat_id, {})

    for i in range(7):
        day = (week_ago + timedelta(days=i)).date().isoformat()
        if day in chat_stats:
            for uid, data in chat_stats[day].items():
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

async def motohelp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📋 *Список доступных команд:*
"
        "/stat — Общая статистика сообщений
"
        "/top — Топ 10 активных участников за неделю
"
        "/graph — График активности за неделю
"
        "/motohelp — Список доступных команд"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def send_weekly_report(application):
    for chat_id in stats.keys():
        dummy_update = Update(update_id=0, message=None)
        dummy_context = ContextTypes.DEFAULT_TYPE()
        dummy_context.bot = application.bot
        dummy_update.effective_chat = type("Chat", (object,), {"id": int(chat_id)})
        await top_command(dummy_update, dummy_context)
        await graph_command(dummy_update, dummy_context)

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

if __name__ == '__main__':
    asyncio.run(main())
