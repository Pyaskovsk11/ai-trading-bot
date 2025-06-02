import requests
import hmac
import hashlib
import time
from typing import Dict, List, Optional
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class BingXService:
    def __init__(self):
        self.api_key = os.getenv('BINGX_API_KEY', '')
        self.secret_key = os.getenv('BINGX_SECRET_KEY', '')
        self.base_url = "https://open-api.bingx.com"
        
    def _generate_signature(self, query_string: str) -> str:
        """Генерация подписи для BingX API"""
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, endpoint: str, params: Dict = None, method: str = "GET") -> Dict:
        """Выполнение запроса к BingX API"""
        if not self.api_key or not self.secret_key:
            logger.warning("BingX API ключи не настроены, используем моковые данные")
            return {}
            
        try:
            timestamp = int(time.time() * 1000)
            params = params or {}
            params['timestamp'] = timestamp
            
            # Создаем строку запроса
            query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
            signature = self._generate_signature(query_string)
            
            headers = {
                'X-BX-APIKEY': self.api_key,
                'Content-Type': 'application/json'
            }
            
            url = f"{self.base_url}{endpoint}?{query_string}&signature={signature}"
            
            response = requests.request(method, url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0:
                    return data.get('data', {})
                else:
                    logger.error(f"BingX API error: {data}")
                    return {}
            else:
                logger.error(f"HTTP error: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Ошибка запроса к BingX API: {e}")
            return {}
    
    def get_account_balance(self) -> Dict:
        """Получение баланса аккаунта"""
        endpoint = "/openApi/spot/v1/account/balance"
        balance_data = self._make_request(endpoint)
        
        if not balance_data:
            # Возвращаем моковые данные если API недоступен
            return {
                "total_balance_usd": 15420.50,
                "total_balance_btc": 0.342,
                "balances": [
                    {"asset": "USDT", "free": "1170.50", "locked": "0.00"},
                    {"asset": "BTC", "free": "0.25", "locked": "0.00"},
                    {"asset": "ETH", "free": "1.2", "locked": "0.00"},
                    {"asset": "BNB", "free": "3.5", "locked": "0.00"}
                ]
            }
        
        # Обработка реальных данных
        total_usd = 0
        balances = []
        
        for balance in balance_data.get('balances', []):
            asset = balance.get('asset')
            free = float(balance.get('free', 0))
            locked = float(balance.get('locked', 0))
            
            if free > 0 or locked > 0:
                balances.append({
                    "asset": asset,
                    "free": str(free),
                    "locked": str(locked)
                })
                
                # Конвертируем в USD (упрощенно)
                if asset == 'USDT':
                    total_usd += free + locked
                elif asset == 'BTC':
                    total_usd += (free + locked) * 45000  # Примерная цена BTC
                elif asset == 'ETH':
                    total_usd += (free + locked) * 2500   # Примерная цена ETH
        
        return {
            "total_balance_usd": round(total_usd, 2),
            "total_balance_btc": round(total_usd / 45000, 6),
            "balances": balances
        }
    
    def get_portfolio_performance(self) -> Dict:
        """Получение данных производительности портфеля"""
        # В реальном проекте здесь был бы запрос к API для получения истории
        # Пока возвращаем моковые данные
        return {
            "daily_pnl": 234.80,
            "daily_pnl_percent": 1.55,
            "weekly_pnl": 1250.30,
            "weekly_pnl_percent": 8.75,
            "monthly_pnl": 2100.50,
            "monthly_pnl_percent": 15.80,
            "total_pnl": 3420.50,
            "total_pnl_percent": 28.50
        }
    
    def get_open_orders(self) -> List[Dict]:
        """Получение открытых ордеров"""
        endpoint = "/openApi/spot/v1/trade/openOrders"
        orders_data = self._make_request(endpoint)
        
        if not orders_data:
            return []
        
        return orders_data.get('orders', [])
    
    def get_trade_history(self, symbol: str = None, limit: int = 100) -> List[Dict]:
        """Получение истории торгов"""
        endpoint = "/openApi/spot/v1/trade/myTrades"
        params = {"limit": limit}
        if symbol:
            params["symbol"] = symbol.replace('/', '-')
            
        trades_data = self._make_request(endpoint, params)
        
        if not trades_data:
            return []
        
        return trades_data.get('trades', [])

# Создаем глобальный экземпляр сервиса
bingx_service = BingXService() 