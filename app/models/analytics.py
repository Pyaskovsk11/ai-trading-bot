"""
Analytics and performance tracking models
"""

from sqlalchemy import Column, String, Integer, DateTime, DECIMAL, JSON, Date, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.config.database import Base

class DailyPortfolioSnapshot(Base):
    """Daily portfolio snapshots for analytics"""
    
    __tablename__ = "daily_portfolio_snapshots"
    __table_args__ = (
        UniqueConstraint('portfolio_id', 'snapshot_date', name='uq_portfolio_snapshot_date'),
        {"schema": "analytics"}
    )
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    snapshot_date = Column(Date, nullable=False, index=True)
    
    # Portfolio metrics at snapshot time
    total_value = Column(DECIMAL(20, 8), nullable=False)
    total_pnl = Column(DECIMAL(20, 8), nullable=False)
    total_pnl_percent = Column(DECIMAL(10, 4), nullable=False)
    
    # Detailed positions data
    positions = Column(JSON, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<DailyPortfolioSnapshot(portfolio_id={self.portfolio_id}, date={self.snapshot_date}, value={self.total_value})>"
    
    def to_dict(self):
        """Convert snapshot to dictionary"""
        return {
            "id": str(self.id),
            "portfolio_id": str(self.portfolio_id),
            "snapshot_date": self.snapshot_date.isoformat() if self.snapshot_date else None,
            "total_value": float(self.total_value),
            "total_pnl": float(self.total_pnl),
            "total_pnl_percent": float(self.total_pnl_percent),
            "positions": self.positions,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class TradingPerformance(Base):
    """Trading performance metrics by period"""
    
    __tablename__ = "trading_performance"
    __table_args__ = {"schema": "analytics"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False, index=True)
    
    # Trading statistics
    total_trades = Column(Integer, default=0, nullable=False)
    winning_trades = Column(Integer, default=0, nullable=False)
    losing_trades = Column(Integer, default=0, nullable=False)
    total_pnl = Column(DECIMAL(20, 8), default=0, nullable=False)
    max_drawdown = Column(DECIMAL(10, 4), default=0, nullable=False)
    
    # Performance ratios
    sharpe_ratio = Column(DECIMAL(10, 4), nullable=True)
    win_rate = Column(DECIMAL(5, 4), nullable=True)  # 0.0 to 1.0
    avg_win = Column(DECIMAL(20, 8), nullable=True)
    avg_loss = Column(DECIMAL(20, 8), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<TradingPerformance(user_id={self.user_id}, period={self.period_start}-{self.period_end}, pnl={self.total_pnl})>"
    
    def to_dict(self):
        """Convert performance to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "total_pnl": float(self.total_pnl),
            "max_drawdown": float(self.max_drawdown),
            "sharpe_ratio": float(self.sharpe_ratio) if self.sharpe_ratio else None,
            "win_rate": float(self.win_rate) if self.win_rate else None,
            "avg_win": float(self.avg_win) if self.avg_win else None,
            "avg_loss": float(self.avg_loss) if self.avg_loss else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        } 