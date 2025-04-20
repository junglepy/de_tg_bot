FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/llm_telegram_bot /app/llm_telegram_bot

CMD ["python", "/app/llm_telegram_bot/bot.py"]