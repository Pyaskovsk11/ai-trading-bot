from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from app.services.signal_generation_service import generate_signal_for_asset
from app.db.session import SessionLocal
import logging

logger = logging.getLogger(__name__)

ASSETS = ["BTC/USDT", "ETH/USDT"]

scheduler = BackgroundScheduler()

def scheduled_signal_generation():
    db: Session = SessionLocal()
    try:
        for asset in ASSETS:
            generate_signal_for_asset(asset, db)
    except Exception as e:
        logger.error(f"Error in scheduled signal generation: {e}")
    finally:
        db.close()

def start_scheduler():
    scheduler.add_job(scheduled_signal_generation, IntervalTrigger(minutes=5), id="signal_generation", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started: signal generation every 5 minutes.") 