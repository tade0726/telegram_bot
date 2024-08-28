from pathlib import Path

from telegram_bot_tts.constants import AUDIO_FOLDER


def create_audio_folder():
    audio_folder = Path(AUDIO_FOLDER)
    audio_folder.mkdir(exist_ok=True, parents=True)
    return audio_folder
