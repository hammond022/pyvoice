from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import os

# Replace 'YOUR_BOT_TOKEN' with your actual bot token or set it as an environment variable
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7877685273:AAEyRZ7g_BAPT9HJogIHxHZcPqXLe1pGxQ4")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"Your chat ID is: {chat_id}")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
