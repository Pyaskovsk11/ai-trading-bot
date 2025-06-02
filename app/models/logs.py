"""
Logging models for application and API logs
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, BigInteger
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.sql import func
from app.config.database import Base

class AppLog(Base):
    """Application logs"""
    
    __tablename__ = "app_logs"
    __table_args__ = {"schema": "logs"}
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    level = Column(String(10), nullable=False, index=True)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    logger = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    
    # Code location
    module = Column(String(100), nullable=True)
    function = Column(String(100), nullable=True)
    line_number = Column(Integer, nullable=True)
    
    # Context
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    session_id = Column(String(100), nullable=True)
    request_id = Column(String(100), nullable=True)
    extra_data = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<AppLog(level='{self.level}', logger='{self.logger}', timestamp='{self.timestamp}')>"
    
    def to_dict(self):
        """Convert log to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "level": self.level,
            "logger": self.logger,
            "message": self.message,
            "module": self.module,
            "function": self.function,
            "line_number": self.line_number,
            "user_id": str(self.user_id) if self.user_id else None,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "extra_data": self.extra_data
        }

class APILog(Base):
    """API request logs"""
    
    __tablename__ = "api_logs"
    __table_args__ = {"schema": "logs"}
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Request details
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE, etc.
    path = Column(String(500), nullable=False, index=True)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    
    # User context
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Request/response size
    request_size = Column(Integer, nullable=True)
    response_size = Column(Integer, nullable=True)
    
    # Error details
    error_message = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<APILog(method='{self.method}', path='{self.path}', status={self.status_code})>"
    
    def to_dict(self):
        """Convert API log to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "method": self.method,
            "path": self.path,
            "status_code": self.status_code,
            "response_time_ms": self.response_time_ms,
            "user_id": str(self.user_id) if self.user_id else None,
            "ip_address": str(self.ip_address) if self.ip_address else None,
            "user_agent": self.user_agent,
            "request_size": self.request_size,
            "response_size": self.response_size,
            "error_message": self.error_message
        } 