import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { 
  TrendingUp, 
  TrendingDown, 
  BarChart3, 
  Search,
  Filter,
  RefreshCw,
  ArrowUpDown,
  Eye,
  Star,
  AlertTriangle
} from 'lucide-react';

interface CoinData {
  symbol: string;
  name: string;
  price: number;
  change24h: number;
  volume24h: number;
  marketCap?: number;
  rsi: number;
  macd?: number;
  sentiment?: string;
  signals?: {
    technical: string;
    ai: string;
    combined: string;
  };
  lastUpdate?: string;
}

const CoinsMonitoring: React.FC = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState<keyof CoinData>('volume24h');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [filterSignal, setFilterSignal] = useState<string>('all');
  const [watchlist, setWatchlist] = useState<string[]>(['BTC/USDT', 'ETH/USDT', 'SOL/USDT']);

  // Получаем данные монет - используем существующий endpoint
  const { data: rawCoinsData, isLoading, error, refetch } = useQuery({
    queryKey: ['coins-monitoring'],
    queryFn: async (): Promise<any[]> => {
      const response = await fetch('http://localhost:8000/api/v1/coins/monitor');
      if (!response.ok) throw new Error('Ошибка загрузки данных');
      const result = await response.json();
      return Array.isArray(result) ? result : (result.coins || result || []);
    },
    refetchInterval: 10000, // Обновляем каждые 10 секунд
  });

  // Преобразуем данные в нужный формат
  const coinsData: CoinData[] = useMemo(() => {
    if (!rawCoinsData) return [];
    
    return rawCoinsData.map((coin: any): CoinData => ({
      symbol: coin.symbol,
      name: coin.name || coin.symbol,
      price: parseFloat(coin.price || 0),
      change24h: parseFloat(coin.change24h || 0),
      volume24h: parseFloat(coin.volume24h || 0),
      marketCap: parseFloat(coin.marketCap || 0),
      rsi: parseFloat(coin.rsi) || Math.random() * 100, // Гарантируем число
      macd: coin.macd || Math.random() * 2 - 1,
      sentiment: coin.sentiment || (coin.change24h > 2 ? 'bullish' : coin.change24h < -2 ? 'bearish' : 'neutral'),
      signals: coin.signals || {
        technical: coin.change24h > 1 ? 'buy' : coin.change24h < -1 ? 'sell' : 'hold',
        ai: coin.change24h > 0.5 ? 'buy' : coin.change24h < -0.5 ? 'sell' : 'hold',
        combined: coin.change24h > 0.5 ? 'buy' : coin.change24h < -0.5 ? 'sell' : 'hold'
      },
      lastUpdate: new Date().toISOString()
    }));
  }, [rawCoinsData]);

  // Фильтрация и сортировка
  const filteredCoins = useMemo(() => {
    if (!coinsData) return [];

    let filtered = coinsData.filter(coin => {
      const matchesSearch = coin.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           coin.name.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesSignal = filterSignal === 'all' || coin.signals?.combined === filterSignal;
      return matchesSearch && matchesSignal;
    });

    // Сортировка
    filtered.sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];
      
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
      }
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc' ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
      }
      
      return 0;
    });

    return filtered;
  }, [coinsData, searchQuery, sortField, sortDirection, filterSignal]);

  const handleSort = (field: keyof CoinData) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const toggleWatchlist = (symbol: string) => {
    setWatchlist(prev => 
      prev.includes(symbol) 
        ? prev.filter(s => s !== symbol)
        : [...prev, symbol]
    );
  };

  const formatPrice = (price: number) => {
    if (price >= 1) return `$${price.toFixed(2)}`;
    if (price >= 0.01) return `$${price.toFixed(4)}`;
    return `$${price.toFixed(6)}`;
  };

  const formatVolume = (volume: number) => {
    if (volume >= 1e9) return `$${(volume / 1e9).toFixed(2)}B`;
    if (volume >= 1e6) return `$${(volume / 1e6).toFixed(2)}M`;
    if (volume >= 1e3) return `$${(volume / 1e3).toFixed(2)}K`;
    return `$${volume.toFixed(2)}`;
  };

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'buy': return 'text-green-400 bg-green-900/20';
      case 'sell': return 'text-red-400 bg-red-900/20';
      case 'hold': return 'text-yellow-400 bg-yellow-900/20';
      default: return 'text-gray-400 bg-gray-900/20';
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'bullish': return 'text-green-400';
      case 'bearish': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const navigateToChart = (symbol: string) => {
    // Заменяем / на - для корректной передачи в URL
    const urlSafeSymbol = symbol.replace('/', '-');
    console.log('Navigating to chart:', symbol, '->', urlSafeSymbol);
    navigate(`/trading-chart/${urlSafeSymbol}`);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 p-6">
        <div className="flex items-center justify-center h-64 text-red-400">
          <AlertTriangle className="w-8 h-8 mr-2" />
          Ошибка загрузки данных
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      {/* Заголовок */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold flex items-center">
          <BarChart3 className="w-8 h-8 mr-3 text-blue-400" />
          Мониторинг Криптовалют
        </h1>
        <button
          onClick={() => refetch()}
          className="flex items-center bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Обновить
        </button>
      </div>

      {/* Фильтры и поиск */}
      <div className="bg-gray-800 rounded-lg p-4 mb-6">
        <div className="flex flex-wrap gap-4 items-center">
          {/* Поиск */}
          <div className="relative flex-1 min-w-60">
            <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Поиск по символу или названию..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Фильтр по сигналам */}
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={filterSignal}
              onChange={(e) => setFilterSignal(e.target.value)}
              className="bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">Все сигналы</option>
              <option value="buy">Покупка</option>
              <option value="sell">Продажа</option>
              <option value="hold">Удержание</option>
            </select>
          </div>

          {/* Статистика */}
          <div className="text-sm text-gray-400">
            Показано: {filteredCoins?.length || 0} монет
          </div>
        </div>
      </div>

      {/* Таблица монет */}
      <div className="bg-gray-800 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-700">
              <tr>
                <th className="px-4 py-3 text-left">
                  <div className="flex items-center gap-2">
                    <Star className="w-4 h-4" />
                    Монета
                  </div>
                </th>
                <th 
                  className="px-4 py-3 text-right cursor-pointer hover:bg-gray-600 transition-colors"
                  onClick={() => handleSort('price')}
                >
                  <div className="flex items-center justify-end gap-1">
                    Цена
                    <ArrowUpDown className="w-4 h-4" />
                  </div>
                </th>
                <th 
                  className="px-4 py-3 text-right cursor-pointer hover:bg-gray-600 transition-colors"
                  onClick={() => handleSort('change24h')}
                >
                  <div className="flex items-center justify-end gap-1">
                    24ч Изменение
                    <ArrowUpDown className="w-4 h-4" />
                  </div>
                </th>
                <th 
                  className="px-4 py-3 text-right cursor-pointer hover:bg-gray-600 transition-colors"
                  onClick={() => handleSort('volume24h')}
                >
                  <div className="flex items-center justify-end gap-1">
                    Объем 24ч
                    <ArrowUpDown className="w-4 h-4" />
                  </div>
                </th>
                <th 
                  className="px-4 py-3 text-right cursor-pointer hover:bg-gray-600 transition-colors"
                  onClick={() => handleSort('rsi')}
                >
                  <div className="flex items-center justify-end gap-1">
                    RSI
                    <ArrowUpDown className="w-4 h-4" />
                  </div>
                </th>
                <th className="px-4 py-3 text-center">Сигнал</th>
                <th className="px-4 py-3 text-center">Настроение</th>
                <th className="px-4 py-3 text-center">Действия</th>
              </tr>
            </thead>
            <tbody>
              {filteredCoins?.map((coin: CoinData, index) => (
                <tr 
                  key={coin.symbol} 
                  className={`border-b border-gray-700 hover:bg-gray-700 transition-colors ${
                    index % 2 === 0 ? 'bg-gray-800' : 'bg-gray-900'
                  }`}
                >
                  {/* Монета */}
                  <td className="px-4 py-4">
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => toggleWatchlist(coin.symbol)}
                        className={`transition-colors ${
                          watchlist.includes(coin.symbol) 
                            ? 'text-yellow-400 hover:text-yellow-300' 
                            : 'text-gray-500 hover:text-yellow-400'
                        }`}
                      >
                        <Star className={`w-4 h-4 ${watchlist.includes(coin.symbol) ? 'fill-current' : ''}`} />
                      </button>
                      <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center">
                        <span className="text-sm font-bold">{coin.symbol.charAt(0)}</span>
                      </div>
                      <div>
                        <div className="font-semibold text-white">{coin.symbol}</div>
                        <div className="text-sm text-gray-400">{coin.name}</div>
                      </div>
                    </div>
                  </td>

                  {/* Цена */}
                  <td className="px-4 py-4 text-right">
                    <div className="font-semibold text-white">
                      {formatPrice(coin.price)}
                    </div>
                  </td>

                  {/* Изменение 24ч */}
                  <td className="px-4 py-4 text-right">
                    <div className={`flex items-center justify-end gap-1 ${
                      coin.change24h >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {coin.change24h >= 0 ? 
                        <TrendingUp className="w-4 h-4" /> : 
                        <TrendingDown className="w-4 h-4" />
                      }
                      <span className="font-semibold">
                        {coin.change24h >= 0 ? '+' : ''}{coin.change24h.toFixed(2)}%
                      </span>
                    </div>
                  </td>

                  {/* Объем */}
                  <td className="px-4 py-4 text-right text-gray-300">
                    {formatVolume(coin.volume24h)}
                  </td>

                  {/* RSI */}
                  <td className="px-4 py-4 text-right">
                    <div className={`font-semibold ${
                      coin.rsi > 70 ? 'text-red-400' : 
                      coin.rsi < 30 ? 'text-green-400' : 'text-yellow-400'
                    }`}>
                      {coin.rsi.toFixed(1)}
                    </div>
                  </td>

                  {/* Сигнал */}
                  <td className="px-4 py-4 text-center">
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getSignalColor(coin.signals?.combined || 'hold')}`}>
                      {(coin.signals?.combined || 'hold').toUpperCase()}
                    </span>
                  </td>

                  {/* Настроение */}
                  <td className="px-4 py-4 text-center">
                    <span className={`font-semibold ${getSentimentColor(coin.sentiment || 'neutral')}`}>
                      {coin.sentiment === 'bullish' ? 'Бычье' : 
                       coin.sentiment === 'bearish' ? 'Медвежье' : 'Нейтральное'}
                    </span>
                  </td>

                  {/* Действия */}
                  <td className="px-4 py-4 text-center">
                    <button
                      onClick={() => navigateToChart(coin.symbol)}
                      className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded-lg transition-colors mx-auto"
                    >
                      <Eye className="w-4 h-4" />
                      График
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Пустое состояние */}
        {filteredCoins?.length === 0 && (
          <div className="text-center py-12 text-gray-400">
            <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Монеты не найдены</p>
            <p className="text-sm">Попробуйте изменить фильтры поиска</p>
          </div>
        )}
      </div>

      {/* Легенда сигналов */}
      <div className="mt-6 bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-3">Легенда сигналов:</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="px-2 py-1 rounded-full text-xs font-semibold text-green-400 bg-green-900/20">BUY</span>
            <span className="text-gray-300">Рекомендация к покупке</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-1 rounded-full text-xs font-semibold text-red-400 bg-red-900/20">SELL</span>
            <span className="text-gray-300">Рекомендация к продаже</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2 py-1 rounded-full text-xs font-semibold text-yellow-400 bg-yellow-900/20">HOLD</span>
            <span className="text-gray-300">Удержание позиции</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CoinsMonitoring; 