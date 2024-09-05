format:
	black src/ tests/

build:
	docker-compose up -d --build

teardown:
	docker-compose down -v

local_run:
	uv run src/telegram_bot_tts/app.py

test:
	PYTHONPATH=. uv run pytest tests 