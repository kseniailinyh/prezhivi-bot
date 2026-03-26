# Преживи – сербский разговорник в Telegram

Telegram-бот, который генерирует мини-разговорники на сербском языке для бытовых ситуаций. Опиши ситуацию на русском – получи готовые фразы на сербском.

Работает на Google Gemini API (бесплатный тир).

## Пример

**Ты пишешь:** _Иду на почту забрать посылку_

**Бот отвечает:**

> 📍 Получение посылки на почте
>
> 🗣 Ты говоришь:
> - Dobar dan, imam pošiljku za preuzimanje. → Добрый день, у меня посылка для получения.
> - Evo koda. → Вот код.
>
> 👂 Тебе могут сказать:
> - Dajte mi ličnu kartu, molim vas. → Дайте удостоверение личности, пожалуйста.
>
> 📝 Полезные слова:
> - pošiljka – посылка
> - lična karta – удостоверение личности

## Команды бота

- `/start` – приветствие и инструкция
- `/sos` – универсальные фразы-спасатели
- `/help` – краткая справка

## Запуск локально

1. Склонируй репозиторий:
   ```bash
   git clone https://github.com/kseniailinyh/prezhivi-bot.git
   cd prezhivi-bot
   ```

2. Создай виртуальное окружение и установи зависимости:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Создай файл `.env` на основе `.env.example` и заполни токены:
   ```bash
   cp .env.example .env
   ```

4. Экспортируй переменные и запусти:
   ```bash
   export $(cat .env | xargs)
   python bot.py
   ```

## Деплой на Railway

1. Зайди на [railway.com](https://railway.com) и подключи GitHub-репозиторий.
2. В **Settings → Variables** добавь:
   - `TELEGRAM_BOT_TOKEN` – токен от @BotFather
   - `GEMINI_API_KEY` – ключ от Google AI Studio
3. Бот запустится автоматически.

## Переменные окружения

| Переменная | Описание |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота от @BotFather |
| `GEMINI_API_KEY` | API-ключ из [Google AI Studio](https://aistudio.google.com) |

## Бесплатный тир Gemini API

Модель `gemini-2.5-flash` на бесплатном тире:
- 10 запросов в минуту
- 250 запросов в день
- 250 000 токенов в минуту

Для личного бота-разговорника этого более чем достаточно. Карта не нужна.

> Промпты на бесплатном тире могут использоваться Google для улучшения моделей – учитывай это, если важна приватность.
