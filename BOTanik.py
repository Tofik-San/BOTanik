import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from openai import OpenAI

# Переменные окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Telegram-приложение
app = FastAPI()
telegram_app = Application.builder().token(BOT_TOKEN).build()

@app.on_event("startup")
async def startup():
    await telegram_app.initialize()
client = OpenAI(api_key=OPENAI_API_KEY)

# GPT-обработка текста
async def process_text_with_gpt(user_text: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """Ты — админ-бот, работающий внутри Telegram.  

"""},
                {"role": "user", "content": user_text}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("GPT Error:", e)
        return "Ошибка при обработке. Попробуй снова позже."

# Обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        user_text = update.message.text
        response = await process_text_with_gpt(user_text)
        await update.message.reply_text(response)

# Роутинг Telegram
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# FastAPI — вебхук
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}
