import logging
from pathlib import Path
from typing import Union
import io

from telegram import Update
from telegram.ext import ContextTypes
from openai import AsyncOpenAI

from telegram_bot_tts.constants import (
    USERS_ALLOWED,
    BOT_USERNAME,
    AUDIO_FOLDER,
)

from telegram_bot_tts.db.db_manager import DBManager

# Responses


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


async def stt_response(audio: Union[bytes, str], client: AsyncOpenAI) -> str:

    if isinstance(audio, str):
        audio_file = open(audio, "rb")
    elif isinstance(audio, Union[bytes, io.BytesIO]):
        audio_file = audio
    else:
        raise ValueError("Invalid audio type")

    transcript = await client.audio.transcriptions.create(
        model="whisper-1", file=audio_file
    )
    return transcript.text


async def handle_text_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    logger: logging.Logger,
    client: AsyncOpenAI,
    db_manager: DBManager,
):

    user_id: int = update.message.from_user.id
    massage_type: str = update.message.chat.type
    user_id: int = update.message.from_user.id
    text: str = update.message.text

    logger.debug(f'User ({user_id}) in {massage_type}: "{text}"')

    # checking if the user have registered
    if not db_manager.is_user_registered(user_id):
        await update.message.reply_text("Please use /start cmd to register first.")
        return

    if massage_type in ("group", "supergroup"):
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, "")
            response: str = text_response(new_text)
            text = new_text
        else:
            return
    else:
        response: str = text_response(text)

    logger.debug(f"Bot reply: {response}")

    # return the audio file
    audio_path = await tts_response(response, client)

    await update.message.reply_voice(voice=audio_path, quote=True)


async def handle_voice_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    logger: logging.Logger,
    client: AsyncOpenAI,
    db_manager: DBManager,
):

    user_id: int = update.message.from_user.id
    massage_type: str = update.message.chat.type
    voice_file_id: str = update.message.voice.file_id
    voice_file = await context.bot.get_file(voice_file_id)

    logger.debug(f'User ({user_id}) in {massage_type}: "{voice_file_id}"')

    # checking if the user have registered
    if not db_manager.is_user_registered(user_id):
        await update.message.reply_text("Please use /start cmd to register first.")
        return

    # store file in memory, not on disk
    buf = io.BytesIO()
    await voice_file.download_to_memory(buf)
    buf.name = "voice.oga"  # file extension is required
    buf.seek(0)  # move cursor to the beginning of the buffer

    # pass the audio to the stt model
    text = await stt_response(buf, client)

    # checking if the text is too long
    if len(text) > 4096:
        # break into chunks of 4096 characters, ensuring breaks at word boundaries
        chunks = []
        for i in range(0, len(text), 4096):
            end = i + 4096
            if end < len(text):
                # Find the last space within the 4096 character limit
                end = text.rfind(" ", i, end)
                if end == -1:  # If no space found, force break at 4096
                    end = i + 4096
            chunks.append(text[i:end].strip())
        for chunk in chunks:
            await update.message.reply_text(chunk, quote=True)
    else:
        await update.message.reply_text(text, quote=True)


async def error(
    update: Update, context: ContextTypes.DEFAULT_TYPE, logger: logging.Logger
):
    try:
        raise context.error
    except Exception as e:
        logger.error(f"Update ({update}) caused error: {str(e)}")

        tb = e.__traceback__
        while tb.tb_next:
            tb = tb.tb_next

        filename = tb.tb_frame.f_code.co_filename
        line_number = tb.tb_lineno

        logger.error(
            f"Error occurred on line {line_number} of {filename}, error: {context.error}"
        )

        # You might want to notify the user about the error
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "An error occurred while processing your request. Please try again later."
            )
