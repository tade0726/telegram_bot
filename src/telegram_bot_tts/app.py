from typing import Final
from telegram import Update
from telegram.ext import (
    MessageHandler,
    filters,
    ContextTypes,
    Application,
    CommandHandler,
)


from telegram_bot_tts.logger import setup_logger
from telegram_bot_tts.constants import TOKEN, ENV
from telegram_bot_tts.components.ults import create_audio_folder
from telegram_bot_tts.components.commands import start_command
from telegram_bot_tts.components.handlers import handle_message, error


logger = setup_logger("telegram_bot_tts", ENV)


if __name__ == "__main__":
    # create the audio folder
    create_audio_folder()

    logger.info("starting bot...")
    app = Application.builder().token(TOKEN).read_timeout(30).write_timeout(45).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", start_command))

    # Messages
    app.add_handler(
        MessageHandler(
            filters.TEXT,
            lambda update, context: handle_message(update, context, logger),
        )
    )

    # Error
    app.add_error_handler(lambda update, context: error(update, context, logger))

    # polls the bot
    logger.info("Polling...")

    app.run_polling(poll_interval=3)
