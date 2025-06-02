# Промпт для AI-агента Cursor: Интеграция демо-торговли в AI трейдинг-бот

## Задача

Реализовать интеграцию с биржей BingX для торговли на демо-счете в AI трейдинг-боте. Подготовить код для безопасного взаимодействия с API биржи, размещения ордеров, получения баланса и отслеживания сделок. Обеспечить безопасное хранение API-ключей и логирование всех операций для последующего анализа.

## Компоненты для реализации

### 1. Модуль интеграции с BingX API (`app/services/exchange_service.py`)

Создать сервис для взаимодействия с API биржи BingX, который будет:

- Устанавливать соединение с API BingX
- Получать данные о балансе и открытых позициях
- Размещать ордера (market, limit)
- Отменять ордера
- Получать историю сделок
- Обрабатывать ошибки API и повторять запросы при необходимости

```python
from typing import Dict, List, Optional, Union, Any
import time
import hmac
import hashlib
import requests
import logging
from datetime import datetime
from app.core.config import settings
from app.db.models import Trade, Signal

logger = logging.getLogger(__name__)

class BingXExchangeService:
    """Сервис для взаимодействия с API биржи BingX"""

    def __init__(self, api_key: str = None, api_secret: str = None, is_demo: bool = True):
        """
        Инициализация сервиса

        :param api_key: API ключ BingX (если None, берется из настроек)
        :param api_secret: API секрет BingX (если None, берется из настроек)
        :param is_demo: Использовать демо-счет (True) или реальный счет (False)
        """
        self.api_key = api_key or settings.BINGX_API_KEY
        self.api_secret = api_secret or settings.BINGX_API_SECRET
        self.is_demo = is_demo

        # Базовый URL API BingX (разный для демо и реального счета)
        if self.is_demo:
            self.base_url = "https://open-api-swap-demo.bingx.com"
        else:
            self.base_url = "https://open-api-swap.bingx.com"

        logger.info(f"Initialized BingX Exchange Service (Demo: {is_demo})")

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """
        Генерация подписи для запросов к API

        :param params: Параметры запроса
        :return: Подпись в виде строки
        """
        query_string = '&'.join([f"{key}={params[key]}" for key in sorted(params.keys())])
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _make_request(self, method: str, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Выполнение запроса к API BingX

        :param method: HTTP метод (GET, POST, DELETE)
        :param endpoint: Эндпоинт API
        :param params: Параметры запроса
        :return: Ответ API в виде словаря
        """
        url = f"{self.base_url}{endpoint}"

        # Подготовка параметров
        params = params or {}
        params['timestamp'] = int(time.time() * 1000)
        params['recvWindow'] = 5000  # Окно приема запроса в миллисекундах

        # Добавление подписи
        signature = self._generate_signature(params)
        params['signature'] = signature

        # Добавление API ключа в заголовки
        headers = {
            'X-BX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        }

        # Выполнение запроса с повторными попытками при ошибках
        max_retries = 3
        retry_delay = 1  # секунды

        for attempt in range(max_retries):
            try:
                if method == 'GET':
                    response = requests.get(url, params=params, headers=headers)
                elif method == 'POST':
                    response = requests.post(url, json=params, headers=headers)
                elif method == 'DELETE':
                    response = requests.delete(url, params=params, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Проверка статуса ответа
                response.raise_for_status()

                # Парсинг JSON ответа
                result = response.json()

                # Проверка на ошибки в ответе API
                if 'code' in result and result['code'] != 0:
                    logger.error(f"API Error: {result['msg']} (Code: {result['code']})")
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Экспоненциальная задержка
                        continue

                return result

            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise

        raise Exception("Failed to make request after multiple retries")

    def get_account_balance(self) -> Dict[str, float]:
        """
        Получение баланса аккаунта

        :return: Словарь с балансами по валютам
        """
        endpoint = "/api/v1/account"
        response = self._make_request('GET', endpoint)

        balances = {}
        for asset in response.get('balances', []):
            balances[asset['asset']] = float(asset['free'])

        logger.info(f"Account balance retrieved: {balances}")
        return balances

    def get_open_positions(self) -> List[Dict[str, Any]]:
        """
        Получение открытых позиций

        :return: Список открытых позиций
        """
        endpoint = "/api/v1/openPositions"
        response = self._make_request('GET', endpoint)

        positions = response.get('positions', [])
        logger.info(f"Retrieved {len(positions)} open positions")
        return positions

    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict[str, Any]:
        """
        Размещение рыночного ордера

        :param symbol: Символ торговой пары (например, "BTCUSDT")
        :param side: Сторона ордера ("BUY" или "SELL")
        :param quantity: Количество для покупки/продажи
        :return: Информация о размещенном ордере
        """
        endpoint = "/api/v1/order"
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'MARKET',
            'quantity': quantity,
        }

        logger.info(f"Placing market order: {side} {quantity} {symbol}")
        response = self._make_request('POST', endpoint, params)

        logger.info(f"Market order placed: {response}")
        return response

    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Dict[str, Any]:
        """
        Размещение лимитного ордера

        :param symbol: Символ торговой пары (например, "BTCUSDT")
        :param side: Сторона ордера ("BUY" или "SELL")
        :param quantity: Количество для покупки/продажи
        :param price: Цена ордера
        :return: Информация о размещенном ордере
        """
        endpoint = "/api/v1/order"
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'LIMIT',
            'timeInForce': 'GTC',  # Good Till Cancel
            'quantity': quantity,
            'price': price
        }

        logger.info(f"Placing limit order: {side} {quantity} {symbol} @ {price}")
        response = self._make_request('POST', endpoint, params)

        logger.info(f"Limit order placed: {response}")
        return response

    def cancel_order(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """
        Отмена ордера

        :param symbol: Символ торговой пары
        :param order_id: ID ордера для отмены
        :return: Информация об отмененном ордере
        """
        endpoint = "/api/v1/order"
        params = {
            'symbol': symbol,
            'orderId': order_id
        }

        logger.info(f"Cancelling order {order_id} for {symbol}")
        response = self._make_request('DELETE', endpoint, params)

        logger.info(f"Order cancelled: {response}")
        return response

    def get_order_status(self, symbol: str, order_id: str) -> Dict[str, Any]:
        """
        Получение статуса ордера

        :param symbol: Символ торговой пары
        :param order_id: ID ордера
        :return: Информация о статусе ордера
        """
        endpoint = "/api/v1/order"
        params = {
            'symbol': symbol,
            'orderId': order_id
        }

        response = self._make_request('GET', endpoint, params)
        logger.info(f"Order status retrieved for {order_id}: {response.get('status')}")
        return response

    def get_order_history(self, symbol: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Получение истории ордеров

        :param symbol: Символ торговой пары (опционально)
        :param limit: Максимальное количество ордеров для получения
        :return: Список ордеров
        """
        endpoint = "/api/v1/allOrders"
        params = {'limit': limit}
        if symbol:
            params['symbol'] = symbol

        response = self._make_request('GET', endpoint, params)
        orders = response.get('orders', [])
        logger.info(f"Retrieved {len(orders)} orders from history")
        return orders

    def execute_signal_trade(self, signal: Signal, risk_percentage: float = 1.0) -> Optional[Trade]:
        """
        Выполнение торговли на основе сигнала

        :param signal: Объект сигнала
        :param risk_percentage: Процент от доступного баланса для риска (1.0 = 1%)
        :return: Объект сделки или None в случае ошибки
        """
        try:
            # Получение баланса
            balances = self.get_account_balance()
            usdt_balance = balances.get('USDT', 0)

            # Расчет размера позиции на основе риска
            risk_amount = usdt_balance * (risk_percentage / 100)

            # Преобразование пары активов в формат биржи
            symbol = signal.asset_pair.replace('/', '')

            # Определение стороны ордера
            side = signal.signal_type
            if side not in ['BUY', 'SELL']:
                logger.error(f"Invalid signal type for trading: {side}")
                return None

            # Расчет количества для покупки/продажи
            quantity = risk_amount / signal.price_at_signal

            # Размещение рыночного ордера
            order_response = self.place_market_order(symbol, side, quantity)

            # Создание объекта сделки
            trade = Trade(
                signal_id=signal.id,
                entry_price=float(order_response.get('price', signal.price_at_signal)),
                volume=float(order_response.get('executedQty', quantity)),
                entry_time=datetime.now(),
                status='OPEN',
                notes=f"Order ID: {order_response.get('orderId')}"
            )

            logger.info(f"Trade executed for signal {signal.id}: {trade}")
            return trade

        except Exception as e:
            logger.error(f"Error executing trade for signal {signal.id}: {str(e)}")
            return None
```

### 2. Модуль управления торговлей (`app/services/trading_service.py`)

Создать сервис для управления торговлей, который будет:

- Обрабатывать сигналы и принимать решения о торговле
- Управлять рисками и размером позиций
- Отслеживать открытые позиции и закрывать их при необходимости
- Сохранять информацию о сделках в базе данных

```python
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.models import Signal, Trade
from app.db.crud import create_trade, update_trade, get_trades_by_signal
from app.services.exchange_service import BingXExchangeService
from app.core.config import settings

logger = logging.getLogger(__name__)

class TradingService:
    """Сервис для управления торговлей на основе сигналов"""

    def __init__(self, db: Session, exchange_service: Optional[BingXExchangeService] = None):
        """
        Инициализация сервиса

        :param db: Сессия базы данных
        :param exchange_service: Сервис для взаимодействия с биржей (если None, создается новый)
        """
        self.db = db
        self.exchange_service = exchange_service or BingXExchangeService(
            is_demo=settings.USE_DEMO_ACCOUNT
        )
        logger.info(f"Trading service initialized (Demo: {settings.USE_DEMO_ACCOUNT})")

    def process_signal(self, signal_id: int, risk_percentage: float = 1.0) -> Optional[Trade]:
        """
        Обработка сигнала и выполнение торговли

        :param signal_id: ID сигнала для обработки
        :param risk_percentage: Процент от доступного баланса для риска (1.0 = 1%)
        :return: Объект сделки или None в случае ошибки
        """
        from app.db.crud import get_signal_by_id

        # Получение сигнала из базы данных
        signal = get_signal_by_id(self.db, signal_id)
        if not signal:
            logger.error(f"Signal with ID {signal_id} not found")
            return None

        # Проверка статуса сигнала
        if signal.status != 'ACTIVE':
            logger.warning(f"Signal {signal_id} is not active (status: {signal.status})")
            return None

        # Проверка срока действия сигнала
        if signal.expires_at and signal.expires_at < datetime.now():
            logger.warning(f"Signal {signal_id} has expired")
            return None

        # Выполнение торговли
        trade = self.exchange_service.execute_signal_trade(signal, risk_percentage)
        if not trade:
            logger.error(f"Failed to execute trade for signal {signal_id}")
            return None

        # Сохранение сделки в базе данных
        db_trade = create_trade(self.db, trade)
        logger.info(f"Trade created for signal {signal_id}: {db_trade.id}")

        return db_trade

    def check_and_close_trades(self) -> List[Trade]:
        """
        Проверка открытых сделок и закрытие при достижении целевой цены или стоп-лосса

        :return: Список закрытых сделок
        """
        from app.db.crud import get_open_trades

        # Получение открытых сделок
        open_trades = get_open_trades(self.db)
        logger.info(f"Checking {len(open_trades)} open trades")

        closed_trades = []

        for trade in open_trades:
            # Получение сигнала для сделки
            signal = trade.signal

            # Получение текущей цены актива
            symbol = signal.asset_pair.replace('/', '')
            current_price = self._get_current_price(symbol)

            if current_price is None:
                logger.warning(f"Could not get current price for {symbol}, skipping trade {trade.id}")
                continue

            # Проверка условий для закрытия сделки
            should_close = False
            close_reason = ""

            # Проверка достижения целевой цены
            if signal.target_price and (
                (signal.signal_type == 'BUY' and current_price >= signal.target_price) or
                (signal.signal_type == 'SELL' and current_price <= signal.target_price)
            ):
                should_close = True
                close_reason = "Target price reached"

            # Проверка достижения стоп-лосса
            elif signal.stop_loss and (
                (signal.signal_type == 'BUY' and current_price <= signal.stop_loss) or
                (signal.signal_type == 'SELL' and current_price >= signal.stop_loss)
            ):
                should_close = True
                close_reason = "Stop loss triggered"

            # Проверка времени в позиции (закрытие через 7 дней, если не сработали другие условия)
            elif trade.entry_time and trade.entry_time < datetime.now() - timedelta(days=7):
                should_close = True
                close_reason = "Position time limit reached (7 days)"

            # Закрытие сделки при необходимости
            if should_close:
                logger.info(f"Closing trade {trade.id}: {close_reason}")

                # Размещение ордера на закрытие позиции
                close_side = 'SELL' if signal.signal_type == 'BUY' else 'BUY'
                try:
                    order_response = self.exchange_service.place_market_order(
                        symbol=symbol,
                        side=close_side,
                        quantity=trade.volume
                    )

                    # Расчет P&L
                    exit_price = float(order_response.get('price', current_price))
                    pnl = self._calculate_pnl(trade, exit_price)
                    pnl_percentage = self._calculate_pnl_percentage(trade, exit_price)

                    # Обновление сделки в базе данных
                    updated_trade = update_trade(
                        self.db,
                        trade.id,
                        {
                            'exit_price': exit_price,
                            'exit_time': datetime.now(),
                            'pnl': pnl,
                            'pnl_percentage': pnl_percentage,
                            'status': 'CLOSED',
                            'notes': f"{trade.notes}\nClosed: {close_reason}. Order ID: {order_response.get('orderId')}"
                        }
                    )

                    closed_trades.append(updated_trade)
                    logger.info(f"Trade {trade.id} closed with P&L: {pnl} ({pnl_percentage:.2f}%)")

                except Exception as e:
                    logger.error(f"Error closing trade {trade.id}: {str(e)}")

        return closed_trades

    def _get_current_price(self, symbol: str) -> Optional[float]:
        """
        Получение текущей цены актива

        :param symbol: Символ торговой пары
        :return: Текущая цена или None в случае ошибки
        """
        try:
            # Здесь должен быть запрос к API биржи для получения текущей цены
            # Для примера используем заглушку
            endpoint = "/api/v1/ticker/price"
            params = {'symbol': symbol}
            response = self.exchange_service._make_request('GET', endpoint, params)
            return float(response.get('price', 0))
        except Exception as e:
            logger.error(f"Error getting current price for {symbol}: {str(e)}")
            return None

    def _calculate_pnl(self, trade: Trade, exit_price: float) -> float:
        """
        Расчет прибыли/убытка для сделки

        :param trade: Объект сделки
        :param exit_price: Цена выхода
        :return: Прибыль/убыток в абсолютном выражении
        """
        signal_type = trade.signal.signal_type

        if signal_type == 'BUY':
            return (exit_price - trade.entry_price) * trade.volume
        elif signal_type == 'SELL':
            return (trade.entry_price - exit_price) * trade.volume
        else:
            return 0

    def _calculate_pnl_percentage(self, trade: Trade, exit_price: float) -> float:
        """
        Расчет процента прибыли/убытка для сделки

        :param trade: Объект сделки
        :param exit_price: Цена выхода
        :return: Процент прибыли/убытка
        """
        signal_type = trade.signal.signal_type

        if signal_type == 'BUY':
            return ((exit_price - trade.entry_price) / trade.entry_price) * 100
        elif signal_type == 'SELL':
            return ((trade.entry_price - exit_price) / trade.entry_price) * 100
        else:
            return 0

    def get_trading_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики по торговле

        :return: Словарь со статистикой
        """
        from app.db.crud import get_all_closed_trades

        # Получение закрытых сделок
        closed_trades = get_all_closed_trades(self.db)

        # Расчет статистики
        total_trades = len(closed_trades)
        profitable_trades = sum(1 for t in closed_trades if t.pnl and t.pnl > 0)
        losing_trades = sum(1 for t in closed_trades if t.pnl and t.pnl <= 0)

        win_rate = (profitable_trades / total_trades * 100) if total_trades > 0 else 0

        total_profit = sum(t.pnl for t in closed_trades if t.pnl and t.pnl > 0)
        total_loss = sum(t.pnl for t in closed_trades if t.pnl and t.pnl <= 0)

        profit_factor = abs(total_profit / total_loss) if total_loss != 0 else float('inf')

        avg_profit = total_profit / profitable_trades if profitable_trades > 0 else 0
        avg_loss = total_loss / losing_trades if losing_trades > 0 else 0

        # Расчет максимальной просадки
        # Для простоты используем упрощенный алгоритм
        cumulative_pnl = 0
        peak = 0
        max_drawdown = 0

        for trade in sorted(closed_trades, key=lambda t: t.exit_time or datetime.min):
            if trade.pnl:
                cumulative_pnl += trade.pnl
                if cumulative_pnl > peak:
                    peak = cumulative_pnl
                else:
                    drawdown = peak - cumulative_pnl
                    if drawdown > max_drawdown:
                        max_drawdown = drawdown

        return {
            'total_trades': total_trades,
            'profitable_trades': profitable_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'total_loss': total_loss,
            'profit_factor': profit_factor,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'max_drawdown': max_drawdown,
            'risk_reward_ratio': abs(avg_profit / avg_loss) if avg_loss != 0 else float('inf')
        }
```

### 3. Настройка конфигурации и переменных окружения (`app/core/config.py`)

Добавить настройки для работы с API биржи и демо-счетом:

```python
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Существующие настройки
    # ...

    # Настройки для BingX API
    BINGX_API_KEY: str = os.getenv("BINGX_API_KEY", "")
    BINGX_API_SECRET: str = os.getenv("BINGX_API_SECRET", "")
    USE_DEMO_ACCOUNT: bool = os.getenv("USE_DEMO_ACCOUNT", "True").lower() in ("true", "1", "t")

    # Настройки для торговли
    DEFAULT_RISK_PERCENTAGE: float = float(os.getenv("DEFAULT_RISK_PERCENTAGE", "1.0"))
    MAX_OPEN_POSITIONS: int = int(os.getenv("MAX_OPEN_POSITIONS", "5"))

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

### 4. API эндпоинты для управления торговлей (`app/api/endpoints/trading.py`)

Создать эндпоинты для управления торговлей:

```python
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Trade
from app.db.crud import get_signal_by_id, get_trade_by_id, get_trades_by_signal
from app.services.trading_service import TradingService
from app.schemas.trade import TradeCreate, TradeRead, TradeList
from app.schemas.signal import SignalRead
from app.core.config import settings

router = APIRouter()

@router.post("/signals/{signal_id}/execute", response_model=TradeRead)
def execute_signal_trade(
    signal_id: int,
    risk_percentage: float = settings.DEFAULT_RISK_PERCENTAGE,
    db: Session = Depends(get_db)
):
    """
    Выполнить торговлю на основе сигнала
    """
    # Проверка существования сигнала
    signal = get_signal_by_id(db, signal_id)
    if not signal:
        raise HTTPException(status_code=404, detail=f"Signal with ID {signal_id} not found")

    # Создание сервиса для торговли
    trading_service = TradingService(db)

    # Выполнение торговли
    trade = trading_service.process_signal(signal_id, risk_percentage)
    if not trade:
        raise HTTPException(status_code=400, detail="Failed to execute trade")

    return trade

@router.get("/trades/open", response_model=TradeList)
def get_open_trades(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Получить список открытых сделок
    """
    from app.db.crud import get_open_trades

    trades = get_open_trades(db, skip=skip, limit=limit)
    total = len(trades)  # В реальном приложении нужно использовать отдельный запрос для подсчета

    return {
        "items": trades,
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "size": limit,
        "pages": (total + limit - 1) // limit if limit > 0 else 1
    }

@router.post("/trades/check-and-close", response_model=List[TradeRead])
def check_and_close_trades(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Проверить открытые сделки и закрыть при необходимости
    """
    # Создание сервиса для торговли
    trading_service = TradingService(db)

    # Запуск проверки в фоновом режиме
    background_tasks.add_task(trading_service.check_and_close_trades)

    return {"message": "Trade check started in background"}

@router.get("/trades/statistics", response_model=Dict[str, Any])
def get_trading_statistics(db: Session = Depends(get_db)):
    """
    Получить статистику по торговле
    """
    trading_service = TradingService(db)
    return trading_service.get_trading_statistics()

@router.get("/account/balance", response_model=Dict[str, float])
def get_account_balance(db: Session = Depends(get_db)):
    """
    Получить баланс аккаунта
    """
    from app.services.exchange_service import BingXExchangeService

    exchange_service = BingXExchangeService(is_demo=settings.USE_DEMO_ACCOUNT)
    return exchange_service.get_account_balance()

@router.get("/account/positions", response_model=List[Dict[str, Any]])
def get_open_positions(db: Session = Depends(get_db)):
    """
    Получить открытые позиции на бирже
    """
    from app.services.exchange_service import BingXExchangeService

    exchange_service = BingXExchangeService(is_demo=settings.USE_DEMO_ACCOUNT)
    return exchange_service.get_open_positions()
```

### 5. Обновление схем Pydantic для сделок (`app/schemas/trade.py`)

Обновить или создать схемы для работы с торговыми сделками:

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.signal import SignalRead

class TradeBase(BaseModel):
    signal_id: int
    entry_price: float
    volume: float
    status: str = Field(..., description="Status of the trade: OPEN, CLOSED, CANCELLED")

    class Config:
        orm_mode = True

class TradeCreate(TradeBase):
    entry_time: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None

class TradeRead(TradeBase):
    id: int
    entry_time: datetime
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_percentage: Optional[float] = None
    notes: Optional[str] = None

    class Config:
        orm_mode = True

class TradeDetailRead(TradeRead):
    signal: SignalRead

    class Config:
        orm_mode = True

class TradeList(BaseModel):
    items: List[TradeRead]
    total: int
    page: int
    size: int
    pages: int
```

### 6. Обновление маршрутов API (`app/api/api.py`)

Добавить новые эндпоинты в маршруты API:

```python
from fastapi import APIRouter
from app.api.endpoints import signals, users, news, trading

api_router = APIRouter()
api_router.include_router(signals.router, prefix="/signals", tags=["signals"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(trading.router, prefix="/trading", tags=["trading"])
```

### 7. Создание фоновой задачи для проверки сделок (`app/services/scheduler.py`)

Обновить планировщик задач для периодической проверки открытых сделок:

```python
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.db.session import SessionLocal
from app.services.trading_service import TradingService

logger = logging.getLogger(__name__)

def check_and_close_trades_job():
    """
    Фоновая задача для проверки открытых сделок и закрытия при необходимости
    """
    logger.info("Running scheduled job: check_and_close_trades")

    db = SessionLocal()
    try:
        trading_service = TradingService(db)
        closed_trades = trading_service.check_and_close_trades()
        logger.info(f"Closed {len(closed_trades)} trades")
    except Exception as e:
        logger.error(f"Error in check_and_close_trades_job: {str(e)}")
    finally:
        db.close()

def setup_scheduler():
    """
    Настройка планировщика задач
    """
    scheduler = BackgroundScheduler()

    # Добавление задачи для проверки сделок каждые 5 минут
    scheduler.add_job(
        check_and_close_trades_job,
        trigger=IntervalTrigger(minutes=5),
        id='check_and_close_trades',
        replace_existing=True
    )

    # Запуск планировщика
    scheduler.start()
    logger.info("Scheduler started")

    return scheduler
```

### 8. Обновление файла `.env.example`

Добавить примеры переменных окружения для работы с API биржи:

```
# BingX API Settings
BINGX_API_KEY=your_api_key_here
BINGX_API_SECRET=your_api_secret_here
USE_DEMO_ACCOUNT=True

# Trading Settings
DEFAULT_RISK_PERCENTAGE=1.0
MAX_OPEN_POSITIONS=5
```

## Рекомендации по тестированию и переходу на реальный счет

### 1. Тестирование на демо-счете

Перед переходом на реальный счет необходимо провести тщательное тестирование на демо-счете:

1. **Создание демо-счета на BingX**:

   - Зарегистрируйтесь на BingX
   - Создайте демо-счет в разделе "Демо-торговля"
   - Получите API-ключи для демо-счета

2. **Настройка переменных окружения**:

   - Создайте файл `.env` на основе `.env.example`
   - Добавьте API-ключи для демо-счета
   - Установите `USE_DEMO_ACCOUNT=True`

3. **Тестирование базовых функций**:

   - Получение баланса и открытых позиций
   - Размещение и отмена ордеров
   - Получение истории сделок

4. **Тестирование автоматической торговли**:

   - Генерация сигналов
   - Выполнение торговли на основе сигналов
   - Закрытие позиций при достижении целевой цены или стоп-лосса

5. **Мониторинг и анализ результатов**:
   - Отслеживание успешности сигналов
   - Анализ статистики торговли
   - Корректировка параметров стратегии при необходимости

### 2. Переход на реальный счет

После успешного тестирования на демо-счете можно переходить на реальный счет:

1. **Создание реального счета на BingX**:

   - Пополните реальный счет на BingX
   - Получите API-ключи для реального счета
   - **ВАЖНО**: Установите ограничения на API-ключи (только торговля, без вывода средств)

2. **Обновление переменных окружения**:

   - Обновите API-ключи в файле `.env`
   - Установите `USE_DEMO_ACCOUNT=False`
   - Установите консервативные значения для `DEFAULT_RISK_PERCENTAGE` (например, 0.5%)

3. **Постепенное увеличение объема торговли**:

   - Начните с минимальных объемов
   - Постепенно увеличивайте объемы по мере подтверждения эффективности стратегии
   - Регулярно анализируйте результаты и корректируйте параметры

4. **Мониторинг и безопасность**:
   - Настройте уведомления о выполнении сделок
   - Регулярно проверяйте журналы и статистику
   - Имейте механизм экстренной остановки торговли в случае проблем

### 3. Рекомендации по безопасности

1. **Защита API-ключей**:

   - Никогда не храните API-ключи в репозитории кода
   - Используйте переменные окружения или защищенное хранилище секретов
   - Регулярно обновляйте API-ключи

2. **Ограничения на API-ключи**:

   - Ограничьте IP-адреса, с которых можно использовать API-ключи
   - Установите ограничения на функциональность (только торговля, без вывода средств)
   - Установите лимиты на объемы торговли

3. **Мониторинг и логирование**:
   - Настройте подробное логирование всех операций
   - Регулярно проверяйте журналы на наличие ошибок или подозрительной активности
   - Настройте уведомления о критических событиях

## Пример использования

### 1. Настройка переменных окружения

```bash
# Создание файла .env
cp .env.example .env

# Редактирование файла .env
nano .env
```

### 2. Запуск приложения

```bash
# Запуск приложения
cd /path/to/project
uvicorn app.main:app --reload
```

### 3. Тестирование API эндпоинтов

```bash
# Получение баланса аккаунта
curl -X GET "http://localhost:8000/api/v1/trading/account/balance"

# Выполнение торговли на основе сигнала
curl -X POST "http://localhost:8000/api/v1/trading/signals/1/execute?risk_percentage=0.5"

# Получение открытых сделок
curl -X GET "http://localhost:8000/api/v1/trading/trades/open"

# Получение статистики по торговле
curl -X GET "http://localhost:8000/api/v1/trading/trades/statistics"
```

Пожалуйста, реализуйте интеграцию с биржей BingX для торговли на демо-счете в AI трейдинг-боте, следуя приведенным выше рекомендациям и примерам кода.
