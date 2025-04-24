import json
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot_utils import get_top_users, escape_markdown

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "YOUR_BOT_TOKEN"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот статистики.")

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        top_users = get_top_users()
        message = "*Топ пользователей по сообщениям:*
"
        for i, user_data in enumerate(top_users, start=1):
            username = escape_markdown(user_data.get("username", "Без ника"))
            message += f"{i}. [{username}](tg://user?id={user_data['user_id']}) — `{user_data['message_count']}` сообщений\n"
        await update.message.reply_text(message, parse_mode="MarkdownV2")
    except Exception as e:
        logger.exception("Ошибка при обработке команды /top")
        await update.message.reply_text("Произошла ошибка при получении статистики.")

async def graph_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("GRAPH команда работает!")

async def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("top", top_command))
    application.add_handler(CommandHandler("graph", graph_command))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: logger.info("Scheduled job running"), 'interval', minutes=1)
    scheduler.start()

    logger.info("Бот запущен...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
