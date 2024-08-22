format:
	black src/

build:
	docker-compose up -d --build


local_run:
	uv run src/telegram_bot_tts/app.py