from typing import Dict

def interpret_sentiment(score: float) -> str:
    if score is None:
        return "нет данных о новостном фоне"
    if score > 0.3:
        return "положительный новостной фон"
    elif score < -0.3:
        return "отрицательный новостной фон"
    else:
        return "нейтральный новостной фон"

XAI_TEMPLATES = {
    "default": (
        "Сигнал {signal_type} по {asset} был сгенерирован на основе следующих факторов: "
        "{factors}."
    )
}

def generate_xai_explanation(signal_data: Dict) -> str:
    """
    Генерирует XAI-объяснение для торгового сигнала на основе шаблона.
    """
    rsi = signal_data.get("rsi")
    macd = signal_data.get("macd")
    ema = signal_data.get("ema")
    candle = signal_data.get("candle_pattern")
    news_sentiment = signal_data.get("news_sentiment")
    asset = signal_data.get("asset_pair", "актив")
    signal_type = signal_data.get("signal_type", "СИГНАЛ")
    smart_money = signal_data.get("smart_money")

    factors = []
    if rsi is not None:
        factors.append(f"RSI={rsi}")
    if macd is not None:
        factors.append(f"MACD={macd}")
    if ema is not None:
        factors.append(f"EMA={ema}")
    if candle:
        factors.append(f"Свечная модель: {candle}")
    if news_sentiment is not None:
        factors.append(interpret_sentiment(news_sentiment))
    if smart_money is not None:
        factors.append(f"Smart Money: {smart_money}")
    if not factors:
        factors.append("Недостаточно данных для объяснения.")

    template = XAI_TEMPLATES["default"]
    explanation = template.format(
        signal_type=signal_type,
        asset=asset,
        factors=", ".join(factors)
    )
    return explanation 