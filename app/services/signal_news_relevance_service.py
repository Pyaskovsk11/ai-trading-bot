from sqlalchemy.orm import Session
from app.db.models import SignalNewsRelevance
from app.schemas.signal_news_relevance import SignalNewsRelevanceCreate
from typing import Optional

def create_signal_news_relevance(db: Session, rel_in: SignalNewsRelevanceCreate) -> SignalNewsRelevance:
    rel = SignalNewsRelevance(
        signal_id=rel_in.signal_id,
        news_id=rel_in.news_id,
        relevance_score=rel_in.relevance_score,
        impact_type=rel_in.impact_type
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)
    return rel

def get_signal_news_relevance_by_id(db: Session, rel_id: int) -> Optional[SignalNewsRelevance]:
    return db.query(SignalNewsRelevance).filter(SignalNewsRelevance.id == rel_id).first() 