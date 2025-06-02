import pytest
from app.services import xai_service
from app.schemas.xai import XAIExplanationCreate
from sqlalchemy.orm import Session

def test_create_and_get_xai_explanation(test_db: Session):
    xai_data = {"explanation_text": "Test XAI", "factors_used": {"factor": 1}, "model_version": "v1"}
    xai = xai_service.create_xai_explanation(test_db, XAIExplanationCreate(**xai_data))
    assert xai.explanation_text == xai_data["explanation_text"]
    fetched = xai_service.get_xai_explanation_by_id(test_db, xai.id)
    assert fetched is not None
    assert fetched.model_version == xai_data["model_version"] 