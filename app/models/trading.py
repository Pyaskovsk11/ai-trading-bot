"""
Trading-related models for market data, orders, and signals
"""

from sqlalchemy import Column, String, Integer, DateTime, DECIMAL, Boolean, Text, JSON, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.config.database import Base

class TradingPair(Base):
    """Trading pair configuration"""
    
    __tablename__ = "trading_pairs"
    __table_args__ = {"schema": "trading"}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    base_asset = Column(String(10), nullable=False)
    quote_asset = Column(String(10), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Trading constraints
    min_quantity = Column(DECIMAL(20, 8), nullable=True)
    max_quantity = Column(DECIMAL(20, 8), nullable=True)
    step_size = Column(DECIMAL(20, 8), nullable=True)
    tick_size = Column(DECIMAL(20, 8), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<TradingPair(symbol='{self.symbol}', base='{self.base_asset}', quote='{self.quote_asset}')>"

class MarketData(Base):
    """Market data (OHLCV) storage - partitioned by timestamp"""
    
    __tablename__ = "market_data"
    __table_args__ = {"schema": "trading"}
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, primary_key=True)
    
    # OHLCV data
    open_price = Column(DECIMAL(20, 8), nullable=False)
    high_price = Column(DECIMAL(20, 8), nullable=False)
    low_price = Column(DECIMAL(20, 8), nullable=False)
    close_price = Column(DECIMAL(20, 8), nullable=False)
    volume = Column(DECIMAL(20, 8), nullable=False)
    
    timeframe = Column(String(10), nullable=False)  # 1m, 5m, 1h, 1d, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<MarketData(symbol='{self.symbol}', timestamp='{self.timestamp}', close={self.close_price})>"

class TradingOrder(Base):
    """Trading orders"""
    
    __tablename__ = "trading_orders"
    __table_args__ = {"schema": "trading"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('trading.users.id', ondelete='CASCADE'), nullable=False, index=True)
    portfolio_id = Column(UUID(as_uuid=True), ForeignKey('trading.portfolios.id', ondelete='SET NULL'), nullable=True)
    
    # Order details
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # buy, sell
    type = Column(String(20), nullable=False)  # market, limit, stop, stop_limit
    quantity = Column(DECIMAL(20, 8), nullable=False)
    price = Column(DECIMAL(20, 8), nullable=True)
    stop_price = Column(DECIMAL(20, 8), nullable=True)
    filled_quantity = Column(DECIMAL(20, 8), default=0, nullable=False)
    
    # Order status
    status = Column(String(20), default='pending', nullable=False, index=True)  # pending, filled, cancelled, rejected, expired
    exchange_order_id = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    filled_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<TradingOrder(id={self.id}, symbol='{self.symbol}', side='{self.side}', status='{self.status}')>"
    
    def to_dict(self):
        """Convert order to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "portfolio_id": str(self.portfolio_id) if self.portfolio_id else None,
            "symbol": self.symbol,
            "side": self.side,
            "type": self.type,
            "quantity": float(self.quantity),
            "price": float(self.price) if self.price else None,
            "stop_price": float(self.stop_price) if self.stop_price else None,
            "filled_quantity": float(self.filled_quantity),
            "status": self.status,
            "exchange_order_id": self.exchange_order_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "filled_at": self.filled_at.isoformat() if self.filled_at else None
        }

class TradingSignal(Base):
    """AI/ML trading signals"""
    
    __tablename__ = "trading_signals"
    __table_args__ = {"schema": "trading"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False, index=True)
    signal_type = Column(String(20), nullable=False, index=True)  # buy, sell, hold
    confidence = Column(DECIMAL(5, 4), nullable=False)  # 0.0 to 1.0
    source = Column(String(50), nullable=False)  # lstm, cnn, ensemble, etc.
    model_name = Column(String(100), nullable=True)
    
    # Signal metadata
    features = Column(JSON, nullable=True)
    signal_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<TradingSignal(symbol='{self.symbol}', signal='{self.signal_type}', confidence={self.confidence})>"
    
    def to_dict(self):
        """Convert signal to dictionary"""
        return {
            "id": str(self.id),
            "symbol": self.symbol,
            "signal_type": self.signal_type,
            "confidence": float(self.confidence),
            "source": self.source,
            "model_name": self.model_name,
            "features": self.features,
            "metadata": self.signal_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        } 