from typing import Dict, List, Any
from datetime import datetime
import pandas as pd

class PatternDetectionService:
	"""Сервис распознавания паттернов и активности крупных игроков"""
	popular_patterns = [
		'head_and_shoulders', 'inverse_head_and_shoulders', 'double_top', 'double_bottom',
		'ascending_triangle', 'descending_triangle', 'symmetrical_triangle',
		'bull_flag', 'bear_flag', 'cup_and_handle', 'wedge_up', 'wedge_down'
	]

	def scan_patterns(self, ohlcv: pd.DataFrame) -> List[Dict[str, Any]]:
		results: List[Dict[str, Any]] = []
		if ohlcv is None or len(ohlcv) < 50:
			return results
		# Заглушки: возвращаем вероятности и ключевые точки; реальная логика может использовать TA-Lib/np
		last_close = float(ohlcv['close'].iloc[-1])
		for name in self.popular_patterns:
			results.append({
				'name': name,
				'confidence': 0.0,
				'key_points': [],
				'active': False
			})
		return results

	def detect_whale_activity(self, ohlcv: pd.DataFrame) -> Dict[str, Any]:
		"""Простая эвристика: всплески объёма, крупные свечи, последовательные крупные принты."""
		if ohlcv is None or len(ohlcv) < 50:
			return {'whale_score': 0.0, 'signals': []}
		signals: List[str] = []
		vol = ohlcv['volume']
		vol_sma = vol.rolling(20).mean()
		vr = float(vol.iloc[-1] / max(1e-9, vol_sma.iloc[-1]))
		c = ohlcv['close']
		chg = float((c.iloc[-1] - c.iloc[-2]) / max(1e-9, c.iloc[-2]))
		whale_score = 0.0
		if vr >= 2.5:
			whale_score += 0.5; signals.append(f'volume_spike_{vr:.1f}x')
		if abs(chg) >= 0.02:
			whale_score += 0.3; signals.append(f'large_move_{chg*100:.1f}%')
		return {'whale_score': min(1.0, whale_score), 'signals': signals, 'timestamp': datetime.now().isoformat()}

pattern_detection_service = PatternDetectionService()
