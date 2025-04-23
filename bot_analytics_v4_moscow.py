import os
import json
import asyncio
import pytz
import logging
import datetime
import matplotlib.pyplot as plt

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from collections import defaultdict

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# Загружаем токен из переменной окружения
TOKEN = os.getenv("BOT_TOKEN")

# Путь к файлу с статистикой
STATS_FILE = "stats.json"

# Чат ID для авторассылки
CHAT_ID = -1002585901809

# Загрузка статистики
def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"total": defaultdict(int), "weekly": defaultdict(int)}

# Сохранение статистики
def save_stats(data):
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Обработка входящих сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user or not update.message:
        return
    name = user.username or f"{user.first_name} {user.last_name or ''}".strip()
    stats = context.bot_data["stats"]
    stats["total"][name] = stats["total"].get(name, 0) + 1
    stats["weekly"][name] = stats["weekly"].get(name, 0) + 1
    save_stats(stats)

# Команда /stat
async def stat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = context.bot_data["stats"]["total"]
    result = "*📊 Общая статистика сообщений:*\n\n"
    for name, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        result += f"▪️ {name} — {count} сообщений\n"
    await update.message.reply_text(result, parse_mode="Markdown")

# Команда /top
async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = context.bot_data["stats"]["weekly"]
    top_users = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]
    result = "*🏆 Топ 10 самых активных за неделю:*\n"
    for i, (name, count) in enumerate(top_users, 1):
        result += f"{i}. {name} — {count} сообщений\n"
    await update.message.reply_text(result, parse_mode="Markdown")

# Команда /graph
async def graph_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = context.bot_data["stats"]["weekly"]
    names, counts = zip(*sorted(stats.items(), key=lambda x: x[1], reverse=True))
    plt.figure(figsize=(10, 6))
    plt.barh(names[::-1], counts[::-1])
    plt.xlabel("Сообщений")
    plt.title("Топ активных за неделю")
    plt.tight_layout()
    plt.savefig("weekly_graph.png")
    plt.close()
    await update.message.reply_photo(photo=open("weekly_graph.png", "rb"))

# Команда /getid
async def getid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"🆔 Chat ID: `{chat_id}`", parse_mode="Markdown")

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "*Список доступных команд:*\n"
        "/stat — Общая статистика сообщений\n"
        "/top — Топ 10 активных за неделю\n"
        "/graph — График активности за неделю\n"
        "/getid — Получить ID текущего чата\n"
        "/help — Список всех команд"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# Автоматическая еженедельная рассылка /top и /graph
async def weekly_report(context: ContextTypes.DEFAULT_TYPE):
    chat_id = CHAT_ID
    stats = context.bot_data["stats"]["weekly"]

    if stats:
        top_users = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]
        result = "*🏆 Топ 10 самых активных за неделю:*\n"
        for i, (name, count) in enumerate(top_users, 1):
            result += f"{i}. {name} — {count} сообщений\n"
        await context.bot.send_message(chat_id=chat_id, text=result, parse_mode="Markdown")

        names, counts = zip(*sorted(stats.items(), key=lambda x: x[1], reverse=True))
        plt.figure(figsize=(10, 6))
        plt.barh(names[::-1], counts[::-1])
        plt.xlabel("Сообщений")
        plt.title("Топ активных за неделю")
        plt.tight_layout()
        plt.savefig("weekly_graph.png")
        plt.close()

        await context.bot.send_photo(chat_id=chat_id, photo=open("weekly_graph.png", "rb"))

    context.bot_data["stats"]["weekly"] = {}
    save_stats(context.bot_data["stats"])

# Главная функция
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.bot_data["stats"] = load_stats()

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CommandHandler("stat", stat_command))
    app.add_handler(CommandHandler("top", top_command))
    app.add_handler(CommandHandler("graph", graph_command))
    app.add_handler(CommandHandler("getid", getid_command))
    app.add_handler(CommandHandler("help", help_command))

    scheduler = AsyncIOScheduler(timezone=pytz.timezone("Europe/Moscow"))
    scheduler.add_job(weekly_report, "cron", day_of_week="sun", hour=23, minute=59, args=[app.bot])
    scheduler.start()

    print("✅ Бот запущен...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
