from telegram import Update
from telegram.ext import ContextTypes


# commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "You can input any text and I will return its audio file."
    )
