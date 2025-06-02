"""
Portfolio and position models
"""

from sqlalchemy import Column, String, DateTime, DECIMAL, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.config.database import Base

class Portfolio(Base):
    """User portfolio"""
    
    __tablename__ = "portfolios"
    __table_args__ = {"schema": "trading"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('trading.users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Portfolio metrics
    total_value = Column(DECIMAL(20, 8), default=0, nullable=False)
    total_pnl = Column(DECIMAL(20, 8), default=0, nullable=False)
    total_pnl_percent = Column(DECIMAL(10, 4), default=0, nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Portfolio(id={self.id}, name='{self.name}', value={self.total_value})>"
    
    def to_dict(self):
        """Convert portfolio to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "name": self.name,
            "description": self.description,
            "total_value": float(self.total_value),
            "total_pnl": float(self.total_pnl),
            "total_pnl_percent": float(self.total_pnl_percent),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class PortfolioPosition(Base):
    """Individual positions within a portfolio"""
    
    __tablename__ = "portfolio_positions"
    __table_args__ = {"schema": "trading"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey('trading.portfolios.id', ondelete='CASCADE'), nullable=False, index=True)
    
    symbol = Column(String(20), nullable=False, index=True)
    quantity = Column(DECIMAL(20, 8), nullable=False)
    average_price = Column(DECIMAL(20, 8), nullable=False)
    current_price = Column(DECIMAL(20, 8), nullable=True)
    market_value = Column(DECIMAL(20, 8), nullable=True)
    unrealized_pnl = Column(DECIMAL(20, 8), nullable=True)
    unrealized_pnl_percent = Column(DECIMAL(10, 4), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<PortfolioPosition(symbol='{self.symbol}', quantity={self.quantity}, value={self.market_value})>"
    
    def to_dict(self):
        """Convert position to dictionary"""
        return {
            "id": str(self.id),
            "portfolio_id": str(self.portfolio_id),
            "symbol": self.symbol,
            "quantity": float(self.quantity),
            "average_price": float(self.average_price),
            "current_price": float(self.current_price) if self.current_price else None,
            "market_value": float(self.market_value) if self.market_value else None,
            "unrealized_pnl": float(self.unrealized_pnl) if self.unrealized_pnl else None,
            "unrealized_pnl_percent": float(self.unrealized_pnl_percent) if self.unrealized_pnl_percent else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        } 