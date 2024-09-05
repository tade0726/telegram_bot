import logging
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes
from openai import AsyncOpenAI

from telegram_bot_tts.constants import (
    USERS_ALLOWED,
    BOT_USERNAME,
    OPENAI_CLIENT,
    AUDIO_FOLDER,
)


# Responses
def handle_respone(text: str) -> str:
    # todo
    return text_response(text)


def text_response(text: str) -> str:
    return text


async def tts_response(text: str, client: AsyncOpenAI, audio_path: str = None) -> str:
    # I want to save the audio file in a temporary directory with a unique name, such as a msg id
    audio_file_name = str(text[:10].replace(" ", "_"))

    speech_file_path = (
        Path(AUDIO_FOLDER) / f"{audio_file_name}.mp3"
        if audio_path is None
        else audio_path
    )

    response = await client.audio.speech.create(model="tts-1", voice="nova", input=text)

    # Write the response content to a file
    with open(speech_file_path, "wb") as file:
        for chunk in response.iter_bytes():
            file.write(chunk)

    return speech_file_path


async def stt_response(audio_path: str, client: AsyncOpenAI) -> str:
    audio_file = open(audio_path, "rb")
    transcript = await client.audio.transcriptions.create(
        model="whisper-1", file=audio_file
    )
    return transcript.text


async def handle_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE, logger: logging.Logger
):
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

    if massage_type in ("group", "supergroup"):
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


async def error(
    update: Update, context: ContextTypes.DEFAULT_TYPE, logger: logging.Logger
):
    logger.error(f"Update {update} caused error: {context.error}")
