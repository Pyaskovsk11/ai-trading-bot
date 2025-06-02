from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any
from app.services.news_service import NewsService
from app.services.news_parser_service import get_available_sources

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
def get_news(limit: int = Query(10, ge=1, le=100)):
    """Получить свежие новости с всех подключенных источников"""
    service = NewsService()
    news = service.get_all_news()
    return news[:limit]

@router.get("/sources", response_model=Dict[str, Dict[str, Any]])
def get_news_sources():
    """Получить список доступных источников новостей"""
    try:
        sources = get_available_sources()
        return {
            "sources": sources,
            "total": len(sources),
            "onchain_sources": len([s for s in sources.values() if s.get("category") == "onchain"]),
            "news_sources": len([s for s in sources.values() if s.get("category") == "news"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения источников: {str(e)}")

@router.get("/by-source/{source_name}")
def get_news_by_source(source_name: str, limit: int = Query(10, ge=1, le=50)):
    """Получить новости от конкретного источника"""
    service = NewsService()
    all_news = service.get_all_news()
    
    # Фильтруем по источнику
    filtered_news = [
        news for news in all_news 
        if news.get("source", "").lower() == source_name.lower()
    ]
    
    return filtered_news[:limit]

@router.get("/by-category/{category}")
def get_news_by_category(category: str, limit: int = Query(10, ge=1, le=50)):
    """Получить новости по категории (news/onchain)"""
    if category not in ["news", "onchain"]:
        raise HTTPException(status_code=400, detail="Категория должна быть 'news' или 'onchain'")
    
    service = NewsService()
    all_news = service.get_all_news()
    
    # Фильтруем по категории
    filtered_news = [
        news for news in all_news 
        if news.get("category", "").lower() == category.lower()
    ]
    
    return filtered_news[:limit] 