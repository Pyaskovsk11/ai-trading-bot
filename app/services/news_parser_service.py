import requests
from bs4 import BeautifulSoup
from typing import List, Dict
from app.services.news_service import create_news
from app.schemas.news import NewsCreate
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import asyncio
import httpx
import json
from app.services.news_ai_processing_service import NewsAIProcessingService
import app.services.sentiment_service
import app.services.ner_service
import app.services.news_relevance_service
import app.services.rag_analysis_service
from app.services.ai_api_client import AIAPIClient

logger = logging.getLogger(__name__)

# Конфигурация источников новостей
NEWS_SOURCES = {
    "arkham": {
        "url": "https://platform.arkhamintelligence.com/",
        "api_url": "https://api.arkhamintelligence.com/intelligence",
        "selector": ".intelligence-item",
        "name": "Arkham Intelligence"
    },
    "lookonchain": {
        "url": "https://lookonchain.com/",
        "api_url": "https://api.lookonchain.com/alerts",
        "selector": ".alert-item",
        "name": "Lookonchain"
    },
    "coindesk": {
        "url": "https://www.coindesk.com/",
        "rss_url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "selector": ".card-title",
        "name": "CoinDesk"
    },
    "cointelegraph": {
        "url": "https://cointelegraph.com/",
        "rss_url": "https://cointelegraph.com/rss",
        "selector": ".post-card-inline__title",
        "name": "Cointelegraph"
    },
    "theblock": {
        "url": "https://www.theblock.co/",
        "selector": ".articleCard__headline",
        "name": "The Block"
    },
    "decrypt": {
        "url": "https://decrypt.co/",
        "selector": ".post-title",
        "name": "Decrypt"
    },
    "cryptoslate": {
        "url": "https://cryptoslate.com/",
        "rss_url": "https://cryptoslate.com/feed/",
        "selector": ".article-title",
        "name": "CryptoSlate"
    }
}

async def fetch_arkham_news(limit: int = 10) -> List[Dict]:
    """Получение новостей с Arkham Intelligence"""
    news_list = []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Пробуем API, если не работает - парсим сайт
            try:
                response = await client.get(NEWS_SOURCES["arkham"]["api_url"])
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("alerts", [])[:limit]:
                        news_list.append({
                            "title": item.get("title", "Arkham Alert"),
                            "content": item.get("description", ""),
                            "source": "Arkham Intelligence",
                            "published_at": item.get("timestamp", datetime.utcnow().isoformat()),
                            "url": item.get("url", NEWS_SOURCES["arkham"]["url"]),
                            "sentiment_score": 0.0,
                            "category": "onchain"
                        })
            except:
                # Fallback к парсингу сайта
                response = await client.get(NEWS_SOURCES["arkham"]["url"])
                soup = BeautifulSoup(response.text, "html.parser")
                for item in soup.select(NEWS_SOURCES["arkham"]["selector"])[:limit]:
                    title = item.get_text(strip=True)
                    if title:
                        news_list.append({
                            "title": title,
                            "content": title,
                            "source": "Arkham Intelligence",
                            "published_at": datetime.utcnow().isoformat(),
                            "url": NEWS_SOURCES["arkham"]["url"],
                            "sentiment_score": 0.0,
                            "category": "onchain"
                        })
        
        logger.info(f"[Arkham] Получено {len(news_list)} новостей")
    except Exception as e:
        logger.error(f"[Arkham] Ошибка получения новостей: {e}")
    
    return news_list

async def fetch_lookonchain_news(limit: int = 10) -> List[Dict]:
    """Получение новостей с Lookonchain"""
    news_list = []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Пробуем API
            try:
                response = await client.get(NEWS_SOURCES["lookonchain"]["api_url"])
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("data", [])[:limit]:
                        news_list.append({
                            "title": item.get("content", "Lookonchain Alert"),
                            "content": item.get("content", ""),
                            "source": "Lookonchain",
                            "published_at": item.get("created_at", datetime.utcnow().isoformat()),
                            "url": f"https://lookonchain.com/tx/{item.get('tx_hash', '')}",
                            "sentiment_score": 0.0,
                            "category": "onchain"
                        })
            except:
                # Fallback к парсингу сайта
                response = await client.get(NEWS_SOURCES["lookonchain"]["url"])
                soup = BeautifulSoup(response.text, "html.parser")
                for item in soup.select(NEWS_SOURCES["lookonchain"]["selector"])[:limit]:
                    title = item.get_text(strip=True)
                    if title:
                        news_list.append({
                            "title": title,
                            "content": title,
                            "source": "Lookonchain",
                            "published_at": datetime.utcnow().isoformat(),
                            "url": NEWS_SOURCES["lookonchain"]["url"],
                            "sentiment_score": 0.0,
                            "category": "onchain"
                        })
        
        logger.info(f"[Lookonchain] Получено {len(news_list)} новостей")
    except Exception as e:
        logger.error(f"[Lookonchain] Ошибка получения новостей: {e}")
    
    return news_list

async def fetch_coindesk_news(limit: int = 10) -> List[Dict]:
    """Получение новостей с CoinDesk"""
    news_list = []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Пробуем RSS
            try:
                response = await client.get(NEWS_SOURCES["coindesk"]["rss_url"])
                soup = BeautifulSoup(response.text, "xml")
                for item in soup.find_all("item")[:limit]:
                    title = item.find("title").text if item.find("title") else ""
                    description = item.find("description").text if item.find("description") else ""
                    link = item.find("link").text if item.find("link") else ""
                    pub_date = item.find("pubDate").text if item.find("pubDate") else datetime.utcnow().isoformat()
                    
                    if title:
                        news_list.append({
                            "title": title,
                            "content": description,
                            "source": "CoinDesk",
                            "published_at": pub_date,
                            "url": link,
                            "sentiment_score": 0.0,
                            "category": "news"
                        })
            except:
                # Fallback к парсингу сайта
                response = await client.get(NEWS_SOURCES["coindesk"]["url"])
                soup = BeautifulSoup(response.text, "html.parser")
                for item in soup.select(NEWS_SOURCES["coindesk"]["selector"])[:limit]:
                    title = item.get_text(strip=True)
                    if title:
                        news_list.append({
                            "title": title,
                            "content": title,
                            "source": "CoinDesk",
                            "published_at": datetime.utcnow().isoformat(),
                            "url": NEWS_SOURCES["coindesk"]["url"],
                            "sentiment_score": 0.0,
                            "category": "news"
                        })
        
        logger.info(f"[CoinDesk] Получено {len(news_list)} новостей")
    except Exception as e:
        logger.error(f"[CoinDesk] Ошибка получения новостей: {e}")
    
    return news_list

async def fetch_cointelegraph_news(limit: int = 10) -> List[Dict]:
    """Получение новостей с Cointelegraph"""
    news_list = []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            # Пробуем RSS
            try:
                response = await client.get(NEWS_SOURCES["cointelegraph"]["rss_url"])
                soup = BeautifulSoup(response.text, "xml")
                for item in soup.find_all("item")[:limit]:
                    title = item.find("title").text if item.find("title") else ""
                    description = item.find("description").text if item.find("description") else ""
                    link = item.find("link").text if item.find("link") else ""
                    pub_date = item.find("pubDate").text if item.find("pubDate") else datetime.utcnow().isoformat()
                    
                    if title:
                        news_list.append({
                            "title": title,
                            "content": description,
                            "source": "Cointelegraph",
                            "published_at": pub_date,
                            "url": link,
                            "sentiment_score": 0.0,
                            "category": "news"
                        })
            except:
                # Fallback к парсингу сайта
                response = await client.get(NEWS_SOURCES["cointelegraph"]["url"])
    soup = BeautifulSoup(response.text, "html.parser")
                for item in soup.select(NEWS_SOURCES["cointelegraph"]["selector"])[:limit]:
                    title = item.get_text(strip=True)
                    if title:
                        news_list.append({
                            "title": title,
                            "content": title,
                            "source": "Cointelegraph",
                            "published_at": datetime.utcnow().isoformat(),
                            "url": NEWS_SOURCES["cointelegraph"]["url"],
                            "sentiment_score": 0.0,
                            "category": "news"
                        })
        
        logger.info(f"[Cointelegraph] Получено {len(news_list)} новостей")
    except Exception as e:
        logger.error(f"[Cointelegraph] Ошибка получения новостей: {e}")
    
    return news_list

async def fetch_theblock_news(limit: int = 10) -> List[Dict]:
    """Получение новостей с The Block"""
    news_list = []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(NEWS_SOURCES["theblock"]["url"])
            soup = BeautifulSoup(response.text, "html.parser")
            for item in soup.select(NEWS_SOURCES["theblock"]["selector"])[:limit]:
                title = item.get_text(strip=True)
                if title:
        news_list.append({
            "title": title,
            "content": title,
                        "source": "The Block",
            "published_at": datetime.utcnow().isoformat(),
                        "url": NEWS_SOURCES["theblock"]["url"],
                        "sentiment_score": 0.0,
                        "category": "news"
        })
        
        logger.info(f"[The Block] Получено {len(news_list)} новостей")
    except Exception as e:
        logger.error(f"[The Block] Ошибка получения новостей: {e}")
    
    return news_list

async def fetch_all_news_sources(limit_per_source: int = 5) -> List[Dict]:
    """Получение новостей со всех источников"""
    all_news = []
    
    # Запускаем все источники параллельно
    tasks = [
        fetch_arkham_news(limit_per_source),
        fetch_lookonchain_news(limit_per_source),
        fetch_coindesk_news(limit_per_source),
        fetch_cointelegraph_news(limit_per_source),
        fetch_theblock_news(limit_per_source)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if isinstance(result, list):
            all_news.extend(result)
        elif isinstance(result, Exception):
            logger.error(f"Ошибка получения новостей: {result}")
    
    # Сортируем по времени публикации
    all_news.sort(key=lambda x: x.get("published_at", ""), reverse=True)
    
    logger.info(f"Всего получено {len(all_news)} новостей из всех источников")
    return all_news

def fetch_news_from_source() -> List[Dict]:
    """Синхронная версия для обратной совместимости"""
    return asyncio.run(fetch_all_news_sources(limit_per_source=3))

def parse_and_save_news(db: Session):
    """Парсинг и сохранение новостей (синхронная версия)"""
    news_items = fetch_news_from_source()
    for news in news_items:
        try:
        news_obj = NewsCreate(**news)
        create_news(db, news_obj)
        except Exception as e:
            logger.error(f"Ошибка сохранения новости: {e}")

async def fetch_and_save_all_news(db: Session, limit: int = 10):
    """
    Асинхронно парсит и сохраняет новости со всех источников, затем запускает AI-обработку.
    """
    all_news = await fetch_all_news_sources(limit_per_source=limit//5 + 1)
    
    saved = 0
    ai_service = NewsAIProcessingService(
        db,
        app.services.sentiment_service.SentimentService(AIAPIClient("http://localhost:8000")),
        app.services.ner_service.NERService(AIAPIClient("http://localhost:8000")),
        app.services.news_relevance_service.NewsRelevanceService(),
        app.services.rag_analysis_service.RAGAnalysisService(app.services.rag_analysis_service.AIAPIClient("http://localhost:8000"))
    )
    
    for news in all_news[:limit]:
        try:
            news_obj = NewsCreate(**news)
            db_news = create_news(db, news_obj)
            saved += 1
            if db_news:
                await ai_service.process_news(db_news.id)
        except Exception as e:
            logger.error(f"Ошибка сохранения или обработки новости: {e}")
    
    logger.info(f"Сохранено {saved} новостей из всех источников (с AI-обработкой)")

def get_available_sources() -> Dict[str, Dict]:
    """Получить список доступных источников новостей"""
    return {
        source_id: {
            "name": config["name"],
            "url": config["url"],
            "category": "onchain" if source_id in ["arkham", "lookonchain"] else "news"
        }
        for source_id, config in NEWS_SOURCES.items()
    } 