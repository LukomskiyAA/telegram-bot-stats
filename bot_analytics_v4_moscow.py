
import json
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
from bot_utils import get_top_users, escape_markdown

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "YOUR_BOT_TOKEN"

def save_chat_id(chat_id):
    with open("chat_id.txt", "w") as f:
        f.write(str(chat_id))

def load_chat_id():
    try:
        with open("chat_id.txt", "r") as f:
            return int(f.read().strip())
    except FileNotFoundError:
        logger.warning("chat_id.txt not found.")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat_id(update.effective_chat.id)
    await update.message.reply_text("Привет! Я бот статистики.")

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat_id(update.effective_chat.id)
    try:
        top_users = get_top_users()
        message = "*Топ пользователей по сообщениям:*
"
        for i, user_data in enumerate(top_users, start=1):
            username = escape_markdown(user_data.get("username", "Без ника"))
            message += f"{i}. [{username}](tg://user?id={user_data['user_id']}) — `{user_data['message_count']}` сообщений\n"
        await update.message.reply_text(message, parse_mode="MarkdownV2")
    except Exception as e:
        logger.exception("Ошибка в /top")
        await update.message.reply_text("Не удалось получить статистику.")

async def graph_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat_id(update.effective_chat.id)
    try:
        with open("activity_chart.png", "rb") as f:
            await update.message.reply_photo(photo=f)
    except FileNotFoundError:
        await update.message.reply_text("График ещё не создан.")

async def stat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat_id(update.effective_chat.id)
    await update.message.reply_text("📊 Статистика доступна через команды /top и /graph.")

async def motohelp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_chat_id(update.effective_chat.id)
    await update.message.reply_text("🛵 Справка по использованию:
/start — запуск
/top — топ пользователей
/graph — график
/stat — сводка
/motohelp — помощь")

async def weekly_summary():
    chat_id = load_chat_id()
    if not chat_id:
        return

    try:
        top_users = get_top_users()
        message = "*Топ пользователей по сообщениям за неделю:*
"
        for i, user_data in enumerate(top_users, start=1):
            username = escape_markdown(user_data.get("username", "Без ника"))
            message += f"{i}. [{username}](tg://user?id={user_data['user_id']}) — `{user_data['message_count']}` сообщений\n"

        await application.bot.send_message(chat_id=chat_id, text=message, parse_mode="MarkdownV2")

        with open("activity_chart.png", "rb") as f:
            await application.bot.send_photo(chat_id=chat_id, photo=f)
    except Exception as e:
        logger.exception("Ошибка при рассылке отчёта")

async def main():
    global application
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("top", top_command))
    application.add_handler(CommandHandler("graph", graph_command))
    application.add_handler(CommandHandler("stat", stat_command))
    application.add_handler(CommandHandler("motohelp", motohelp_command))

    scheduler = AsyncIOScheduler(timezone=timezone("Europe/Moscow"))
    scheduler.add_job(weekly_summary, trigger="cron", day_of_week="sun", hour=23, minute=59)
    scheduler.start()

    logger.info("Бот запущен...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
