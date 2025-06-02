from typing import Dict, List, Optional, Union, Any
import time
import hmac
import hashlib
import requests
import logging
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)

class BingXExchangeService:
    """Сервис для взаимодействия с API биржи BingX"""
    
    def __init__(self, is_demo: bool = True):
        """
        Инициализация сервиса
        
        :param is_demo: Использовать демо-счет (True) или реальный счет (False)
        """
        self.api_key = settings.BINGX_API_KEY
        self.api_secret = settings.BINGX_API_SECRET
        self.base_url = "https://open-api.bingx.com"
        self.is_demo = is_demo
        
        logger.info(f"Initialized BingX Exchange Service (Demo: {is_demo})")
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """
        Генерация подписи для запросов к API
        
        :param params: Параметры запроса
        :return: Подпись в виде строки
        """
        query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Выполнение запроса к API BingX
        
        :param method: HTTP метод (GET, POST, DELETE)
        :param endpoint: Эндпоинт API
        :param params: Параметры запроса
        :return: Ответ API в виде словаря
        """
        url = f"{self.base_url}{endpoint}"
        timestamp = int(time.time() * 1000)
        
        if params is None:
            params = {}
        
        params.update({
            "apiKey": self.api_key,
            "timestamp": timestamp
        })
        
        params["signature"] = self._generate_signature(params)
        
        try:
            response = requests.request(method, url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error making request to BingX API: {str(e)}")
            raise
    
    def get_account_balance(self) -> Dict[str, Any]:
        """
        Получение баланса аккаунта
        
        :return: Словарь с балансами по валютам
        """
        return self._make_request("GET", "/api/v1/account/balance")
    
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
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": quantity
        }
        
        logger.info(f"Placing market order: {side} {quantity} {symbol}")
        response = self._make_request("POST", "/api/v1/order", params)
        
        logger.info(f"Market order placed: {response}")
        return response

    def get_open_orders(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Получает список открытых ордеров.
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._make_request("GET", "/api/v1/openOrders", params)

    def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Отменяет ордер.
        """
        params = {
            "orderId": order_id,
            "symbol": symbol
        }
        return self._make_request("DELETE", "/api/v1/order", params) 