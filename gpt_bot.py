import os
import logging
from threading import Thread
from flask import Flask
from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# 1. Embedded HTTP server for Render health checks
web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return "Gemini Bot is online!", 200

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# 2. Initialize Gemini Client (automatically reads GEMINI_API_KEY environment variable)
gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ជម្រាបសួរ! ខ្ញុំគឺជា Telegram Bot ដែលប្រើប្រាស់ Google Gemini (Free API)។ តើខ្ញុំអាចជួយអ្វីអ្នកបានខ្លះនៅថ្ងៃនេះ?"
    )

async def handle_gemini_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ignore updates that aren't standard text messages (e.g., photos, stickers, edited messages)
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # Asynchronous query to Gemini 2.5 Flash
        response = await gemini_client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are a helpful, polite, and clear AI assistant in a Telegram chat. "
                    "Always respond in natural, grammatically correct Khmer language (ភាសាខ្មែរ). "
                    "If the user asks in English or another language, still answer them in Khmer unless explicitly asked otherwise."
                ),
                max_output_tokens=600,
            ),
        )

        await update.message.reply_text(response.text)

    except Exception as e:
        logging.error(f"Gemini API Error: {e}")
        await update.message.reply_text(
            "សូមអភ័យទោស មានបញ្ហាក្នុងការដំណើរការសំណើរបស់អ្នក។ សូមព្យាយាមម្តងទៀតនៅពេលក្រោយ។"
        )

def main():
    Thread(target=run_web_server, daemon=True).start()

    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not telegram_token:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN environment variable.")

    app = ApplicationBuilder().token(telegram_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_gemini_query))

    print("Starting Khmer Gemini Telegram Bot...")
    app.run_polling()

if __name__ == "__main__":
    main()
