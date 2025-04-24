import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from bot_utils import get_top_users

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "TELEGRAM_BOT_TOKEN"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот-аналитик. Используй /top, чтобы увидеть статистику.")

def escape_markdown(text: str) -> str:
    escape_chars = r"*_[]()~`>#+-=|{}.!"
    return "".join(f"\{char}" if char in escape_chars else char for char in text)

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = get_top_users()
    lines = ["🏆 *Топ пользователей по активности:*"]
    for i, (user, count) in enumerate(top_users, start=1):
        username = escape_markdown(user.replace('.', '\.').replace('_', '\_'))
        lines.append(f"{i}) @{username} — {count}")
    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")

async def main():
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("top", top_command))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: print("⏰ Scheduler task executed."), 'interval', minutes=10)
    scheduler.start()

    logger.info("Бот запущен...")
    await application.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
async def graph_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("GRAPH команда работает!")
