from typing import Final
from telegram import Update
from telegram.ext import (
    MessageHandler,
    filters,
    Application,
    CommandHandler,
)
from openai import AsyncOpenAI

from telegram_bot_tts.logger import setup_logger
from telegram_bot_tts.constants import TOKEN, ENV
from telegram_bot_tts.components.ults import create_audio_folder
from telegram_bot_tts.components.commands import start, help
from telegram_bot_tts.components.handlers import (
    handle_text_message,
    handle_voice_message,
    error,
)
from telegram_bot_tts.db.db_manager import DBManager


logger = setup_logger("telegram_bot_tts", ENV)


if __name__ == "__main__":

    # the timeout varibles will be set here
    READ_TIMEOUT = 180
    WRITE_TIMEOUT = 180

    # create the audio folder
    create_audio_folder()

    # create the openai client
    client = AsyncOpenAI()

    # create the db manager
    db_manager = DBManager()

    logger.info("starting bot...")
    app = (
        Application.builder()
        .token(TOKEN)
        .read_timeout(READ_TIMEOUT)
        .write_timeout(WRITE_TIMEOUT)
        .build()
    )

    # Commands

    app.add_handler(
        CommandHandler(
            "start", lambda update, context: start(update, context, db_manager)
        )
    )

    app.add_handler(
        CommandHandler("help", lambda update, context: help(update, context))
    )

    # text Messages
    app.add_handler(
        MessageHandler(
            filters.TEXT,
            lambda update, context: handle_text_message(
                update, context, logger, client, db_manager
            ),
        )
    )

    # add voice message handler
    app.add_handler(
        MessageHandler(
            filters.VOICE,
            lambda update, context: handle_voice_message(
                update, context, logger, client, db_manager
            ),
        )
    )

    # Error
    app.add_error_handler(lambda update, context: error(update, context, logger))

    # polls the bot
    logger.info("Polling...")

    app.run_polling(poll_interval=3)
