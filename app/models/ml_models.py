"""
ML model performance tracking
"""

from sqlalchemy import Column, String, Integer, DateTime, DECIMAL, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.config.database import Base

class MLModelPerformance(Base):
    """ML model performance metrics and metadata"""
    
    __tablename__ = "ml_model_performance"
    __table_args__ = {"schema": "trading"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(100), nullable=False, index=True)
    model_type = Column(String(50), nullable=False)  # lstm, cnn, ensemble, etc.
    symbol = Column(String(20), nullable=True, index=True)
    
    # Performance metrics
    accuracy = Column(DECIMAL(5, 4), nullable=True)
    precision_score = Column(DECIMAL(5, 4), nullable=True)
    recall = Column(DECIMAL(5, 4), nullable=True)
    f1_score = Column(DECIMAL(5, 4), nullable=True)
    
    # Training info
    training_samples = Column(Integer, nullable=True)
    validation_samples = Column(Integer, nullable=True)
    training_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Model metadata
    model_version = Column(String(50), nullable=True)
    hyperparameters = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<MLModelPerformance(model='{self.model_name}', accuracy={self.accuracy})>"
    
    def to_dict(self):
        """Convert model performance to dictionary"""
        return {
            "id": str(self.id),
            "model_name": self.model_name,
            "model_type": self.model_type,
            "symbol": self.symbol,
            "accuracy": float(self.accuracy) if self.accuracy else None,
            "precision_score": float(self.precision_score) if self.precision_score else None,
            "recall": float(self.recall) if self.recall else None,
            "f1_score": float(self.f1_score) if self.f1_score else None,
            "training_samples": self.training_samples,
            "validation_samples": self.validation_samples,
            "training_date": self.training_date.isoformat() if self.training_date else None,
            "model_version": self.model_version,
            "hyperparameters": self.hyperparameters,
            "metrics": self.metrics
        } 