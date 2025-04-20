FROM python:3.9-slim

WORKDIR /app

# Установка postgresql-client для pg_isready и psql
# и других зависимостей для pandas/openpyxl
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/llm_telegram_bot /app/llm_telegram_bot
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]