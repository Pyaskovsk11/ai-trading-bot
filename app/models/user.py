"""
User model for authentication and user management
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, DECIMAL, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.config.database import Base

class User(Base):
    """User model for authentication and profile management"""
    
    __tablename__ = "users"
    __table_args__ = {"schema": "trading"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Encrypted API keys for trading
    api_key_encrypted = Column(Text, nullable=True)
    secret_key_encrypted = Column(Text, nullable=True)
    
    # User status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # User settings and preferences
    settings = Column(JSON, default={}, nullable=False)
    
    # Risk management settings
    risk_profile = Column(String(20), default='moderate', nullable=False)  # conservative, moderate, aggressive
    max_daily_loss = Column(DECIMAL(10, 2), default=1000.00, nullable=False)
    max_position_size = Column(DECIMAL(10, 2), default=10000.00, nullable=False)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
    
    def to_dict(self):
        """Convert user to dictionary (excluding sensitive data)"""
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "settings": self.settings,
            "risk_profile": self.risk_profile,
            "max_daily_loss": float(self.max_daily_loss) if self.max_daily_loss else None,
            "max_position_size": float(self.max_position_size) if self.max_position_size else None
        } 