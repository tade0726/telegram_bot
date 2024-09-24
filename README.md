# openai_tts_telegram_bot


This repo hosts the telegram bot @openaitts_bot, it serves two simple functions:

1. Convert text to audio msg
2. Transcribe audio msg back to text 

Both functionarities ultize openai API



## If you want to self host your own bot


1. Configure your own bot with @botfather at Telegram

2. Put those confidentials in .env file under root diretory


`OPENAI_API_KEY` is the token access to openai services for both Text to Speech and Transcribe functions
`TELEGRAM_BOT_TOKEN` is the token generated from telegrame @botfather
`DATABASE_URL` is the cockroachdb database url, you can choose your own local or cloud version as you see fit.
`VIP_USER_ID_LIST` is the user_id that bypassing the free trail limit, by default I hardcoded that all free users will share a total quota of 3 dollar monthly for bot usage


```bash
# .env

OPENAI_API_KEY=''
TELEGRAM_BOT_TOKEN=''

DATABASE_URL="cockroachdb://root@localhost:26257/defaultdb?sslmode=disable"
VIP_USER_ID_LIST="101,"

```


3. init the database instance


```bash
# trigger the local db
make local_db
```

4. run the db_manager.py to initial the database



5. trigger the service of bot

```bash
make run
```





## TODO

- add stats on user usages


## bug fix 

- ~~long recording is not aceptiable in openai api~~
