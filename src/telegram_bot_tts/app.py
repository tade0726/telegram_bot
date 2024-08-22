from typing import Final
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackContext,
)

from pathlib import Path
from openai import OpenAI, AsyncOpenAI

from os import environ

from telegram_bot_tts.logger import setup_logger


TOKEN: Final = environ.get("TELEGRAM_BOT_TOKEN")
BOT_USERNAME: Final = "@openaitts_bot"
USERS_ALLOWED: Final = (626730440, 859920241)
ENV: Final = environ.get("ENV", "dev")
OPENAI_CLIENT: AsyncOpenAI = AsyncOpenAI()

AUDIO_FOLDER = "/tts_bot_audio" if ENV == "prod" else "/tmp/tts_bot_audio"


# logging
logger = setup_logger("telegram_bot_tts", ENV)


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


async def tts_response(text: str, client: AsyncOpenAI) -> object:
    # I want to save the audio file in a temporary directory with a unique name, such as a msg id
    audio_file_name = str(text[:10].replace(" ", "_"))
    speech_file_path = Path(AUDIO_FOLDER) / f"{audio_file_name}.mp3"

    response = await client.audio.speech.create(model="tts-1", voice="nova", input=text)

    # Write the response content to a file
    with open(speech_file_path, "wb") as file:
        for chunk in response.iter_bytes():
            file.write(chunk)

    return speech_file_path


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global USERS_ALLOWED

    massage_type: str = update.message.chat.type
    user_id: int = update.message.from_user.id
    text: str = update.message.text

    logger.debug(f'User ({update.message.chat.id}) in {massage_type}: "{text}"')

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

    logger.debug(f"Bot reply: {response}")

    # return the audio file
    audio_path = await tts_response(response, client=OPENAI_CLIENT)

    await update.message.reply_voice(voice=audio_path)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")


if __name__ == "__main__":
    create_audio_folder()

    logger.info("starting bot...")
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", start_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Error
    app.add_error_handler(error)

    # polls the bot
    logger.info("Polling...")

    app.run_polling(poll_interval=3)
