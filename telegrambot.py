import logging
# from time import sleep
from login import check_and_book_slot, get_confirmed_bookings
from utils import TELEGRAM_TOKEN, get_now_with_offset
from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)


if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)
logger = logging.getLogger(__name__)

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    # reply_markup=ForceReply(selective=True)
    reply_keyboard = [["Book", "Check"]]
    greetings = rf"Hi {user.mention_html()}! Please select book or check"
    await update.message.reply_html(greetings,
                                    reply_markup=ReplyKeyboardMarkup(reply_keyboard,
                                                                     one_time_keyboard=True,
                                                                     input_field_placeholder="Book or Check?"),
                                    )


async def help_command(update: Update,
                       context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Help!")


async def run_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    # await update.message.reply_text(update.message.text)
    in_msg = update.message.text.lower()
    offset = get_now_with_offset()
    if in_msg == "book":
        reply = f"Sure Sir/Ma'am, right away. {in_msg}ing now..Please come back again at {offset} to check"
        await update.message.reply_text(reply)
        try:
            result = check_and_book_slot()
        except Exception as e:
            result = e
        await update.message.reply_text(result)
    elif in_msg == "check":
        try:
            check_list = get_confirmed_bookings()
            if check_list:
                await update.message.reply_text("Confirmed booking are as follows")
                for booking in check_list:
                    await update.message.reply_text(booking)
            else:
                await update.message.reply_text("No confirmed booking found")
        except Exception as e:
            result = e
            await update.message.reply_text(result)
    else:
        result = f"{update.message.text}ing function is not implemented yet."
        await update.message.reply_text(result)


def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                                           run_task))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
