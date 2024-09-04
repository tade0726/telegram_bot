format:
	black src/

build:
	docker-compose up -d --build

teardown:
	docker-compose down -v

local_run:
	uv run src/telegram_bot_tts/app.py

test:
	PYTHONPATH=. pytest tests