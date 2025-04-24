
import json
import logging
import asyncio
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot_utils import get_top_users, escape_markdown

logging.basicConfig(level=logging.INFO, filename="bot.log", filemode="a",
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

TOKEN = "YOUR_BOT_TOKEN"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот статистики. Используй /top или /graph.")

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        top_users = get_top_users()
        message = "*Топ пользователей по сообщениям:*
\#️⃣\#️⃣\#️⃣\#️⃣\#️⃣\#️⃣\#️⃣\#️⃣\#️⃣\#️⃣\n"
        for i, user_data in enumerate(top_users, start=1):
            username = escape_markdown(user_data.get("username", "Без ника"))
            message += f"{i}. [{username}](tg://user?id={user_data['user_id']}) — `{user_data['message_count']}` сообщений\n"
        await update.message.reply_text(message, parse_mode="MarkdownV2")
    except Exception as e:
        logger.exception("Ошибка при обработке команды /top")
        await update.message.reply_text("Произошла ошибка при получении статистики.")

async def graph_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open("activity_chart.png", "rb") as chart:
            await update.message.reply_photo(photo=InputFile(chart), caption="📊 График активности")
    except Exception as e:
        logger.exception("Ошибка при отправке графика")
        await update.message.reply_text("Не удалось загрузить график активности.")

async def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("top", top_command))
    application.add_handler(CommandHandler("graph", graph_command))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: logger.info("🕒 Планировщик активен"), 'interval', minutes=1)
    scheduler.start()

    logger.info("Бот запущен...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
