import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import TradingChart from '../components/TradingChart';
import { 
  TrendingUp, 
  Activity, 
  Clock,
  RefreshCw,
  Plus,
  Minus
} from 'lucide-react';

interface ChartData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface Position {
  id: string;
  symbol: string;
  side: 'long' | 'short';
  size: number;
  entry_price: number;
  current_price: number;
  unrealized_pnl: number;
  pnl_percent: number;
  entry_time: string;
  stop_loss?: number;
  take_profit?: number;
}

interface Trade {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  size: number;
  entry_price: number;
  exit_price?: number;
  realized_pnl?: number;
  entry_time: string;
  exit_time?: string;
  status: 'open' | 'closed';
}

const TradingChartPage: React.FC = () => {
  const { symbol: urlSymbol } = useParams<{ symbol: string }>();
  const symbol = urlSymbol?.replace('-', '/') || 'BTC/USDT';
  const [activeTab, setActiveTab] = useState<'positions' | 'history'>('positions');

  // Сохранение позиции скролла
  useEffect(() => {
    const savedScrollPosition = sessionStorage.getItem(`scroll-${symbol}`);
    if (savedScrollPosition) {
      setTimeout(() => {
        window.scrollTo(0, parseInt(savedScrollPosition));
      }, 100); // Небольшая задержка для загрузки контента
    }

    const handleScroll = () => {
      sessionStorage.setItem(`scroll-${symbol}`, window.scrollY.toString());
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [symbol]);

  // Получаем данные графика
  const { data: chartData, isLoading: chartLoading } = useQuery({
    queryKey: ['chart-data', symbol],
    queryFn: async (): Promise<{chartData: ChartData[], indicators: any[]}> => {
      const apiSymbol = symbol.replace('/', '');
      const response = await fetch(`http://localhost:8000/api/v1/charts/historical-data?symbol=${apiSymbol}`);
      if (!response.ok) throw new Error('Ошибка загрузки данных графика');
      
      const result = await response.json();
      console.log('Raw API response:', result);
      console.log('Type of result:', typeof result);
      console.log('Is array:', Array.isArray(result));
      
      // Обрабатываем разные форматы ответа API
      let data = result;
      if (result.data) {
        data = result.data;
      } else if (result.ohlcv) {
        data = result.ohlcv;
      } else if (result.candles) {
        data = result.candles;
      } else if (!Array.isArray(result)) {
        console.error('Unexpected API response format:', result);
        throw new Error('Неверный формат данных API');
      }
      
      console.log('Processed data:', data);
      console.log('Data length:', data?.length);
      
      if (!Array.isArray(data)) {
        throw new Error('API не вернул массив данных');
      }
      
      const chartData = data.map((item: any) => ({
        time: item.time || new Date(item.timestamp).getTime() / 1000,
        open: parseFloat(item.open),
        high: parseFloat(item.high),
        low: parseFloat(item.low),
        close: parseFloat(item.close),
        volume: parseFloat(item.volume || 0)
      }));

      // Получаем данные индикаторов
      const indicators = result.indicators || [];
      console.log('Indicators data:', indicators?.length, 'points');

      return { chartData, indicators };
    },
    refetchInterval: 10000,
  });

  // Получаем данные позиций
  const { data: portfolioData, refetch: refetchPortfolio } = useQuery({
    queryKey: ['trading-portfolio'],
    queryFn: async () => {
      const response = await fetch('http://localhost:8000/api/v1/trading/portfolio');
      if (!response.ok) throw new Error('Ошибка загрузки портфеля');
      return await response.json();
    },
    refetchInterval: 5000,
  });

  // Получаем историю сделок
  const { data: tradesHistory } = useQuery({
    queryKey: ['trades-history'],
    queryFn: async () => {
      const response = await fetch(`http://localhost:8000/api/v1/trading/history`);
      if (!response.ok) throw new Error('Ошибка загрузки истории');
      return await response.json();
    },
    refetchInterval: 30000,
  });

  // Парсим данные
  const activePositions: Position[] = portfolioData?.active_positions?.map((pos: any) => ({
    id: pos.id || `pos_${Date.now()}`,
    symbol: pos.symbol,
    side: pos.side === 'buy' || pos.quantity > 0 ? 'long' : 'short',
    size: Math.abs(pos.quantity || pos.size || 0),
    entry_price: pos.entry_price || pos.avg_price || 0,
    current_price: pos.current_price || pos.mark_price || 0,
    unrealized_pnl: pos.unrealized_pnl || pos.pnl || 0,
    pnl_percent: pos.pnl_percent || 0,
    entry_time: pos.entry_time || pos.created_at || new Date().toISOString(),
    stop_loss: pos.stop_loss,
    take_profit: pos.take_profit
  })) || [];

  const completedTrades: Trade[] = tradesHistory?.trades?.filter((trade: any) => trade.exit_time)?.map((trade: any) => ({
    id: trade.id,
    symbol: trade.symbol,
    side: trade.side.toLowerCase(),
    size: trade.quantity,
    entry_price: trade.entry_price,
    exit_price: trade.exit_price,
    realized_pnl: trade.pnl,
    entry_time: trade.entry_time,
    exit_time: trade.exit_time,
    status: 'closed'
  })) || [];

  const formatPrice = (price: number) => `$${price.toFixed(2)}`;
  const formatPnL = (pnl: number) => (pnl >= 0 ? '+' : '') + pnl.toFixed(2);
  const formatTime = (timeString: string) => {
    return new Date(timeString).toLocaleString('ru-RU', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (chartLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Заголовок */}
      <div className="bg-gray-800 px-6 py-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              <TrendingUp className="w-6 h-6 text-green-400" />
              {symbol} Торговля
            </h1>
            <div className="flex items-center gap-4 text-sm">
              <div className="text-green-400">
                Цена: {chartData?.chartData?.[chartData.chartData.length - 1]?.close ? formatPrice(chartData.chartData[chartData.chartData.length - 1].close) : '—'}
              </div>
              <div className="text-gray-400">
                Активных позиций: {activePositions.length}
              </div>
            </div>
          </div>
          <button
            onClick={() => refetchPortfolio()}
            className="flex items-center bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Обновить
          </button>
        </div>
      </div>

      <div className="flex h-[calc(100vh-80px)]">
        {/* Левая часть - График */}
        <div className="flex-1 p-4">
          <TradingChart
            symbol={symbol}
            data={chartData?.chartData || []}
            indicators={chartData?.indicators || []}
            className="h-full"
          />
        </div>

        {/* Правая часть - Торговые панели */}
        <div className="w-96 bg-gray-800 border-l border-gray-700 flex flex-col">
          
          {/* Быстрые кнопки торговли */}
          <div className="p-4 border-b border-gray-700">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">Быстрая торговля</h3>
            <div className="grid grid-cols-2 gap-2">
              <button className="bg-green-600 hover:bg-green-700 text-white py-2 px-3 rounded text-sm font-semibold transition-colors flex items-center justify-center gap-2">
                <Plus className="w-4 h-4" />
                КУПИТЬ
              </button>
              <button className="bg-red-600 hover:bg-red-700 text-white py-2 px-3 rounded text-sm font-semibold transition-colors flex items-center justify-center gap-2">
                <Minus className="w-4 h-4" />
                ПРОДАТЬ
              </button>
            </div>
          </div>

          {/* Вкладки позиций и истории */}
          <div className="border-b border-gray-700">
            <div className="flex">
              <button
                onClick={() => setActiveTab('positions')}
                className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${
                  activeTab === 'positions'
                    ? 'bg-gray-700 text-white border-b-2 border-blue-500'
                    : 'text-gray-400 hover:text-white hover:bg-gray-700'
                }`}
              >
                <div className="flex items-center justify-center gap-2">
                  <Activity className="w-4 h-4" />
                  Позиции ({activePositions.length})
                </div>
              </button>
              <button
                onClick={() => setActiveTab('history')}
                className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${
                  activeTab === 'history'
                    ? 'bg-gray-700 text-white border-b-2 border-blue-500'
                    : 'text-gray-400 hover:text-white hover:bg-gray-700'
                }`}
              >
                <div className="flex items-center justify-center gap-2">
                  <Clock className="w-4 h-4" />
                  История ({completedTrades.length})
                </div>
              </button>
            </div>
          </div>

          {/* Содержимое вкладок */}
          <div className="flex-1 overflow-y-auto">
            {activeTab === 'positions' && (
              <div className="p-4">
                {activePositions.length === 0 ? (
                  <div className="text-center py-12 text-gray-400">
                    <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>Нет активных позиций</p>
                    <p className="text-sm">Откройте позицию для начала торговли</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {activePositions.map((position) => (
                      <div key={position.id} className="bg-gray-700 rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className={`px-2 py-1 rounded text-xs font-semibold ${
                              position.side === 'long' 
                                ? 'bg-green-900 text-green-400' 
                                : 'bg-red-900 text-red-400'
                            }`}>
                              {position.side.toUpperCase()}
                            </span>
                            <span className="text-white font-medium">{position.symbol}</span>
                          </div>
                          <div className="text-right">
                            <div className={`text-sm font-semibold ${
                              position.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'
                            }`}>
                              {formatPnL(position.unrealized_pnl)}
                            </div>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div>
                            <span className="text-gray-400">Размер:</span>
                            <span className="text-white ml-1">{position.size}</span>
                          </div>
                          <div>
                            <span className="text-gray-400">Вход:</span>
                            <span className="text-white ml-1">{formatPrice(position.entry_price)}</span>
                          </div>
                          <div>
                            <span className="text-gray-400">Текущая:</span>
                            <span className="text-white ml-1">{formatPrice(position.current_price)}</span>
                          </div>
                          <div>
                            <span className="text-gray-400">P&L%:</span>
                            <span className={`ml-1 ${position.pnl_percent >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {position.pnl_percent.toFixed(2)}%
                            </span>
                          </div>
                        </div>

                        <div className="mt-2 pt-2 border-t border-gray-600 flex gap-2">
                          <button className="flex-1 bg-red-600 hover:bg-red-700 text-white py-1 px-2 rounded text-xs transition-colors">
                            Закрыть
                          </button>
                          <button className="flex-1 bg-gray-600 hover:bg-gray-500 text-white py-1 px-2 rounded text-xs transition-colors">
                            Изменить
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'history' && (
              <div className="p-4">
                {completedTrades.length === 0 ? (
                  <div className="text-center py-12 text-gray-400">
                    <Clock className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>Нет истории сделок</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {completedTrades.slice(0, 20).map((trade) => (
                      <div key={trade.id} className="bg-gray-700 rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className={`px-2 py-1 rounded text-xs font-semibold ${
                              trade.side === 'buy' 
                                ? 'bg-green-900 text-green-400' 
                                : 'bg-red-900 text-red-400'
                            }`}>
                              {trade.side.toUpperCase()}
                            </span>
                            <span className="text-white font-medium">{trade.symbol}</span>
                          </div>
                          <div className="text-right">
                            <div className={`text-sm font-semibold ${
                              (trade.realized_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                            }`}>
                              {formatPnL(trade.realized_pnl || 0)}
                            </div>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div>
                            <span className="text-gray-400">Размер:</span>
                            <span className="text-white ml-1">{trade.size}</span>
                          </div>
                          <div>
                            <span className="text-gray-400">Вход:</span>
                            <span className="text-white ml-1">{formatPrice(trade.entry_price)}</span>
                          </div>
                          <div>
                            <span className="text-gray-400">Выход:</span>
                            <span className="text-white ml-1">
                              {trade.exit_price ? formatPrice(trade.exit_price) : '—'}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-400">Время:</span>
                            <span className="text-white ml-1">{formatTime(trade.entry_time)}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Статистика внизу */}
          <div className="p-4 border-t border-gray-700 bg-gray-800">
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="text-center">
                <div className="text-gray-400">Общий P&L</div>
                <div className="text-green-400 font-semibold">
                  {formatPnL(
                    activePositions.reduce((sum, pos) => sum + pos.unrealized_pnl, 0) +
                    completedTrades.reduce((sum, trade) => sum + (trade.realized_pnl || 0), 0)
                  )}
                </div>
              </div>
              <div className="text-center">
                <div className="text-gray-400">Win Rate</div>
                <div className="text-blue-400 font-semibold">
                  {completedTrades.length > 0 
                    ? `${((completedTrades.filter(t => (t.realized_pnl || 0) > 0).length / completedTrades.length) * 100).toFixed(1)}%`
                    : '0%'
                  }
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradingChartPage; 