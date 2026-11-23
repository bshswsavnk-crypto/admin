import os
import html
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Read secrets from environment variables (set these in Railway)
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    # Greet the user
    await update.message.reply_text(f"Hi {user.first_name}! Welcome 👋")

    # Notify the admin
    username = f"@{user.username}" if user.username else "no username"
    text = (
        "🔔 <b>New user started the bot</b>\n\n"
        f"Name: {html.escape(user.full_name)}\n"
        f"Username: {html.escape(username)}\n"
        f"ID: <code>{user.id}</code>"
    )
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="HTML")
    except Exception as e:
        logger.error("Could not notify admin: %s", e)


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    logger.info("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
