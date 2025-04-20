# Telegram Bot с LLM интеграцией

Telegram бот, отвечающий на вопросы с помощью LLM моделей и сохраняющий статистику для аналитики.

## Компоненты

- **llm_telegram_bot**: Основной сервис Telegram бота
- **postgres**: БД для хранения статистики взаимодействий
- **yandexgpt-adapter**: Адаптер для Yandex GPT, обеспечивающий совместимость с OpenAI API

## Особенности

- Поддержка различных LLM моделей через OpenAI-совместимый API
- Работа с YandexGPT через адаптер, предоставляющий совместимый с OpenAI API интерфейс
- Сохранение статистики в PostgreSQL для последующего анализа в DataLens
- Экспорт данных на Яндекс.Диск для интеграции с DataLens

## Запуск

1. Клонировать репозиторий
2. Инициализировать подмодули:
   ```
   git submodule update --init --recursive
   ```
3. Создать и настроить файлы переменных окружения:
   ```
   cp llm_telegram_bot/.env.example llm_telegram_bot/.env
   cp postgres/.env.example postgres/.env
   ```
4. Запустить сервисы:
   ```
   docker compose up -d
   ```

## Переменные окружения

- Токен Telegram бота (`TELEGRAM_BOT_TOKEN`)
- Ключ OpenAI API (`LLM_API_KEY`)
- URL API (`LLM_API_URL`)
- Модель LLM (`MODEL`)
- Токен Яндекс.Диска (`YADISK_TOKEN`)

## Настройка YandexGPT

Для использования YandexGPT:
1. Получите API ключ в личном кабинете [Yandex Cloud](https://cloud.yandex.ru/)
2. В .env файле укажите `LLM_API_URL=http://yandexgpt-adapter:9041/v1`


## Аналитика

Статистика взаимодействий сохраняется в PostgreSQL и используется для построения дашбордов в DataLens. Основные показатели:
- Количество запросов
- Использование токенов
- Активность пользователей 