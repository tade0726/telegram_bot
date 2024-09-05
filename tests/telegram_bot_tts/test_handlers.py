# test stt_response
from openai import AsyncOpenAI
import os
import pytest

from telegram_bot_tts.components.handlers import stt_response, tts_response


pytest_plugins = ("pytest_asyncio",)


audio_path = "tests/src/telegram_bot_tts/test_audio.wav"


@pytest.mark.asyncio
async def test_tts_response():

    text = "Hello, how are you?"

    current_dir = os.path.dirname(os.path.abspath(__file__))
    audio_path = os.path.join(current_dir, "audio", "tts_test_audio.wav")

    client = AsyncOpenAI()

    response = await tts_response(text, client, audio_path)

    assert os.path.exists(response)
    assert os.path.samefile(response, audio_path)


@pytest.mark.asyncio
async def test_stt_response():

    current_dir = os.path.dirname(os.path.abspath(__file__))
    audio_path = os.path.join(current_dir, "audio", "test_audio.wav")

    client = AsyncOpenAI()

    response = await stt_response(audio_path, client)
    assert response == "Hello, how are you?"
