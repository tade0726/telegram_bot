from typing import Final
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from pathlib import Path
from openai import OpenAI

from os import environ

import logging

# logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


TOKEN: Final = environ.get("TELEGRAM_BOT_TOKEN")
BOT_USERNAME: Final = "@openaitts_bot"
USERS_ALLOWED: Final = (626730440, 859920241)

CLIENT = OpenAI()


AUDIO_FOLDER = "/tts_bot_audio"


# helper

def create_audio_folder():
    audio_folder = Path(AUDIO_FOLDER)
    audio_folder.mkdir(exist_ok=True, parents=True)
    return audio_folder


# commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "You can input any text and I will return its audio file."
    )

# Responses
def handle_respone(text: str) -> str:
    # todo
    return text_response(text)


def text_response(text: str) -> str:
    return text


def tts_response(text: str) -> object:

    global CLIENT
    # I want to save the audio file in a temporary directory with a unique name, such as a msg id
    audio_file_name = str(text[:10].replace(" ", "_"))
    speech_file_path = Path(AUDIO_FOLDER) / f"{audio_file_name}.mp3"

    response = CLIENT.audio.speech.create(model="tts-1", voice="nova", input=text)

    # Write the response content to a file
    with open(speech_file_path, "wb") as file:
        for chunk in response.iter_bytes():
            file.write(chunk)

    return speech_file_path


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global USERS_ALLOWED

    massage_type: str = update.message.chat.type
    user_id: int = update.message.chat.id
    text: str = update.message.text

    logging.debug(f'User ({update.message.chat.id}) in {massage_type}: "{text}"')

    if user_id not in USERS_ALLOWED:
        await update.message.reply_text(
            "You are not allowed to use this bot. Contact the author for more information."
        )
        return

    if massage_type == "group":
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, "")
            response: str = handle_respone(new_text)
            text = new_text
        else:
            return
    else:
        response: str = handle_respone(text)

    logging.debug("Bot:", response)

    # return the audio file
    audio_path = tts_response(response)

    await update.message.reply_voice(voice=audio_path)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Update {update} caused error {context.error}")


if __name__ == "__main__":

    create_audio_folder()

    logging.info("starting bot...")
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", start_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Error
    app.add_error_handler(error)

    # polls the bot
    logging.info("Polling...")
    app.run_polling(poll_interval=3)
