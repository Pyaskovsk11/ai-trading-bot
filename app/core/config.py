import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """
    Настройки приложения.
    Загружаются из переменных окружения или .env файла.
    """
    # База данных - используем SQLite по умолчанию
    DB_URL: str = os.getenv(
        "DB_URL",
        "sqlite:///./trading_bot.db"
    )
    
    # API настройки
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Futures Trading Bot"
    
    # Настройки безопасности
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 дней
    
    # Настройки Telegram бота
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # Настройки торговли
    DEFAULT_LEVERAGE: int = 1
    MAX_LEVERAGE: int = 10
    RISK_PER_TRADE: float = 0.02  # 2% от депозита
    
    # Настройки BingX API
    BINGX_API_KEY: str = os.getenv("BINGX_API_KEY", "")
    BINGX_API_SECRET: str = os.getenv("BINGX_API_SECRET", "")
    USE_DEMO_ACCOUNT: bool = os.getenv("USE_DEMO_ACCOUNT", "True").lower() in ("true", "1", "t")
    
    class Config:
        case_sensitive = True

settings = Settings() 