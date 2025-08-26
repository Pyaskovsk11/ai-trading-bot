from fastapi import APIRouter, Query
from typing import Dict, Any
from datetime import datetime, timedelta
import pandas as pd

from app.services.bingx_historical_data_service import bingx_historical_service
from backend.app.services.pattern_detection_service import pattern_detection_service

router = APIRouter()

@router.get("/scan")
async def scan_patterns(symbol: str = Query(...), timeframe: str = Query("1h"), days: int = Query(14)) -> Dict[str, Any]:
	end_date = datetime.now()
	start_date = end_date - timedelta(days=int(days))
	# Получаем данные
	data = await bingx_historical_service.get_multiple_symbols_data([symbol], start_date, end_date, timeframe)
	df = data.get(symbol)
	if df is None or len(df) == 0:
		return {"status": "error", "message": "no data"}
	# Приводим индекс
	if not isinstance(df.index, pd.DatetimeIndex) and 'timestamp' in df.columns:
		df = df.copy(); df['timestamp'] = pd.to_datetime(df['timestamp']); df.set_index('timestamp', inplace=True)
	# Запускаем сканирование
	patterns = pattern_detection_service.scan_patterns(df)
	whales = pattern_detection_service.detect_whale_activity(df)
	return {"status": "ok", "symbol": symbol, "timeframe": timeframe, "patterns": patterns, "whales": whales}
