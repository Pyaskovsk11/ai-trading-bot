#!/usr/bin/env python3
"""
Конфигурация для реальной торговли с API ключами
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

class TradingMode(Enum):
    """Режимы торговли"""
    DEMO = "demo"  # Демо торговля (бумажная)
    LIVE = "live"  # Реальная торговля
    BACKTEST = "backtest"  # Исторический тест

class ExchangeType(Enum):
    """Типы бирж"""
    BINGX = "bingx"
    BINANCE = "binance"
    BYBIT = "bybit"
    OKX = "okx"

@dataclass
class APICredentials:
    """Учетные данные API"""
    api_key: str
    secret_key: str
    passphrase: Optional[str] = None  # Для некоторых бирж
    sandbox: bool = True  # Использовать тестовую среду
    
    def is_valid(self) -> bool:
        """Проверка валидности ключей"""
        return bool(self.api_key and self.secret_key)

@dataclass
class TradingConfig:
    """Основная конфигурация торговли"""
    # Режим торговли
    mode: TradingMode = TradingMode.DEMO
    exchange: ExchangeType = ExchangeType.BINGX
    
    # API учетные данные
    credentials: Optional[APICredentials] = None
    
    # Торговые параметры
    initial_capital: float = 10000.0
    max_daily_loss: float = 0.02  # 2% максимальный дневной убыток
    max_position_size: float = 0.1  # 10% максимальный размер позиции
    max_open_positions: int = 5
    
    # Символы для торговли
    trading_symbols: List[str] = None
    
    # Стратегии
    enable_scalping: bool = True
    enable_swing_trading: bool = True
    enable_ml_predictions: bool = False  # Пока отключено
    
    # Риск-менеджмент
    use_stop_loss: bool = True
    use_take_profit: bool = True
    use_trailing_stop: bool = True
    
    # Уведомления
    enable_telegram_notifications: bool = False
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    
    def __post_init__(self):
        if self.trading_symbols is None:
            self.trading_symbols = [
                'BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'BNBUSDT', 
                'SOLUSDT', 'XRPUSDT', 'DOGEUSDT', 'AVAXUSDT'
            ]

class ConfigManager:
    """Менеджер конфигурации"""
    
    def __init__(self):
        self.config = TradingConfig()
        self._load_from_env()
    
    def _load_from_env(self):
        """Загрузка конфигурации из переменных окружения"""
        # Режим торговли
        mode = os.getenv('TRADING_MODE', 'demo').lower()
        if mode in ['live', 'real']:
            self.config.mode = TradingMode.LIVE
        elif mode == 'backtest':
            self.config.mode = TradingMode.BACKTEST
        else:
            self.config.mode = TradingMode.DEMO
        
        # Биржа
        exchange = os.getenv('EXCHANGE', 'bingx').lower()
        if exchange == 'binance':
            self.config.exchange = ExchangeType.BINANCE
        elif exchange == 'bybit':
            self.config.exchange = ExchangeType.BYBIT
        elif exchange == 'okx':
            self.config.exchange = ExchangeType.OKX
        else:
            self.config.exchange = ExchangeType.BINGX
        
        # API ключи
        api_key = os.getenv('API_KEY') or os.getenv('BINGX_API_KEY')
        secret_key = os.getenv('SECRET_KEY') or os.getenv('BINGX_SECRET_KEY')
        passphrase = os.getenv('PASSPHRASE')
        sandbox = os.getenv('SANDBOX', 'true').lower() == 'true'
        
        if api_key and secret_key:
            self.config.credentials = APICredentials(
                api_key=api_key,
                secret_key=secret_key,
                passphrase=passphrase,
                sandbox=sandbox
            )
        
        # Торговые параметры
        self.config.initial_capital = float(os.getenv('INITIAL_CAPITAL', '10000'))
        self.config.max_daily_loss = float(os.getenv('MAX_DAILY_LOSS', '0.02'))
        self.config.max_position_size = float(os.getenv('MAX_POSITION_SIZE', '0.1'))
        self.config.max_open_positions = int(os.getenv('MAX_OPEN_POSITIONS', '5'))
        
        # Символы
        symbols_env = os.getenv('TRADING_SYMBOLS')
        if symbols_env:
            self.config.trading_symbols = [s.strip() for s in symbols_env.split(',')]
        
        # Стратегии
        self.config.enable_scalping = os.getenv('ENABLE_SCALPING', 'true').lower() == 'true'
        self.config.enable_swing_trading = os.getenv('ENABLE_SWING_TRADING', 'true').lower() == 'true'
        self.config.enable_ml_predictions = os.getenv('ENABLE_ML_PREDICTIONS', 'false').lower() == 'true'
        
        # Telegram уведомления
        self.config.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.config.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.config.enable_telegram_notifications = bool(
            self.config.telegram_bot_token and self.config.telegram_chat_id
        )
    
    def get_config(self) -> TradingConfig:
        """Получить текущую конфигурацию"""
        return self.config
    
    def is_live_trading_enabled(self) -> bool:
        """Проверка, включена ли реальная торговля"""
        return (
            self.config.mode == TradingMode.LIVE and
            self.config.credentials and
            self.config.credentials.is_valid()
        )
    
    def get_status_summary(self) -> Dict[str, str]:
        """Получить сводку статуса конфигурации"""
        status = {
            'mode': self.config.mode.value,
            'exchange': self.config.exchange.value,
            'api_configured': 'Yes' if self.config.credentials and self.config.credentials.is_valid() else 'No',
            'sandbox': 'Yes' if self.config.credentials and self.config.credentials.sandbox else 'No',
            'symbols_count': str(len(self.config.trading_symbols)),
            'scalping_enabled': 'Yes' if self.config.enable_scalping else 'No',
            'swing_trading_enabled': 'Yes' if self.config.enable_swing_trading else 'No',
            'ml_enabled': 'Yes' if self.config.enable_ml_predictions else 'No',
            'telegram_notifications': 'Yes' if self.config.enable_telegram_notifications else 'No'
        }
        return status
    
    def create_env_template(self) -> str:
        """Создать шаблон .env файла"""
        template = """# AI Trading Bot Configuration

# Trading Mode: demo, live, backtest
TRADING_MODE=demo

# Exchange: bingx, binance, bybit, okx
EXCHANGE=bingx

# API Credentials (REQUIRED for live trading)
API_KEY=your_api_key_here
SECRET_KEY=your_secret_key_here
PASSPHRASE=your_passphrase_here  # Only for some exchanges
SANDBOX=true  # Use sandbox/testnet environment

# Trading Parameters
INITIAL_CAPITAL=10000
MAX_DAILY_LOSS=0.02  # 2% maximum daily loss
MAX_POSITION_SIZE=0.1  # 10% maximum position size
MAX_OPEN_POSITIONS=5

# Trading Symbols (comma-separated)
TRADING_SYMBOLS=BTCUSDT,ETHUSDT,ADAUSDT,BNBUSDT,SOLUSDT,XRPUSDT

# Strategy Settings
ENABLE_SCALPING=true
ENABLE_SWING_TRADING=true
ENABLE_ML_PREDICTIONS=false

# Telegram Notifications (optional)
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Risk Management
USE_STOP_LOSS=true
USE_TAKE_PROFIT=true
USE_TRAILING_STOP=true
"""
        return template

# Глобальный экземпляр менеджера конфигурации
config_manager = ConfigManager()

def get_trading_config() -> TradingConfig:
    """Получить текущую торговую конфигурацию"""
    return config_manager.get_config()

def is_live_trading_ready() -> bool:
    """Проверить готовность к реальной торговле"""
    return config_manager.is_live_trading_enabled()

def get_config_status() -> Dict[str, str]:
    """Получить статус конфигурации"""
    return config_manager.get_status_summary() 