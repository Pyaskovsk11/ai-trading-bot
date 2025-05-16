import logging
import os
from typing import Dict, Any
import requests

logger = logging.getLogger(__name__)

BINGX_API_URL = os.getenv("BINGX_API_URL", "https://api.bingx.com/ohlcv")
BINGX_API_KEY = os.getenv("BINGX_API_KEY")
ARKHAM_API_URL = os.getenv("ARKHAM_API_URL", "https://api.arkham.com/data")
ARKHAM_API_KEY = os.getenv("ARKHAM_API_KEY")
LOOKONCHAIN_API_URL = os.getenv("LOOKONCHAIN_API_URL", "https://api.lookonchain.com/data")
LOOKONCHAIN_API_KEY = os.getenv("LOOKONCHAIN_API_KEY")

TIMEOUT = 10


def fetch_bingx_prices(asset_pair: str) -> Dict[str, Any]:
    """
    Получить OHLCV-данные для указанной пары с BingX.
    """
    try:
        headers = {"X-API-KEY": BINGX_API_KEY} if BINGX_API_KEY else {}
        params = {"symbol": asset_pair, "interval": "1h", "limit": 100}
        resp = requests.get(BINGX_API_URL, headers=headers, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        # Преобразование данных под формат OHLCV
        return {
            'open': [float(c[1]) for c in data['data']],
            'high': [float(c[2]) for c in data['data']],
            'low': [float(c[3]) for c in data['data']],
            'close': [float(c[4]) for c in data['data']],
            'volume': [float(c[5]) for c in data['data']]
        }
    except Exception as e:
        logger.error(f"Error fetching BingX prices: {e}")
        return {'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}


def fetch_arkham_data(asset_pair: str) -> Dict[str, Any]:
    """
    Получить данные Arkham.
    """
    try:
        headers = {"Authorization": f"Bearer {ARKHAM_API_KEY}"} if ARKHAM_API_KEY else {}
        params = {"symbol": asset_pair}
        resp = requests.get(ARKHAM_API_URL, headers=headers, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return {
            'smart_money_inflow': data.get('smart_money_inflow', 0),
            'smart_money_outflow': data.get('smart_money_outflow', 0)
        }
    except Exception as e:
        logger.error(f"Error fetching Arkham data: {e}")
        return {'smart_money_inflow': 0, 'smart_money_outflow': 0}


def fetch_lookonchain_data(asset_pair: str) -> Dict[str, Any]:
    """
    Получить данные Lookonchain.
    """
    try:
        headers = {"Authorization": f"Bearer {LOOKONCHAIN_API_KEY}"} if LOOKONCHAIN_API_KEY else {}
        params = {"symbol": asset_pair}
        resp = requests.get(LOOKONCHAIN_API_URL, headers=headers, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return {
            'whale_alerts': data.get('whale_alerts', 0),
            'last_alert_type': data.get('last_alert_type')
        }
    except Exception as e:
        logger.error(f"Error fetching Lookonchain data: {e}")
        return {'whale_alerts': 0, 'last_alert_type': None} 