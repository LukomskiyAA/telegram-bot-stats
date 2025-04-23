import logging
import re
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bot_utils import get_top_users  # Предполагается, что у тебя есть этот модуль

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def escape_md(text: str) -> str:
    return re.sub(r'(?<!@)([_*\[\]()~`>#+\-=|{}.!])', r'\\\1', text)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот запущен и работает!")

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    top_users = get_top_users(chat_id)

    if not top_users:
        await update.message.reply_text("Нет данных для отображения.")
        return

    lines = ["🏆 *Топ 10 самых активных за неделю:*"]
    for i, (username, count) in enumerate(top_users, start=1):
        name = f"@{username}" if username else "Без ника"
        lines.append(f"{i}. {escape_md(name)} — {count} сообщений")

    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")

async def main():
    application = ApplicationBuilder().token("YOUR_BOT_TOKEN").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("top", top_command))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: print("Планировщик активен"), "interval", minutes=10)
    scheduler.start()

    logger.info("Бот запущен...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
