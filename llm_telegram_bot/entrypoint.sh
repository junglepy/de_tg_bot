#!/bin/sh
set -e

# Ожидание готовности PostgreSQL
echo "Ожидание готовности PostgreSQL..."
export PGPASSWORD=$POSTGRES_PASSWORD
while ! pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER; do
  echo "PostgreSQL недоступен - ожидание..."
  sleep 2
done
echo "PostgreSQL готов!"

# Инициализация базы данных
echo "Инициализация базы данных..."
psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -c "
CREATE TABLE IF NOT EXISTS analytics (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    datetime TIMESTAMP NOT NULL,
    action VARCHAR(50) NOT NULL,
    completion_tokens INT DEFAULT 0,
    prompt_tokens INT DEFAULT 0,
    model VARCHAR(100),
    messages JSONB,
    answer TEXT
);"

echo "База данных инициализирована!"

# Ожидание готовности YandexGPT адаптера
echo "Ожидание готовности YandexGPT адаптера..."
sleep 10
echo "Предполагаем, что YandexGPT адаптер готов!"

# Запуск экспортера в фоновом режиме
echo "Запуск экспортера данных в фоновом режиме..."
python -m llm_telegram_bot.export &

# Запуск основного приложения
echo "Запуск Telegram бота..."
exec python /app/llm_telegram_bot/bot.py 