import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Newspaper, 
  TrendingUp, 
  TrendingDown, 
  Activity,
  ExternalLink,
  Filter,
  RefreshCw,
  Globe,
  Zap,
  BarChart3
} from 'lucide-react';

interface NewsItem {
  id: string;
  title: string;
  content: string;
  source: string;
  category: 'news' | 'onchain';
  published_at: string;
  url?: string;
  sentiment_score: number;
  affected_assets?: string[];
}

const NewsAnalysis: React.FC = () => {
  const [selectedSource, setSelectedSource] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Доступные источники новостей
  const newsSources = {
    'arkham': { name: 'Arkham Intelligence', category: 'onchain', icon: '🔍' },
    'lookonchain': { name: 'Lookonchain', category: 'onchain', icon: '⛓️' },
    'cryptopanic': { name: 'CryptoPanic', category: 'news', icon: '🚨' },
    'coindesk': { name: 'CoinDesk', category: 'news', icon: '📰' },
    'cointelegraph': { name: 'Cointelegraph', category: 'news', icon: '📡' },
    'binance': { name: 'Binance News', category: 'news', icon: '🟡' },
    'theblock': { name: 'The Block', category: 'news', icon: '🧱' },
    'decrypt': { name: 'Decrypt', category: 'news', icon: '🔓' },
    'cryptoslate': { name: 'CryptoSlate', category: 'news', icon: '📊' }
  };

  const { data: newsData, isLoading, error, refetch } = useQuery({
    queryKey: ['news-analysis', selectedSource, selectedCategory],
    queryFn: async (): Promise<NewsItem[]> => {
      try {
        console.log('Запрос новостей к бэкенду...');
        const response = await fetch('http://localhost:8000/news?limit=10');
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const rawNews = await response.json();
        console.log('Получены новости:', rawNews);
        
        // Преобразуем данные с бэкенда в формат компонента
        const formattedNews: NewsItem[] = rawNews.map((item: any, index: number) => {
          // Определяем sentiment_score на основе источника (временно)
          let sentiment_score = 0;
          if (item.source === 'CoinDesk' || item.source === 'Cointelegraph') {
            sentiment_score = Math.random() * 0.8 - 0.4; // От -0.4 до 0.4
          } else if (item.source === 'Lookonchain') {
            sentiment_score = Math.random() * 0.6 - 0.3; // От -0.3 до 0.3
          }
          
          // Определяем категорию
          const category = (
            item.source === 'Lookonchain' || 
            item.source === 'Lookonchain Enhanced' || 
            item.source === 'Arkham Intelligence'
          ) ? 'onchain' : 'news';
          
          return {
            id: `news_${index}`,
            title: item.title || 'Без заголовка',
            content: item.content || 'Содержание недоступно',
            source: item.source || 'Неизвестный источник',
            category: category,
            published_at: item.published_at || new Date().toISOString(),
            url: item.url || undefined,
            sentiment_score: sentiment_score,
            affected_assets: ['BTC', 'ETH'] // Заглушка, можно улучшить
          };
        });

        // Фильтрация по источнику и категории
        return formattedNews.filter(item => {
          const sourceMatch = selectedSource === 'all' || item.source.toLowerCase().includes(selectedSource.toLowerCase());
          const categoryMatch = selectedCategory === 'all' || item.category === selectedCategory;
          return sourceMatch && categoryMatch;
        });
        
      } catch (error) {
        console.error('Ошибка загрузки новостей:', error);
        // В случае ошибки возвращаем заглушку
        return [{
          id: 'error',
          title: 'Ошибка загрузки новостей',
          content: `Не удалось загрузить новости с сервера: ${error}`,
          source: 'Система',
          category: 'news',
          published_at: new Date().toISOString(),
          sentiment_score: 0,
          affected_assets: []
        }];
      }
    },
    refetchInterval: 30000, // Обновляем каждые 30 секунд
  });

  const getSentimentColor = (score: number) => {
    if (score > 0.3) return 'text-green-400';
    if (score < -0.3) return 'text-red-400';
    return 'text-yellow-400';
  };

  const getSentimentIcon = (score: number) => {
    if (score > 0.3) return <TrendingUp className="w-4 h-4" />;
    if (score < -0.3) return <TrendingDown className="w-4 h-4" />;
    return <Activity className="w-4 h-4" />;
  };

  const getSentimentText = (score: number) => {
    if (score > 0.3) return 'Позитивное';
    if (score < -0.3) return 'Негативное';
    return 'Нейтральное';
  };

  const formatTimeAgo = (dateString: string) => {
    const now = new Date();
    const date = new Date(dateString);
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 60) return `${diffInMinutes} мин назад`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)} ч назад`;
    return `${Math.floor(diffInMinutes / 1440)} дн назад`;
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-white flex items-center">
          <Newspaper className="w-8 h-8 mr-3 text-blue-400" />
          Анализ новостей
        </h1>
        <button
          onClick={() => refetch()}
          className="flex items-center bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Обновить
        </button>
      </div>

      <p className="text-gray-400">
        AI-анализ новостей и их влияния на рынок криптовалют
      </p>

      {/* Статистика источников */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Всего источников</p>
              <p className="text-2xl font-bold text-white">{Object.keys(newsSources).length}</p>
            </div>
            <Globe className="w-8 h-8 text-blue-400" />
          </div>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Onchain источники</p>
              <p className="text-2xl font-bold text-white">
                {Object.values(newsSources).filter(s => s.category === 'onchain').length}
              </p>
            </div>
            <Zap className="w-8 h-8 text-yellow-400" />
          </div>
        </div>
        
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Новостные источники</p>
              <p className="text-2xl font-bold text-white">
                {Object.values(newsSources).filter(s => s.category === 'news').length}
              </p>
            </div>
            <BarChart3 className="w-8 h-8 text-green-400" />
          </div>
        </div>
      </div>

      {/* Источники новостей */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Подключенные источники</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
          {Object.entries(newsSources).map(([key, source]) => (
            <div key={key} className="bg-gray-700 rounded-lg p-3 text-center">
              <div className="text-2xl mb-2">{source.icon}</div>
              <p className="text-white text-sm font-medium">{source.name}</p>
              <p className={`text-xs mt-1 ${
                source.category === 'onchain' ? 'text-yellow-400' : 'text-blue-400'
              }`}>
                {source.category === 'onchain' ? 'Onchain' : 'Новости'}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Фильтры */}
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center space-x-4">
          <Filter className="w-5 h-5 text-gray-400" />
          <div className="flex space-x-4">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
            >
              <option value="all">Все категории</option>
              <option value="news">Новости</option>
              <option value="onchain">Onchain</option>
            </select>
            
            <select
              value={selectedSource}
              onChange={(e) => setSelectedSource(e.target.value)}
              className="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
            >
              <option value="all">Все источники</option>
              {Object.entries(newsSources).map(([key, source]) => (
                <option key={key} value={key}>{source.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Список новостей */}
      <div className="space-y-4">
        {newsData?.map((news) => (
          <div key={news.id} className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    news.category === 'onchain' 
                      ? 'bg-yellow-900 text-yellow-300' 
                      : 'bg-blue-900 text-blue-300'
                  }`}>
                    {news.source}
                  </span>
                  <span className="text-gray-400 text-sm">
                    {formatTimeAgo(news.published_at)}
                  </span>
                </div>
                <h3 className="text-xl font-semibold text-white mb-2">
                  {news.title}
                </h3>
                <p className="text-gray-300 mb-4">
                  {news.content}
                </p>
              </div>
              
              {news.url && (
                <a
                  href={news.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:text-blue-300 ml-4"
                >
                  <ExternalLink className="w-5 h-5" />
                </a>
              )}
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className={`flex items-center space-x-1 ${getSentimentColor(news.sentiment_score)}`}>
                  {getSentimentIcon(news.sentiment_score)}
                  <span className="text-sm font-medium">
                    {getSentimentText(news.sentiment_score)}
                  </span>
                  <span className="text-xs">
                    ({news.sentiment_score.toFixed(2)})
                  </span>
                </div>
                
                {news.affected_assets && news.affected_assets.length > 0 && (
                  <div className="flex items-center space-x-1">
                    <span className="text-gray-400 text-sm">Активы:</span>
                    <div className="flex space-x-1">
                      {news.affected_assets.map((asset) => (
                        <span
                          key={asset}
                          className="bg-gray-700 text-white px-2 py-1 rounded text-xs"
                        >
                          {asset}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {newsData?.length === 0 && (
        <div className="bg-gray-800 rounded-lg p-12 text-center">
          <Newspaper className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-400 mb-2">
            Новости не найдены
          </h3>
          <p className="text-gray-500">
            Попробуйте изменить фильтры или обновить данные
          </p>
        </div>
      )}
    </div>
  );
};

export default NewsAnalysis; 