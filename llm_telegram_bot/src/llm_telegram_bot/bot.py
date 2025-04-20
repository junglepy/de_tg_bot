#!/usr/bin/env python
# pylint: disable=unused-argument

import logging
import os
import csv
import json
import psycopg2
from psycopg2 import sql
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# OpenAI client setup
openai_api_key = os.getenv("LLM_API_KEY")
openai_api_base = os.getenv("LLM_API_URL")
model = os.getenv("MODEL")

client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)

# Путь к CSV файлу аналитики
ANALYTICS_FILE = "/app/analytics/user_actions.csv"

# PostgreSQL config
PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")
PG_USER = os.getenv("POSTGRES_USER", "postgres")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
PG_DB = os.getenv("POSTGRES_DB", "telegram_bot")

def get_db_connection():
    """Получение соединения с БД."""
    try:
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            user=PG_USER,
            password=PG_PASSWORD,
            dbname=PG_DB
        )
        return conn
    except Exception as e:
        logger.error(f"Ошибка соединения с БД: {e}")
        return None

def log_to_db(user_id, action, completion_tokens=0, prompt_tokens=0, messages=None, answer=None):
    """Логирование в PostgreSQL."""
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("Не удалось получить соединение с БД")
            return
            
        cursor = conn.cursor()
        
        query = '''
        INSERT INTO analytics (user_id, datetime, action, completion_tokens, prompt_tokens, model, messages, answer)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''
        
        now = datetime.now()
        messages_json = json.dumps(messages) if messages else None
        
        cursor.execute(query, (
            user_id, 
            now, 
            action, 
            completion_tokens, 
            prompt_tokens,
            model,
            messages_json,
            answer
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка при записи в БД: {e}")

def log_analytics(user_id, action, completion_tokens=0, prompt_tokens=0, messages=None, answer=None):
    """Логирование действий пользователя в CSV файл и БД."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Запись в CSV
    file_exists = os.path.isfile(ANALYTICS_FILE)
    
    try:
        with open(ANALYTICS_FILE, 'a', newline='') as csvfile:
            fieldnames = ['user_id', 'datetime', 'action', 'completion_tokens', 'prompt_tokens', 'model']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                'user_id': user_id,
                'datetime': now,
                'action': action,
                'completion_tokens': completion_tokens,
                'prompt_tokens': prompt_tokens,
                'model': model
            })
    except Exception as e:
        logger.error(f"Ошибка при записи в CSV: {e}")
    
    # Запись в PostgreSQL
    log_to_db(user_id, action, completion_tokens, prompt_tokens, messages, answer)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    user_id = update.message.from_user.id
    
    # Логируем событие start
    log_analytics(user_id, "start")
    
    await update.message.reply_html(
        rf"Привет {user.mention_html()}! Я бот, который использует модель {model} для ответов на ваши вопросы.",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    user_id = update.message.from_user.id
    
    # Логируем событие help
    log_analytics(user_id, "help")
    
    await update.message.reply_text("Просто отправьте мне сообщение, и я отвечу используя LLM!")


async def process_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process the user message with OpenAI API."""
    user_message = update.message.text
    user_id = update.message.from_user.id
    
    await update.message.chat.send_action(action="typing")
    
    try:
        messages = [{'role': 'user', 'content': user_message}]
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
        )
        
        # Получение ответа от модели
        bot_response = response.choices[0].message.content
        
        # Логируем событие answer с информацией о токенах
        completion_tokens = response.usage.completion_tokens
        prompt_tokens = response.usage.prompt_tokens
        log_analytics(
            user_id, 
            "answer", 
            completion_tokens, 
            prompt_tokens, 
            messages=messages, 
            answer=bot_response
        )
        
        # Отправка ответа пользователю
        await update.message.reply_text(bot_response)
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text("Извините, произошла ошибка при обработке вашего сообщения.")


def main() -> None:
    """Start the bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("No token provided! Please set TELEGRAM_BOT_TOKEN environment variable.")
        return
        
    if not all([openai_api_key, openai_api_base, model]):
        logger.error("OpenAI API settings missing! Please set LLM_API_KEY, LLM_API_URL, and MODEL environment variables.")
        return

    application = Application.builder().token(token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - process with OpenAI
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_message))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main() 