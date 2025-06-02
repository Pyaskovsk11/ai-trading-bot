"""
Database configuration for AI Trading Bot
Supports PostgreSQL and Redis connections
"""

import os
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
import redis.asyncio as redis
import asyncpg
from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)

class DatabaseSettings(BaseSettings):
    """Database configuration settings"""
    
    # PostgreSQL settings
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "trading_user"
    postgres_password: str = "trading_password_2025"
    postgres_db: str = "trading_bot"
    postgres_schema: str = "trading"
    
    # Redis settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = "redis_password_2025"
    redis_db: int = 0
    
    # Connection pool settings
    postgres_pool_size: int = 20
    postgres_max_overflow: int = 30
    postgres_pool_timeout: int = 30
    postgres_pool_recycle: int = 3600
    
    # Redis connection settings
    redis_max_connections: int = 50
    redis_socket_timeout: int = 30
    redis_socket_connect_timeout: int = 30
    
    class Config:
        env_file = ".env"
        env_prefix = "DB_"
        extra = "ignore"

# Global settings instance
db_settings = DatabaseSettings()

class DatabaseManager:
    """Database connection manager for PostgreSQL and Redis"""
    
    def __init__(self):
        self.postgres_engine = None
        self.postgres_async_engine = None
        self.postgres_session_factory = None
        self.redis_client = None
        self._initialized = False
    
    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL connection URL"""
        return (
            f"postgresql://{db_settings.postgres_user}:{db_settings.postgres_password}"
            f"@{db_settings.postgres_host}:{db_settings.postgres_port}/{db_settings.postgres_db}"
        )
    
    @property
    def postgres_async_url(self) -> str:
        """Get PostgreSQL async connection URL"""
        return (
            f"postgresql+asyncpg://{db_settings.postgres_user}:{db_settings.postgres_password}"
            f"@{db_settings.postgres_host}:{db_settings.postgres_port}/{db_settings.postgres_db}"
        )
    
    @property
    def redis_url(self) -> str:
        """Get Redis connection URL"""
        return (
            f"redis://:{db_settings.redis_password}@{db_settings.redis_host}:"
            f"{db_settings.redis_port}/{db_settings.redis_db}"
        )
    
    async def initialize(self):
        """Initialize database connections"""
        if self._initialized:
            return
        
        try:
            # Initialize PostgreSQL connections
            await self._init_postgres()
            
            # Initialize Redis connection
            await self._init_redis()
            
            self._initialized = True
            logger.info("Database connections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            raise
    
    async def _init_postgres(self):
        """Initialize PostgreSQL connections"""
        try:
            # Create async engine with more conservative settings
            self.postgres_async_engine = create_async_engine(
                self.postgres_async_url,
                pool_size=5,  # Уменьшаем размер пула
                max_overflow=10,  # Уменьшаем overflow
                pool_timeout=60,  # Увеличиваем timeout
                pool_recycle=1800,  # Уменьшаем recycle time
                echo=False,
                future=True,
                pool_pre_ping=True,  # Добавляем pre-ping
                connect_args={
                    "server_settings": {
                        "application_name": "ai_trading_bot",
                    }
                }
            )
            
            # Create session factory
            self.postgres_session_factory = async_sessionmaker(
                self.postgres_async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection with retry logic
            import asyncio
            for attempt in range(3):
                try:
                    async with self.postgres_async_engine.begin() as conn:
                        result = await conn.execute("SELECT 1")
                        await result.fetchone()
                    break
                except Exception as e:
                    if attempt == 2:  # Last attempt
                        raise
                    logger.warning(f"PostgreSQL connection attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(2)  # Wait 2 seconds before retry
            
            logger.info("PostgreSQL connection established")
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            raise
    
    async def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.Redis(
                host=db_settings.redis_host,
                port=db_settings.redis_port,
                password=db_settings.redis_password,
                db=db_settings.redis_db,
                max_connections=20,  # Уменьшаем количество соединений
                socket_timeout=10,  # Уменьшаем timeout
                socket_connect_timeout=10,
                decode_responses=True,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection with retry logic
            import asyncio
            for attempt in range(3):
                try:
                    await self.redis_client.ping()
                    break
                except Exception as e:
                    if attempt == 2:  # Last attempt
                        raise
                    logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(2)  # Wait 2 seconds before retry
            
            logger.info("Redis connection established")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise
    
    def get_postgres_session(self) -> AsyncSession:
        """Get PostgreSQL async session"""
        if not self._initialized:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        
        return self.postgres_session_factory()
    
    async def get_redis_client(self) -> redis.Redis:
        """Get Redis client"""
        if not self._initialized:
            await self.initialize()
        
        return self.redis_client
    
    async def close(self):
        """Close all database connections"""
        try:
            if self.postgres_async_engine:
                await self.postgres_async_engine.dispose()
                logger.info("PostgreSQL connections closed")
            
            if self.redis_client:
                await self.redis_client.close()
                logger.info("Redis connection closed")
            
            self._initialized = False
            
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")
    
    async def health_check(self) -> dict:
        """Check health of all database connections"""
        health = {
            "postgres": False,
            "redis": False,
            "overall": False
        }
        
        try:
            # Check PostgreSQL
            if self.postgres_async_engine:
                async with self.postgres_async_engine.begin() as conn:
                    await conn.execute("SELECT 1")
                health["postgres"] = True
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
        
        try:
            # Check Redis
            if self.redis_client:
                await self.redis_client.ping()
                health["redis"] = True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
        
        health["overall"] = health["postgres"] and health["redis"]
        return health

# Global database manager instance
db_manager = DatabaseManager()

# SQLAlchemy Base for ORM models
Base = declarative_base()

# Dependency functions for FastAPI
async def get_db_session():
    """Dependency to get database session"""
    if not db_manager._initialized:
        await db_manager.initialize()
    
    async with db_manager.get_postgres_session() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_redis() -> redis.Redis:
    """Dependency to get Redis client"""
    return await db_manager.get_redis_client()

# Cache utilities
class CacheManager:
    """Redis cache management utilities"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: str, expire: int = 3600) -> bool:
        """Set value in cache with expiration"""
        try:
            return await self.redis.setex(key, expire, value)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            return bool(await self.redis.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return bool(await self.redis.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter in cache"""
        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return 0
    
    async def set_hash(self, key: str, mapping: dict, expire: int = 3600) -> bool:
        """Set hash in cache"""
        try:
            await self.redis.hset(key, mapping=mapping)
            if expire > 0:
                await self.redis.expire(key, expire)
            return True
        except Exception as e:
            logger.error(f"Cache hash set error for key {key}: {e}")
            return False
    
    async def get_hash(self, key: str) -> dict:
        """Get hash from cache"""
        try:
            return await self.redis.hgetall(key)
        except Exception as e:
            logger.error(f"Cache hash get error for key {key}: {e}")
            return {}

async def get_cache_manager() -> CacheManager:
    """Dependency to get cache manager"""
    redis_client = await db_manager.get_redis_client()
    return CacheManager(redis_client) 