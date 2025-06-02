import logging
from sqlalchemy.orm import Session
from app.services.data_collection_service import fetch_bingx_prices, fetch_arkham_data, fetch_lookonchain_data
from app.services.technical_analysis_service import analyze_ohlcv
from app.services.rag_analysis_service import analyze_news_with_hector_rag
from app.services.xai_service import create_and_save_xai_explanation
from app.services.risk_management_service import apply_risk_management
from app.db.models import Signal
from datetime import datetime, timedelta
from app.services.adaptive_asset_selector import AdaptiveAssetSelector
from app.services.btcd_analyzer import BTCDominanceAnalyzer
from app.data_providers.btcd_data_provider import MockBTCDDataProvider
from app.core.event_bus import EVENT_BUS, MarketRegimeChangedEvent
import asyncio

logger = logging.getLogger(__name__)

class SignalGenerationService:
    def __init__(self, db: Session):
        self.db = db
        self.asset_selector = AdaptiveAssetSelector()
        self.asset_pool = []
        EVENT_BUS.subscribe(MarketRegimeChangedEvent, self.on_market_regime_changed)

    async def on_market_regime_changed(self, event):
        logger.info(f"[Event] Market regime changed: {event.payload}")
        self.asset_pool = self.asset_selector.get_asset_pool(event.payload)
        # (опционально) инициировать генерацию новых сигналов:
        await self.generate_signals_for_asset_pool()

    async def generate_signals_for_asset_pool(self):
        signals = []
        for asset_pair in self.asset_pool:
            signal = generate_signal_for_asset(asset_pair, self.db)
            if signal:
                signals.append(signal)
        logger.info(f"[Event] Signals generated for new asset pool: {self.asset_pool}")
        return signals

# --- Пример публикации события смены режима рынка ---
async def detect_and_publish_market_regime():
    data_provider = MockBTCDDataProvider()
    btcd_analyzer = BTCDominanceAnalyzer(data_provider)
    btcd_analyzer.update_data()
    btcd_analyzer.calculate_technical_indicators()
    btcd_analyzer.detect_patterns()
    btcd_analyzer.identify_support_resistance()
    market_regime = btcd_analyzer.get_market_regime()
    await EVENT_BUS.publish(MarketRegimeChangedEvent(name="market_regime_changed", payload=market_regime))

# --- Оригинальная функция для генерации сигналов по рынку ---
def generate_signals_for_market_regime(db: Session):
    """
    Генерирует сигналы только по релевантным активам в зависимости от режима рынка (BTC.D, alt season и др.)
    """
    # 1. Инициализация анализатора и селектора
    data_provider = MockBTCDDataProvider()
    btcd_analyzer = BTCDominanceAnalyzer(data_provider)
    asset_selector = AdaptiveAssetSelector()
    # 2. Получение режима рынка и пула активов
    btcd_analyzer.update_data()
    btcd_analyzer.calculate_technical_indicators()
    btcd_analyzer.detect_patterns()
    btcd_analyzer.identify_support_resistance()
    market_regime = btcd_analyzer.get_market_regime()
    asset_pool = asset_selector.get_asset_pool(market_regime)
    logger.info(f"Market regime: {market_regime}, asset pool: {asset_pool}")
    # 3. Генерация сигналов только по asset_pool
    signals = []
    for asset_pair in asset_pool:
        signal = generate_signal_for_asset(asset_pair, db)
        if signal:
            signals.append(signal)
    return signals

def generate_signal_for_asset(asset_pair: str, db: Session) -> Signal:
    """
    Генерирует торговый сигнал для указанной пары, используя TA, RAG, Smart Money, XAI, Risk Management.
    """
    try:
        # 1. Получить ценовые данные
        ohlcv = fetch_bingx_prices(asset_pair)
        if not ohlcv or 'close' not in ohlcv or not ohlcv['close']:
            logger.error(f'No OHLCV data for {asset_pair}')
            return None
        ta = analyze_ohlcv(ohlcv)
    except Exception as e:
        logger.error(f'Error fetching or analyzing OHLCV for {asset_pair}: {e}')
        return None

    try:
        # 2. Получить анализ новостей
        news_analysis = analyze_news_with_hector_rag(f"Новости по {asset_pair}")
    except Exception as e:
        logger.error(f'Error analyzing news for {asset_pair}: {e}')
        news_analysis = {"sentiment_score": 0}

    try:
        # 3. Получить данные Smart Money
        smart_money = fetch_arkham_data(asset_pair)
    except Exception as e:
        logger.error(f'Error fetching smart money data for {asset_pair}: {e}')
        smart_money = {"smart_money_inflow": 0, "smart_money_outflow": 0}

    # 4. Простая логика генерации сигнала
    signal_type = "HOLD"
    if ta['rsi'] is not None and ta['rsi'] < 30 and news_analysis['sentiment_score'] > 0:
        signal_type = "BUY"
    elif ta['rsi'] is not None and ta['rsi'] > 70 and news_analysis['sentiment_score'] < 0:
        signal_type = "SELL"

    # 5. Применить Risk Management
    balance = 1000  # TODO: получить реальный баланс пользователя
    risk_per_trade = 0.01  # 1% риска на сделку
    stop_loss_pct = 0.02  # 2% стоп-лосс
    direction = "LONG" if signal_type == "BUY" else ("SHORT" if signal_type == "SELL" else "LONG")
    risk = apply_risk_management(balance, ohlcv['close'][-1], risk_per_trade, stop_loss_pct, direction)

    # 6. Применить XAI
    signal_factors = {
        "rsi": ta['rsi'],
        "macd": ta['macd'],
        "ema": ta['ema'],
        "candle_pattern": ta['candle_pattern'],
        "news_sentiment": news_analysis['sentiment_score'],
        "asset_pair": asset_pair,
        "signal_type": signal_type,
        "smart_money": smart_money['smart_money_inflow'] - smart_money['smart_money_outflow']
    }
    xai_explanation_id = create_and_save_xai_explanation(signal_factors, db)

    # 7. Сохранить сигнал
    signal = Signal(
        asset_pair=asset_pair,
        signal_type=signal_type,
        confidence_score=0.8,
        price_at_signal=ohlcv['close'][-1],
        target_price=ohlcv['close'][-1] * 1.05 if signal_type == "BUY" else ohlcv['close'][-1] * 0.95,
        stop_loss=risk['stop_loss'],
        time_frame="1h",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=4),
        status="ACTIVE",
        technical_indicators=ta,
        xai_explanation_id=xai_explanation_id,
        smart_money_influence=signal_factors['smart_money'],
        volatility_estimate=None
    )
    db.add(signal)
    db.commit()
    db.refresh(signal)
    logger.info(f"Signal generated for {asset_pair}: {signal_type}, position_size={risk['position_size']}, stop_loss={risk['stop_loss']}")
    return signal 