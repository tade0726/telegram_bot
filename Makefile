format:
	black src/ tests/

build:
	docker-compose up -d --build

teardown:
	docker-compose down -v

run:
	uv run src/telegram_bot_tts/app.py

test:
	PYTHONPATH=. uv run pytest tests 

db_run:
# start local db in background with default port and initialize database as telegram_bot_dev
	cockroach start-single-node --insecure --store=cockroach-data \
	--listen-addr=localhost:26257 \
	--http-addr=localhost:8080
	cockroach sql --insecure -e "CREATE DATABASE IF NOT EXISTS telegram_bot_dev;"
