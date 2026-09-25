import os
import logging
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Setup logging to see errors in Render
logging.basicConfig(level=logging.INFO)

# --- Flask Keepalive for Render ---
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "Admiral Bot is LIVE!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

# --- Telegram ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Admiral Movies Bot is LIVE ✅")

def main():
    # Start Flask in background
    threading.Thread(target=run_flask, daemon=True).start()
    logging.info("Flask started, now starting bot...")

    if not BOT_TOKEN:
        logging.error("BOT_TOKEN MISSING!")
        return

    telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    
    logging.info("Bot polling started...")
    telegram_app.run_polling()

if __name__ == "main":
    main()