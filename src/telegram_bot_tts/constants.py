from os import environ
from typing import Final
from openai import AsyncOpenAI


TOKEN: Final = environ.get("TELEGRAM_BOT_TOKEN")
BOT_USERNAME: Final = "@openaitts_bot"
ENV: Final = environ.get("ENV", "dev")
OPENAI_CLIENT: AsyncOpenAI = AsyncOpenAI()
AUDIO_FOLDER: Final = "/tts_bot_audio" if ENV == "prod" else "/tmp/tts_bot_audio"

user_id_list = environ.get("VIP_USER_ID_LIST")
user_id_list = user_id_list.split(",") if user_id_list else []
VIP_USER_ID_LIST: Final = [
    int(user_id) if user_id.isdigit() else None for user_id in user_id_list
]
