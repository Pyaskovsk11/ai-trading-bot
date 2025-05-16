import os
import logging
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать в AI Trading Bot! Используйте /status, /latest_signal, /summary.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        resp = requests.get(f"{API_BASE_URL}/")
        if resp.ok:
            data = resp.json()
            await update.message.reply_text(f"Статус API: {data.get('status', 'unknown')}")
        else:
            await update.message.reply_text("Ошибка при получении статуса API.")
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("Ошибка соединения с API.")

async def latest_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        resp = requests.get(f"{API_BASE_URL}/signals/?limit=1")
        if resp.ok and resp.json().get('items'):
            signal = resp.json()['items'][0]
            msg = f"Последний сигнал: {signal['signal_type']} по {signal['asset_pair']}\nЦена: {signal['price_at_signal']}\nВремя: {signal['created_at']}"
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("Нет сигналов.")
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("Ошибка соединения с API.")

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Сводка пока не реализована.")

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        resp = requests.get(f"{API_BASE_URL}/news/?limit=3")
        if resp.ok and resp.json().get('items'):
            news_items = resp.json()['items']
            if not news_items:
                await update.message.reply_text("Нет новостей.")
                return
            for n in news_items:
                msg = f"📰 {n['title']}\nИсточник: {n.get('source', 'N/A')}\nДата: {n['published_at']}\nТональность: {n.get('sentiment_score', 'N/A')}\n{n.get('url', '')}"
                await update.message.reply_text(msg)
        else:
            await update.message.reply_text("Нет новостей.")
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("Ошибка соединения с API.")

async def trades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        resp = requests.get(f"{API_BASE_URL}/trades/?limit=3")
        if resp.ok and resp.json().get('items'):
            trades = resp.json()['items']
            if not trades:
                await update.message.reply_text("Нет сделок.")
                return
            for t in trades:
                msg = f"Сделка #{t['id']}\nВход: {t['entry_price']}\nВыход: {t.get('exit_price', 'N/A')}\nОбъём: {t['volume']}\nPnL: {t.get('pnl', 'N/A')}\nСтатус: {t['status']}\nВремя входа: {t['entry_time']}"
                await update.message.reply_text(msg)
        else:
            await update.message.reply_text("Нет сделок.")
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("Ошибка соединения с API.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("latest_signal", latest_signal))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("trades", trades))
    logger.info("Telegram bot started.")
    app.run_polling()

if __name__ == "__main__":
    main() 