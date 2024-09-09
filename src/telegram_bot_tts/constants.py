from os import environ
from typing import Final
from openai import AsyncOpenAI


TOKEN: Final = environ.get("TELEGRAM_BOT_TOKEN")
BOT_USERNAME: Final = "@openaitts_bot"
ENV: Final = environ.get("ENV", "dev")
OPENAI_CLIENT: AsyncOpenAI = AsyncOpenAI()
AUDIO_FOLDER: Final = "/tts_bot_audio" if ENV == "prod" else "/tmp/tts_bot_audio"
