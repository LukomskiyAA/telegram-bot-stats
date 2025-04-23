import json
import os
import datetime
import logging
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
import matplotlib.pyplot as plt

TOKEN = "8164071818:AAFCBZTKBXcCbxLdmN1uyjRT26X_w4abjVY"
CHAT_FILE = "chat.json"

def load_chat_id():
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("chat_id")
    return None

def save_chat_id(chat_id):
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump({"chat_id": chat_id}, f)

AUTO_POST_CHAT_ID = load_chat_id()
STATS_FILE = "stats.json"

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"meta": {"last_weekly_reset": datetime.date.today().isoformat()}}

def save_stats(stats):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Сохраняем chat_id при первом сообщении
    global AUTO_POST_CHAT_ID
    if AUTO_POST_CHAT_ID is None:
        AUTO_POST_CHAT_ID = update.effective_chat.id
        save_chat_id(AUTO_POST_CHAT_ID)
        logging.info(f"🔧 Новый чат сохранён: {AUTO_POST_CHAT_ID}")
    if not update.message or not update.message.text:
        return
    user = update.message.from_user
    user_id = str(user.id)
    username = user.username or user.full_name or "Без_имени"
    stats = context.bot_data.get("stats", {})
    user_stats = stats.get(user_id, {"username": username, "messages": 0, "weekly_messages": 0})
    user_stats["username"] = username
    user_stats["messages"] += 1
    user_stats["weekly_messages"] += 1
    stats[user_id] = user_stats
    context.bot_data["stats"] = stats
    save_stats(stats)
    logging.info(f"Сообщение от {username} ({user_id}) в чате {update.effective_chat.id}")

async def stat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = context.bot_data.get("stats", {})
    lines = ["📊 Общая статистика сообщений:\n"]
    for uid, data in stats.items():
        if uid == "meta":
            continue
        username = f"@{data['username']}" if data.get("username") else f"ID:{uid}"
        lines.append(f"{username}: {data['messages']} сообщений")
    await update.message.reply_text("\n".join(lines))

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE, force_chat_id=None, force_thread_id=None):
    stats = context.bot_data.get("stats", {})
    top = sorted(
        [(uid, d) for uid, d in stats.items() if uid != "meta"],
        key=lambda x: x[1].get("weekly_messages", 0),
        reverse=True
    )[:10]
    if not top:
        text = "Пока нет статистики за неделю."
    else:
        lines = ["🏆 Топ 10 активных за неделю:\n"]
        for i, (uid, data) in enumerate(top, 1):
            username = f"@{data['username']}" if data.get("username") else f"ID:{uid}"
            count = data.get("weekly_messages", 0)
            lines.append(f"{i}. {username}: {count} сообщений")
        text = "\n".join(lines)
    if force_chat_id:
        await context.bot.send_message(chat_id=force_chat_id, text=text, message_thread_id=force_thread_id)
    elif update:
        await update.message.reply_text(text)

async def graph_command(update: Update, context: ContextTypes.DEFAULT_TYPE, force_chat_id=None, force_thread_id=None):
    stats = context.bot_data.get("stats", {})
    users = []
    counts = []
    for uid, data in stats.items():
        if uid == "meta":
            continue
        users.append(data['username'])
        counts.append(data['weekly_messages'])
    if not users:
        if update:
            await update.message.reply_text("Нет данных для построения графика.")
        return
    plt.figure(figsize=(10, 5))
    plt.bar(users, counts)
    plt.xlabel("Пользователи")
    plt.ylabel("Сообщений за неделю")
    plt.title("📊 Активность пользователей за неделю")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig("activity_chart.png")
    plt.close()
    with open("activity_chart.png", "rb") as f:
        if force_chat_id:
            await context.bot.send_photo(chat_id=force_chat_id, photo=f, caption="📈 Активность за неделю", message_thread_id=force_thread_id)
        elif update:
            await update.message.reply_photo(photo=f, caption="📈 Активность за неделю")

async def getid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    thread_id = update.message.message_thread_id
    await update.message.reply_text(
        f"🆔 Chat ID: `{chat_id}`\n🧵 Thread ID: `{thread_id}`",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🧾 Доступные команды:\n"
        "/stat — Общая статистика\n"
        "/top — Топ 10 активных за неделю\n"
        "/graph — График активности\n"
        "/getid — Показать Chat ID и Thread ID\n"
        "/help — Список команд"
    )
    await update.message.reply_text(text)

async def weekly_task(context: ContextTypes.DEFAULT_TYPE):
    stats = context.bot_data.get("stats", {})
    await top_command(None, context, force_chat_id=AUTO_POST_CHAT_ID)
    await graph_command(None, context, force_chat_id=AUTO_POST_CHAT_ID)
    for uid in stats:
        if uid != "meta":
            stats[uid]["weekly_messages"] = 0
    stats["meta"]["last_weekly_reset"] = datetime.date.today().isoformat()
    save_stats(stats)

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.bot_data["stats"] = load_stats()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CommandHandler("stat", stat_command))
    app.add_handler(CommandHandler("top", lambda u, c: top_command(u, c)))
    app.add_handler(CommandHandler("graph", lambda u, c: graph_command(u, c)))
    app.add_handler(CommandHandler("getid", getid_command))
    app.add_handler(CommandHandler("help", help_command))
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        lambda: weekly_task(app.bot_data["application"].context),
        trigger='cron',
        day_of_week='sun', hour=23, minute=59,
        timezone=pytz.timezone('Europe/Moscow')
    )
    scheduler.start()
    logging.info("✅ Бот запущен!")
    await app.run_polling()

nest_asyncio.apply()
asyncio.run(main())
