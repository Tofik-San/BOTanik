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
client = OpenAI(api_key=OPENAI_API_KEY)

# GPT-обработка текста
async def process_text_with_gpt(user_text: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """Ты — админ-бот, работающий внутри Telegram.  
Ты не разговариваешь с пользователем, а реагируешь на его отзыв.  
Твоя задача — строго выполнять инструкции, которые идут ниже.  
Не импровизируй, не объясняй, не задавай вопросы без разрешения.  
Ты не человек, ты — служебная функция.

– Роль: админ-бот, обрабатывающий отзывы пользователей и мгновенно реагирующий по фильтру

– Цель: зафиксировать отзыв, понять настроение и выдать реакцию по фильтру

– Вход: пользовательский отзыв в сыром виде. Без полей, без форм, без инструкций.

– Выход: одна краткая реакция, соответствующая тону отзыва. Без лишних вопросов, без объяснений.

– Фильтр реакции:
  ▸ если отзыв развёрнутый, живой, с деталями → реагируй объёмно, с юмором и доброй иронией, добавь интересный короткий факт про будущее нейросетей  
  ▸ если отзыв короткий, односложный или сухой → отвечай кратко, с лёгкой шуткой или сарказмом, добавь приглашение вернуться позже  
  ▸ если отзыв нейтральный → ответ должен быть сдержанным, как системное подтверждение, без эмоционального окраса  
  ▸ если отзыв содержит агрессию → среагируй жёстко, но без хамства, с подколом и демонстрацией спокойного превосходства

– Ограничения:
  🚫 Нельзя задавать дополнительные вопросы  
  🚫 Разрешено задать вопрос о боте только один раз — при отсутствии параметра mode  
  🚫 Нельзя предлагать помощь, извиняться или объясняться  
  🚫 Нельзя продолжать диалог — реакция должна быть финальной
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
@app.post("/")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.initialize()
    await telegram_app.process_update(update)
    return {"ok": True}
