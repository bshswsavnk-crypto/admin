import os
import html
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Read secrets from environment variables (set these in Railway)
BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ["ADMIN_ID"])

# ---- Customer-facing messages (edit the wording here) ----
WELCOME_MESSAGE = (
    "Hi {name}! 👋 Welcome to Bum Heads Spoon Collection.\n\n"
    "Thank you for your interest. Our team will write to you shortly."
)
CONTACTED_MESSAGE = (
    "✅ Our sales person has written to you.\n\n"
    "Please check your Telegram messages."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    # Tracking source, e.g. https://t.me/YOUR_BOT?start=ad1
    source = context.args[0] if context.args else "organic"

    # 1. Tell the customer the team will write shortly
    await update.message.reply_text(
        WELCOME_MESSAGE.format(name=user.first_name)
    )

    # 2. Notify the admin
    username = f"@{user.username}" if user.username else "no username"
    text = (
        "🔔 <b>New customer started the bot</b>\n\n"
        f"Name: {html.escape(user.full_name)}\n"
        f"Username: {html.escape(username)}\n"
        f"ID: <code>{user.id}</code>\n"
        f"Source: {html.escape(source)}"
    )

    # Link that opens the customer's chat (works even without a username)
    chat_link = (
        f"https://t.me/{user.username}" if user.username else f"tg://user?id={user.id}"
    )
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("💬 Open chat", url=chat_link)],
            [
                InlineKeyboardButton(
                    "✅ I've messaged them", callback_data=f"contacted:{user.id}"
                )
            ],
        ]
    )

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID, text=text, parse_mode="HTML", reply_markup=keyboard
        )
    except Exception as e:
        logger.error("Could not notify admin: %s", e)


async def contacted(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin pressed 'I've messaged them' -> notify the customer."""
    query = update.callback_query

    # Only the admin may use this button
    if query.from_user.id != ADMIN_ID:
        await query.answer("Not allowed.", show_alert=True)
        return

    customer_id = int(query.data.split(":")[1])

    try:
        await context.bot.send_message(chat_id=customer_id, text=CONTACTED_MESSAGE)
    except Exception as e:
        logger.error("Could not notify customer %s: %s", customer_id, e)
        await query.answer(
            "Could not notify the customer (they may have blocked the bot).",
            show_alert=True,
        )
        return

    await query.answer("Customer notified ✅")
    await query.edit_message_text(
        query.message.text_html + "\n\n✅ <b>Customer notified</b>",
        parse_mode="HTML",
    )


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(contacted, pattern=r"^contacted:\d+$"))
    logger.info("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
