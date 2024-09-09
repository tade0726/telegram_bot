from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from telegram_bot_tts.db.db_manager import DBManager


# commands
async def start(
    update: Update, context: ContextTypes.DEFAULT_TYPE, db_manager: DBManager
):

    # add a welcome message
    await update.message.reply_text(
        "Welcome to the Telegram Bot TTS! I have two simple features: Text to Speech and Speech to Text. \n\n"
        "You will automatically get 10,000 characters for tts and 60 minutes for stt in a 7-days trial. "
        "After that, you will need to buy a plan to continue using the bot. "
    )

    # check if the user is already registered
    if not db_manager.is_user_registered(update.message.from_user.id):

        # register the user
        if db_manager.register_user(
            update.message.from_user.id,
            username=update.message.from_user.username,
            first_name=update.message.from_user.first_name,
            last_name=update.message.from_user.last_name,
        ):

            # notify the user that the subscription is added
            await update.message.reply_text(
                "You have been registered successfully. You have a free subscription to use the bot."
            )

        else:
            await update.message.reply_text(
                "Error registering user. Please try again later."
            )
    else:
        await update.message.reply_text(
            "You are already registered. You can use the bot now."
        )


async def subscribe(
    update: Update, context: ContextTypes.DEFAULT_TYPE, db_manager: DBManager
):
    pass


async def balance(
    update: Update, context: ContextTypes.DEFAULT_TYPE, db_manager: DBManager
):
    pass


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # add a help message
    # list out all the commands and their usage

    await update.message.reply_text(
        "Here are the commands you can use: \n\n"
        "/start - Start the bot and get a welcome message\n"
        "/subscribe - Subscribe to the bot to get unlimited access\n"
        "/unsubscribe - Unsubscribe from the bot\n"
        "/balance - Check your balance\n"
        "/help - Get help with the bot\n\n"
    )
