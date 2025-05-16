from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, CheckConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    """
    Модель пользователя (whitelist).
    """
    __tablename__ = 'users'
    __table_args__ = (
        Index('ix_users_telegram_id', 'telegram_id'),
        Index('ix_users_whitelist_status', 'whitelist_status'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String(50), unique=True, nullable=False, index=True, comment="Telegram user ID")
    username = Column(String(100), nullable=True, comment="Telegram username")
    email = Column(String(255), nullable=True, comment="User email")
    whitelist_status = Column(Boolean, default=False, nullable=False, comment="Whitelist access")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="Created at")
    last_active = Column(DateTime, nullable=True, comment="Last active time")
    settings = Column(JSONB, nullable=True, comment="User settings (JSONB)")

    trades = relationship("Trade", back_populates="user", passive_deletes=True)

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id='{self.telegram_id}')>"

class XAIExplanation(Base):
    """
    Модель объяснения XAI.
    """
    __tablename__ = 'xai_explanations'
    __table_args__ = (
        Index('ix_xai_explanations_created_at', 'created_at'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    explanation_text = Column(Text, nullable=False, comment="XAI explanation text")
    factors_used = Column(JSONB, nullable=True, comment="Factors used for explanation (JSONB)")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="Created at")
    model_version = Column(String(50), nullable=True, comment="XAI model version")

    signals = relationship("Signal", back_populates="xai_explanation")

    def __repr__(self):
        return f"<XAIExplanation(id={self.id}, model_version='{self.model_version}')>"

class Signal(Base):
    """
    Модель торгового сигнала.
    """
    __tablename__ = 'signals'
    __table_args__ = (
        Index('ix_signals_asset_pair', 'asset_pair'),
        Index('ix_signals_created_at', 'created_at'),
        Index('ix_signals_status', 'status'),
        Index('ix_signals_signal_type', 'signal_type'),
        CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='ck_signals_confidence_score'),
        CheckConstraint('smart_money_influence >= -1 AND smart_money_influence <= 1', name='ck_signals_smart_money_influence'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_pair = Column(String(20), nullable=False, comment="Asset pair (e.g., BTC/USDT)")
    signal_type = Column(String(10), nullable=False, comment="Signal type (BUY/SELL/HOLD)")
    confidence_score = Column(Float, nullable=False, comment="Confidence score [0,1]")
    price_at_signal = Column(Float, nullable=False, comment="Price at signal time")
    target_price = Column(Float, nullable=True, comment="Target price")
    stop_loss = Column(Float, nullable=True, comment="Stop loss level")
    time_frame = Column(String(10), nullable=False, comment="Time frame")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="Created at")
    expires_at = Column(DateTime, nullable=True, comment="Signal expiration time")
    status = Column(String(20), nullable=False, comment="Signal status")
    technical_indicators = Column(JSONB, nullable=True, comment="Technical indicators (JSONB)")
    xai_explanation_id = Column(Integer, ForeignKey('xai_explanations.id', name='fk_signals_xai_explanation_id'), nullable=True)
    smart_money_influence = Column(Float, nullable=True, comment="Smart money influence [-1,1]")
    volatility_estimate = Column(Float, nullable=True, comment="Volatility estimate")

    xai_explanation = relationship("XAIExplanation", back_populates="signals")
    trades = relationship("Trade", back_populates="signal", passive_deletes=True)
    news_relevance = relationship("SignalNewsRelevance", back_populates="signal", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Signal(id={self.id}, asset_pair='{self.asset_pair}', type='{self.signal_type}')>"

class Trade(Base):
    """
    Модель сделки (trade).
    """
    __tablename__ = 'trades'
    __table_args__ = (
        Index('ix_trades_signal_id', 'signal_id'),
        Index('ix_trades_user_id', 'user_id'),
        Index('ix_trades_entry_time', 'entry_time'),
        Index('ix_trades_status', 'status'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    signal_id = Column(Integer, ForeignKey('signals.id', name='fk_trades_signal_id', ondelete='SET NULL'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id', name='fk_trades_user_id', ondelete='SET NULL'), nullable=True)
    entry_price = Column(Float, nullable=False, comment="Entry price")
    exit_price = Column(Float, nullable=True, comment="Exit price")
    volume = Column(Float, nullable=False, comment="Trade volume")
    pnl = Column(Float, nullable=True, comment="Profit/Loss")
    pnl_percentage = Column(Float, nullable=True, comment="PnL percentage")
    entry_time = Column(DateTime, default=datetime.utcnow, nullable=False, comment="Entry time")
    exit_time = Column(DateTime, nullable=True, comment="Exit time")
    status = Column(String(20), nullable=False, comment="Trade status")
    notes = Column(Text, nullable=True, comment="Trade notes")

    signal = relationship("Signal", back_populates="trades")
    user = relationship("User", back_populates="trades")

    def __repr__(self):
        return f"<Trade(id={self.id}, signal_id={self.signal_id}, user_id={self.user_id})>"

class NewsArticle(Base):
    """
    Модель новости (news article).
    """
    __tablename__ = 'news_articles'
    __table_args__ = (
        Index('ix_news_articles_published_at', 'published_at'),
        Index('ix_news_articles_processed', 'processed'),
        Index('ix_news_articles_sentiment_score', 'sentiment_score'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, comment="News title")
    content = Column(Text, nullable=False, comment="News content")
    source = Column(String(100), nullable=True, comment="News source")
    published_at = Column(DateTime, nullable=False, comment="Published at")
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False, comment="Fetched at")
    sentiment_score = Column(Float, nullable=True, comment="Sentiment score [-1,1]")
    processed = Column(Boolean, default=False, nullable=False, comment="Processed by RAG")
    url = Column(String(512), nullable=True, comment="News URL")
    affected_assets = Column(ARRAY(String), nullable=True, comment="Affected assets (array)")

    news_relevance = relationship("SignalNewsRelevance", back_populates="news_article", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<NewsArticle(id={self.id}, title='{self.title}')>"

class SignalNewsRelevance(Base):
    """
    Модель связи сигнал-новость (многие-ко-многим).
    """
    __tablename__ = 'signal_news_relevance'
    __table_args__ = (
        Index('ix_signal_news_relevance_signal_id', 'signal_id'),
        Index('ix_signal_news_relevance_news_id', 'news_id'),
        Index('ix_signal_news_relevance_relevance_score', 'relevance_score'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    signal_id = Column(Integer, ForeignKey('signals.id', name='fk_signal_news_relevance_signal_id', ondelete='CASCADE'), nullable=False)
    news_id = Column(Integer, ForeignKey('news_articles.id', name='fk_signal_news_relevance_news_id', ondelete='CASCADE'), nullable=False)
    relevance_score = Column(Float, nullable=False, comment="Relevance score [0,1]")
    impact_type = Column(String(20), nullable=False, comment="Impact type (POSITIVE/NEGATIVE/NEUTRAL)")

    signal = relationship("Signal", back_populates="news_relevance")
    news_article = relationship("NewsArticle", back_populates="news_relevance")

    def __repr__(self):
        return f"<SignalNewsRelevance(id={self.id}, signal_id={self.signal_id}, news_id={self.news_id})>" 