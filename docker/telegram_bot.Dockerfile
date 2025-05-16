FROM python:3.11-slim

WORKDIR /bot

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install python-telegram-bot fastapi sqlalchemy

COPY ./telegram_bot ./telegram_bot
COPY .env .env

CMD ["python", "telegram_bot/bot.py"] 