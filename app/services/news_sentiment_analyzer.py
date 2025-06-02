"""
News Sentiment Analyzer - Анализ новостей и сентимента для экстремальной торговли
Цель: Обнаружение экстремальных движений на основе новостного фона
"""

import logging
import asyncio
import aiohttp
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class SentimentStrength(Enum):
    """Сила сентимента"""
    EXTREME_NEGATIVE = "extreme_negative"  # -0.8 to -1.0
    STRONG_NEGATIVE = "strong_negative"    # -0.5 to -0.8
    NEGATIVE = "negative"                  # -0.2 to -0.5
    NEUTRAL = "neutral"                    # -0.2 to 0.2
    POSITIVE = "positive"                  # 0.2 to 0.5
    STRONG_POSITIVE = "strong_positive"    # 0.5 to 0.8
    EXTREME_POSITIVE = "extreme_positive"  # 0.8 to 1.0

@dataclass
class NewsEvent:
    """Новостное событие"""
    title: str
    content: str
    source: str
    timestamp: datetime
    symbols_mentioned: List[str]
    sentiment_score: float      # -1.0 to 1.0
    sentiment_strength: SentimentStrength
    impact_score: float         # 0.0 to 1.0 (влияние на рынок)
    keywords: List[str]
    category: str              # "regulation", "adoption", "technical", etc.
    urgency: float             # 0.0 to 1.0 (срочность)

@dataclass
class MarketSentiment:
    """Общий рыночный сентимент"""
    overall_score: float        # -1.0 to 1.0
    crypto_score: float         # -1.0 to 1.0
    symbol_scores: Dict[str, float]  # Сентимент по символам
    trending_topics: List[str]
    breaking_news_count: int
    sentiment_momentum: float   # Изменение сентимента
    confidence: float          # Уверенность в анализе

class NewsSentimentAnalyzer:
    """
    Анализатор новостей и сентимента для экстремальной торговли
    """
    
    def __init__(self):
        self.positive_keywords = self._load_positive_keywords()
        self.negative_keywords = self._load_negative_keywords()
        self.extreme_keywords = self._load_extreme_keywords()
        self.crypto_symbols = self._load_crypto_symbols()
        self.news_sources = self._get_news_sources()
        
        # Кэш для избежания повторных запросов
        self.sentiment_cache = {}
        self.cache_duration = 300  # 5 минут
        
        logger.info("NewsSentimentAnalyzer инициализирован")
    
    def _load_positive_keywords(self) -> List[str]:
        """Загрузка позитивных ключевых слов"""
        return [
            # Общие позитивные
            "bullish", "moon", "pump", "surge", "rally", "breakout", "adoption",
            "institutional", "investment", "partnership", "integration", "upgrade",
            "launch", "success", "profit", "gain", "rise", "increase", "growth",
            
            # Криптоспецифичные
            "halving", "burn", "staking", "yield", "defi", "nft", "metaverse",
            "web3", "blockchain", "innovation", "breakthrough", "milestone",
            "all-time high", "ath", "golden cross", "accumulation",
            
            # Институциональные
            "etf approval", "regulation clarity", "legal tender", "mainstream",
            "wall street", "bank adoption", "payment", "treasury", "reserve"
        ]
    
    def _load_negative_keywords(self) -> List[str]:
        """Загрузка негативных ключевых слов"""
        return [
            # Общие негативные
            "bearish", "dump", "crash", "collapse", "plunge", "decline", "fall",
            "drop", "loss", "sell-off", "panic", "fear", "uncertainty", "risk",
            
            # Криптоспецифичные
            "hack", "exploit", "rug pull", "scam", "ponzi", "bubble", "ban",
            "regulation", "crackdown", "investigation", "lawsuit", "fine",
            "death cross", "capitulation", "liquidation", "margin call",
            
            # Технические проблемы
            "bug", "vulnerability", "attack", "breach", "outage", "downtime",
            "fork", "split", "controversy", "dispute", "delay", "postpone"
        ]
    
    def _load_extreme_keywords(self) -> Dict[str, float]:
        """Загрузка экстремальных ключевых слов с весами"""
        return {
            # Экстремально позитивные (0.8-1.0)
            "parabolic": 0.9,
            "explosive": 0.9,
            "historic": 0.8,
            "unprecedented": 0.8,
            "revolutionary": 0.8,
            "game-changer": 0.9,
            "massive adoption": 0.9,
            "institutional fomo": 0.9,
            
            # Экстремально негативные (-0.8 to -1.0)
            "catastrophic": -0.9,
            "devastating": -0.9,
            "apocalyptic": -0.8,
            "total collapse": -0.9,
            "market crash": -0.8,
            "black swan": -0.9,
            "systemic risk": -0.8,
            "contagion": -0.8
        }
    
    def _load_crypto_symbols(self) -> List[str]:
        """Загрузка криптовалютных символов"""
        return [
            "BTC", "BITCOIN", "ETH", "ETHEREUM", "BNB", "BINANCE",
            "ADA", "CARDANO", "SOL", "SOLANA", "XRP", "RIPPLE",
            "DOGE", "DOGECOIN", "AVAX", "AVALANCHE", "MATIC", "POLYGON",
            "DOT", "POLKADOT", "LINK", "CHAINLINK", "UNI", "UNISWAP"
        ]
    
    def _get_news_sources(self) -> List[Dict]:
        """Получение источников новостей"""
        return [
            {
                "name": "CoinDesk",
                "url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
                "weight": 0.9,
                "category": "mainstream"
            },
            {
                "name": "CoinTelegraph", 
                "url": "https://cointelegraph.com/rss",
                "weight": 0.8,
                "category": "crypto"
            },
            {
                "name": "Decrypt",
                "url": "https://decrypt.co/feed",
                "weight": 0.7,
                "category": "crypto"
            },
            {
                "name": "The Block",
                "url": "https://www.theblockcrypto.com/rss.xml",
                "weight": 0.9,
                "category": "institutional"
            }
        ]
    
    async def analyze_market_sentiment(self, symbols: List[str] = None) -> MarketSentiment:
        """Анализ общего рыночного сентимента"""
        try:
            # Получаем последние новости
            recent_news = await self._fetch_recent_news(hours=24)
            
            if not recent_news:
                return self._create_neutral_sentiment(symbols or [])
            
            # Анализируем каждую новость
            analyzed_news = []
            for news in recent_news:
                sentiment = await self._analyze_news_sentiment(news)
                if sentiment:
                    analyzed_news.append(sentiment)
            
            # Рассчитываем общий сентимент
            overall_sentiment = self._calculate_overall_sentiment(analyzed_news)
            
            # Анализируем сентимент по символам
            symbol_sentiments = {}
            if symbols:
                for symbol in symbols:
                    symbol_sentiments[symbol] = self._calculate_symbol_sentiment(
                        analyzed_news, symbol
                    )
            
            # Определяем трендовые топики
            trending_topics = self._extract_trending_topics(analyzed_news)
            
            # Подсчитываем экстренные новости
            breaking_news_count = len([n for n in analyzed_news if n.urgency > 0.7])
            
            # Рассчитываем моментум сентимента
            sentiment_momentum = await self._calculate_sentiment_momentum(analyzed_news)
            
            # Оценка уверенности
            confidence = min(1.0, len(analyzed_news) / 20.0)  # Больше новостей = больше уверенности
            
            market_sentiment = MarketSentiment(
                overall_score=overall_sentiment,
                crypto_score=self._calculate_crypto_sentiment(analyzed_news),
                symbol_scores=symbol_sentiments,
                trending_topics=trending_topics,
                breaking_news_count=breaking_news_count,
                sentiment_momentum=sentiment_momentum,
                confidence=confidence
            )
            
            logger.info(f"Рыночный сентимент: {overall_sentiment:.3f}, "
                       f"крипто: {market_sentiment.crypto_score:.3f}, "
                       f"экстренных новостей: {breaking_news_count}")
            
            return market_sentiment
            
        except Exception as e:
            logger.error(f"Ошибка анализа рыночного сентимента: {e}")
            return self._create_neutral_sentiment(symbols or [])
    
    async def _fetch_recent_news(self, hours: int = 24) -> List[Dict]:
        """Получение последних новостей"""
        try:
            all_news = []
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Симуляция получения новостей (в реальности - RSS/API)
            simulated_news = self._generate_simulated_news(hours)
            
            for news in simulated_news:
                if news['timestamp'] >= cutoff_time:
                    all_news.append(news)
            
            # Сортируем по времени (новые сначала)
            all_news.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return all_news[:50]  # Максимум 50 новостей
            
        except Exception as e:
            logger.error(f"Ошибка получения новостей: {e}")
            return []
    
    def _generate_simulated_news(self, hours: int) -> List[Dict]:
        """Генерация симулированных новостей для тестирования"""
        import random
        
        news_templates = [
            {
                "title": "Bitcoin Surges to New Weekly High Amid Institutional Interest",
                "content": "Bitcoin price rallied strongly today following reports of increased institutional adoption...",
                "sentiment_bias": 0.7,
                "symbols": ["BTC", "BITCOIN"]
            },
            {
                "title": "Ethereum Network Upgrade Shows Promising Results",
                "content": "The latest Ethereum upgrade has been successfully implemented, showing improved performance...",
                "sentiment_bias": 0.6,
                "symbols": ["ETH", "ETHEREUM"]
            },
            {
                "title": "Regulatory Uncertainty Weighs on Crypto Markets",
                "content": "Cryptocurrency markets faced pressure today amid ongoing regulatory uncertainty...",
                "sentiment_bias": -0.5,
                "symbols": ["BTC", "ETH", "CRYPTO"]
            },
            {
                "title": "Major Exchange Reports Security Breach",
                "content": "A significant cryptocurrency exchange reported a security incident affecting user funds...",
                "sentiment_bias": -0.8,
                "symbols": ["CRYPTO", "SECURITY"]
            },
            {
                "title": "DeFi Protocol Launches Revolutionary Feature",
                "content": "A leading DeFi protocol announced a groundbreaking new feature that could transform...",
                "sentiment_bias": 0.8,
                "symbols": ["DEFI", "ETH"]
            }
        ]
        
        simulated_news = []
        base_time = datetime.now()
        
        for i in range(hours * 2):  # 2 новости в час
            template = random.choice(news_templates)
            
            # Добавляем случайные вариации
            sentiment_variation = random.uniform(-0.2, 0.2)
            final_sentiment = max(-1.0, min(1.0, template["sentiment_bias"] + sentiment_variation))
            
            news = {
                "title": template["title"],
                "content": template["content"],
                "source": random.choice(["CoinDesk", "CoinTelegraph", "The Block"]),
                "timestamp": base_time - timedelta(minutes=i * 30),
                "symbols": template["symbols"],
                "base_sentiment": final_sentiment
            }
            
            simulated_news.append(news)
        
        return simulated_news
    
    async def _analyze_news_sentiment(self, news: Dict) -> Optional[NewsEvent]:
        """Анализ сентимента отдельной новости"""
        try:
            title = news.get("title", "")
            content = news.get("content", "")
            text = f"{title} {content}".lower()
            
            # Базовый анализ сентимента
            sentiment_score = self._calculate_text_sentiment(text)
            
            # Если есть базовый сентимент из симуляции, используем его
            if "base_sentiment" in news:
                sentiment_score = news["base_sentiment"]
            
            # Определяем силу сентимента
            sentiment_strength = self._classify_sentiment_strength(sentiment_score)
            
            # Рассчитываем влияние на рынок
            impact_score = self._calculate_impact_score(text, news.get("source", ""))
            
            # Извлекаем ключевые слова
            keywords = self._extract_keywords(text)
            
            # Определяем категорию
            category = self._classify_news_category(text)
            
            # Рассчитываем срочность
            urgency = self._calculate_urgency(text, news.get("timestamp", datetime.now()))
            
            # Находим упомянутые символы
            symbols_mentioned = self._extract_mentioned_symbols(text)
            
            news_event = NewsEvent(
                title=news.get("title", ""),
                content=news.get("content", ""),
                source=news.get("source", "unknown"),
                timestamp=news.get("timestamp", datetime.now()),
                symbols_mentioned=symbols_mentioned,
                sentiment_score=sentiment_score,
                sentiment_strength=sentiment_strength,
                impact_score=impact_score,
                keywords=keywords,
                category=category,
                urgency=urgency
            )
            
            return news_event
            
        except Exception as e:
            logger.error(f"Ошибка анализа новости: {e}")
            return None
    
    def _calculate_text_sentiment(self, text: str) -> float:
        """Расчет сентимента текста"""
        sentiment_score = 0.0
        word_count = 0
        
        words = re.findall(r'\b\w+\b', text.lower())
        
        for word in words:
            word_count += 1
            
            # Проверяем экстремальные ключевые слова
            for extreme_word, weight in self.extreme_keywords.items():
                if extreme_word in text:
                    sentiment_score += weight * 2  # Удвоенный вес для экстремальных
            
            # Проверяем позитивные слова
            if word in self.positive_keywords:
                sentiment_score += 0.1
            
            # Проверяем негативные слова
            if word in self.negative_keywords:
                sentiment_score -= 0.1
        
        # Нормализуем по количеству слов
        if word_count > 0:
            sentiment_score = sentiment_score / max(1, word_count / 10)
        
        # Ограничиваем диапазон
        return max(-1.0, min(1.0, sentiment_score))
    
    def _classify_sentiment_strength(self, score: float) -> SentimentStrength:
        """Классификация силы сентимента"""
        if score <= -0.8:
            return SentimentStrength.EXTREME_NEGATIVE
        elif score <= -0.5:
            return SentimentStrength.STRONG_NEGATIVE
        elif score <= -0.2:
            return SentimentStrength.NEGATIVE
        elif score < 0.2:
            return SentimentStrength.NEUTRAL
        elif score < 0.5:
            return SentimentStrength.POSITIVE
        elif score < 0.8:
            return SentimentStrength.STRONG_POSITIVE
        else:
            return SentimentStrength.EXTREME_POSITIVE
    
    def _calculate_impact_score(self, text: str, source: str) -> float:
        """Расчет влияния новости на рынок"""
        impact = 0.0
        
        # Вес источника
        source_weights = {
            "coindesk": 0.9,
            "the block": 0.9,
            "cointelegraph": 0.8,
            "decrypt": 0.7
        }
        
        source_weight = source_weights.get(source.lower(), 0.5)
        impact += source_weight * 0.3
        
        # Ключевые слова высокого влияния
        high_impact_keywords = [
            "regulation", "ban", "approval", "etf", "institutional",
            "hack", "breach", "adoption", "partnership", "integration"
        ]
        
        for keyword in high_impact_keywords:
            if keyword in text:
                impact += 0.2
        
        # Упоминание крупных компаний/институтов
        major_entities = [
            "tesla", "microstrategy", "blackrock", "fidelity", "sec",
            "fed", "government", "bank", "paypal", "visa", "mastercard"
        ]
        
        for entity in major_entities:
            if entity in text:
                impact += 0.3
        
        return min(1.0, impact)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Извлечение ключевых слов"""
        # Простое извлечение - в реальности можно использовать NLP
        words = re.findall(r'\b\w{4,}\b', text.lower())
        
        # Фильтруем стоп-слова и оставляем важные
        stop_words = {"that", "this", "with", "from", "they", "have", "been", "were"}
        keywords = [w for w in words if w not in stop_words]
        
        # Возвращаем топ-10 самых частых
        from collections import Counter
        word_counts = Counter(keywords)
        return [word for word, count in word_counts.most_common(10)]
    
    def _classify_news_category(self, text: str) -> str:
        """Классификация категории новости"""
        categories = {
            "regulation": ["regulation", "ban", "legal", "government", "sec", "law"],
            "adoption": ["adoption", "partnership", "integration", "payment", "institutional"],
            "technical": ["upgrade", "fork", "protocol", "blockchain", "network"],
            "security": ["hack", "breach", "security", "vulnerability", "attack"],
            "market": ["price", "surge", "dump", "rally", "crash", "volume"],
            "defi": ["defi", "yield", "staking", "liquidity", "protocol", "dex"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return "general"
    
    def _calculate_urgency(self, text: str, timestamp: datetime) -> float:
        """Расчет срочности новости"""
        urgency = 0.0
        
        # Возраст новости
        age_hours = (datetime.now() - timestamp).total_seconds() / 3600
        age_factor = max(0, 1 - age_hours / 24)  # Снижается за 24 часа
        urgency += age_factor * 0.3
        
        # Ключевые слова срочности
        urgent_keywords = [
            "breaking", "urgent", "alert", "emergency", "immediate",
            "crash", "surge", "hack", "breach", "halt"
        ]
        
        for keyword in urgent_keywords:
            if keyword in text:
                urgency += 0.3
        
        # Экстремальные движения цены
        price_keywords = ["surge", "plunge", "crash", "moon", "dump"]
        for keyword in price_keywords:
            if keyword in text:
                urgency += 0.2
        
        return min(1.0, urgency)
    
    def _extract_mentioned_symbols(self, text: str) -> List[str]:
        """Извлечение упомянутых криптовалютных символов"""
        mentioned = []
        
        for symbol in self.crypto_symbols:
            if symbol.lower() in text:
                mentioned.append(symbol)
        
        return list(set(mentioned))  # Убираем дубликаты
    
    def _calculate_overall_sentiment(self, news_events: List[NewsEvent]) -> float:
        """Расчет общего сентимента"""
        if not news_events:
            return 0.0
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for event in news_events:
            # Вес зависит от влияния и срочности
            weight = event.impact_score * (1 + event.urgency)
            weighted_sum += event.sentiment_score * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _calculate_symbol_sentiment(self, news_events: List[NewsEvent], symbol: str) -> float:
        """Расчет сентимента для конкретного символа"""
        relevant_events = [
            event for event in news_events 
            if symbol in event.symbols_mentioned or 
               symbol.replace("USDT", "").replace("USD", "") in event.symbols_mentioned
        ]
        
        if not relevant_events:
            return 0.0
        
        return self._calculate_overall_sentiment(relevant_events)
    
    def _calculate_crypto_sentiment(self, news_events: List[NewsEvent]) -> float:
        """Расчет общего криптовалютного сентимента"""
        crypto_events = [
            event for event in news_events
            if event.category in ["market", "adoption", "regulation", "defi"] or
               any(symbol in self.crypto_symbols for symbol in event.symbols_mentioned)
        ]
        
        return self._calculate_overall_sentiment(crypto_events)
    
    def _extract_trending_topics(self, news_events: List[NewsEvent]) -> List[str]:
        """Извлечение трендовых топиков"""
        all_keywords = []
        for event in news_events:
            all_keywords.extend(event.keywords)
        
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        
        # Возвращаем топ-5 трендовых топиков
        return [keyword for keyword, count in keyword_counts.most_common(5)]
    
    async def _calculate_sentiment_momentum(self, news_events: List[NewsEvent]) -> float:
        """Расчет моментума сентимента"""
        if len(news_events) < 2:
            return 0.0
        
        # Сортируем по времени
        sorted_events = sorted(news_events, key=lambda x: x.timestamp)
        
        # Разделяем на две половины
        mid_point = len(sorted_events) // 2
        older_events = sorted_events[:mid_point]
        newer_events = sorted_events[mid_point:]
        
        # Рассчитываем средний сентимент для каждой половины
        older_sentiment = self._calculate_overall_sentiment(older_events)
        newer_sentiment = self._calculate_overall_sentiment(newer_events)
        
        # Моментум = изменение сентимента
        return newer_sentiment - older_sentiment
    
    def _create_neutral_sentiment(self, symbols: List[str]) -> MarketSentiment:
        """Создание нейтрального сентимента при отсутствии данных"""
        return MarketSentiment(
            overall_score=0.0,
            crypto_score=0.0,
            symbol_scores={symbol: 0.0 for symbol in symbols},
            trending_topics=[],
            breaking_news_count=0,
            sentiment_momentum=0.0,
            confidence=0.0
        )
    
    async def get_extreme_sentiment_signals(self, symbols: List[str]) -> Dict[str, float]:
        """Получение экстремальных сентиментальных сигналов для торговли"""
        try:
            market_sentiment = await self.analyze_market_sentiment(symbols)
            
            extreme_signals = {}
            
            for symbol in symbols:
                symbol_sentiment = market_sentiment.symbol_scores.get(symbol, 0.0)
                overall_sentiment = market_sentiment.overall_score
                momentum = market_sentiment.sentiment_momentum
                
                # Комбинируем факторы для экстремального сигнала
                extreme_score = 0.0
                
                # Экстремальный сентимент по символу
                if abs(symbol_sentiment) > 0.7:
                    extreme_score += symbol_sentiment * 0.4
                
                # Общий рыночный сентимент
                if abs(overall_sentiment) > 0.6:
                    extreme_score += overall_sentiment * 0.3
                
                # Моментум сентимента
                if abs(momentum) > 0.3:
                    extreme_score += momentum * 0.2
                
                # Экстренные новости
                if market_sentiment.breaking_news_count > 2:
                    extreme_score *= 1.2  # Усиливаем при многих экстренных новостях
                
                # Уверенность в анализе
                extreme_score *= market_sentiment.confidence
                
                # Ограничиваем диапазон
                extreme_signals[symbol] = max(-1.0, min(1.0, extreme_score))
            
            logger.info(f"Экстремальные сентиментальные сигналы: {extreme_signals}")
            
            return extreme_signals
            
        except Exception as e:
            logger.error(f"Ошибка получения экстремальных сигналов: {e}")
            return {symbol: 0.0 for symbol in symbols}

# Глобальный экземпляр анализатора
news_analyzer = NewsSentimentAnalyzer() 