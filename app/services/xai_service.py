import logging
from sqlalchemy.orm import Session
from app.db.models import XAIExplanation
from app.utils.xai import generate_xai_explanation
from typing import Dict
from datetime import datetime

logger = logging.getLogger(__name__)

def create_and_save_xai_explanation(signal_factors: Dict, db: Session) -> int:
    """
    Генерирует XAI-объяснение, сохраняет его в БД и возвращает ID.
    """
    try:
        explanation_text = generate_xai_explanation(signal_factors)
        xai = XAIExplanation(
            explanation_text=explanation_text,
            factors_used=signal_factors,
            created_at=datetime.utcnow(),
            model_version=signal_factors.get("model_version", "v1")
        )
        db.add(xai)
        db.commit()
        db.refresh(xai)
        logger.info(f"XAI explanation saved with id={xai.id}")
        return xai.id
    except Exception as e:
        logger.error(f"Error generating or saving XAI explanation: {e}")
        return -1 