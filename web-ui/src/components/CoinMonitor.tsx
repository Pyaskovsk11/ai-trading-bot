import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  DollarSign, 
  BarChart3,
  AlertTriangle,
  CheckCircle,
  Clock,
  Volume2
} from 'lucide-react';

interface CoinData {
  symbol: string;
  name: string;
  price: number;
  change24h: number;
  volume24h: number;
  marketCap: number;
  rsi: number;
  macd: number;
  bollinger: {
    upper: number;
    middle: number;
    lower: number;
    position: 'upper' | 'middle' | 'lower';
  };
  support: number;
  resistance: number;
  sentiment: 'bullish' | 'bearish' | 'neutral';
  signals: {
    technical: 'buy' | 'sell' | 'hold';
    ai: 'buy' | 'sell' | 'hold';
    combined: 'buy' | 'sell' | 'hold';
  };
  lastUpdate: string;
}

const CoinMonitor: React.FC = () => {
  const [selectedCoins, setSelectedCoins] = useState<string[]>([
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'ADA/USDT'
  ]);

  const { data: coinsData, isLoading, error } = useQuery({
    queryKey: ['coins-monitor', selectedCoins],
    queryFn: async (): Promise<CoinData[]> => {
      try {
        const symbolsParam = selectedCoins.join(',');
        const response = await fetch(`http://localhost:8000/api/v1/coins/monitor?symbols=${symbolsParam}`);
        
        if (!response.ok) {
          throw new Error('Ошибка загрузки данных');
        }
        
        return await response.json();
      } catch (error) {
        console.error('Ошибка API:', error);
        // Показываем ошибку пользователю вместо fallback данных
        throw error;
      }
    },
    refetchInterval: 5000, // Обновляем каждые 5 секунд
  });

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'buy': return 'text-green-400';
      case 'sell': return 'text-red-400';
      default: return 'text-yellow-400';
    }
  };

  const getSignalIcon = (signal: string) => {
    switch (signal) {
      case 'buy': return <TrendingUp className="w-4 h-4" />;
      case 'sell': return <TrendingDown className="w-4 h-4" />;
      default: return <Activity className="w-4 h-4" />;
    }
  };

  const getRSIColor = (rsi: number) => {
    if (rsi > 70) return 'text-red-400'; // Перекупленность
    if (rsi < 30) return 'text-green-400'; // Перепроданность
    return 'text-blue-400'; // Нейтральная зона
  };

  const formatPrice = (price: number, symbol?: string) => {
    if (price >= 10000) {
      // Для BTC и других дорогих монет: $103,556.78
      return price.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      });
    } else if (price >= 1) {
      // Для ETH, BNB, SOL и т.д.: $2,516.85
      return price.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 4
      });
    } else {
      // Для мелких монет ADA, DOGE: $0.895643
      return price.toFixed(6);
    }
  };

  const formatVolume = (num: number) => {
    if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`;
    if (num >= 1e3) return `${(num / 1e3).toFixed(2)}K`;
    return num.toFixed(0);
  };

  const formatMarketCap = (num: number) => {
    if (num >= 1e12) return `${(num / 1e12).toFixed(2)}T`;
    if (num >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `${(num / 1e6).toFixed(2)}M`;
    return num.toFixed(0);
  };

  const formatSupportResistance = (price: number, mainPrice: number) => {
    // Используем ту же точность что и основная цена
    if (mainPrice >= 10000) {
      return price.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      });
    } else if (mainPrice >= 1) {
      return price.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 4
      });
    } else {
      return price.toFixed(6);
    }
  };

  const formatNumber = (num: number, decimals: number = 2) => {
    if (num >= 1e9) return `${(num / 1e9).toFixed(decimals)}B`;
    if (num >= 1e6) return `${(num / 1e6).toFixed(decimals)}M`;
    if (num >= 1e3) return `${(num / 1e3).toFixed(decimals)}K`;
    return num.toFixed(decimals);
  };

  const addCoin = (newCoin: string) => {
    const coin = newCoin.trim().toUpperCase();
    if (coin && !selectedCoins.includes(coin)) {
      setSelectedCoins([...selectedCoins, coin]);
    }
  };

  const removeCoin = (coinToRemove: string) => {
    setSelectedCoins(selectedCoins.filter(c => c !== coinToRemove));
  };

  if (isLoading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex flex-col items-center justify-center h-64 text-red-400">
          <AlertTriangle className="w-8 h-8 mb-2" />
          <p className="text-lg font-semibold mb-2">Ошибка загрузки данных</p>
          <p className="text-sm text-gray-400 text-center">
            Проверьте подключение к API на http://localhost:8000
          </p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Обновить страницу
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white flex items-center">
          <BarChart3 className="w-8 h-8 mr-3 text-blue-400" />
          Мониторинг монет
        </h2>
        <div className="flex items-center space-x-4 text-sm text-gray-400">
          <div className="flex items-center">
            <Clock className="w-4 h-4 mr-1" />
            Обновление каждые 5 сек
          </div>
          <div className="flex items-center">
            <div className="w-2 h-2 bg-green-400 rounded-full mr-1 animate-pulse"></div>
            Данные с BingX API
          </div>
        </div>
      </div>

      {/* Сетка монет */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {coinsData?.map((coin) => (
          <div key={coin.symbol} className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            {/* Заголовок монеты */}
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-xl font-bold text-white">{coin.symbol}</h3>
                <p className="text-gray-400">{coin.name}</p>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold text-white">
                  ${formatPrice(coin.price)}
                </p>
                <p className={`text-sm ${coin.change24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {coin.change24h >= 0 ? '+' : ''}{coin.change24h.toFixed(2)}%
                </p>
              </div>
            </div>

            {/* Основные метрики */}
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-gray-700 rounded p-3">
                <div className="flex items-center text-gray-400 text-sm mb-1">
                  <Volume2 className="w-4 h-4 mr-1" />
                  Объем 24ч
                </div>
                <p className="text-white font-semibold">${formatVolume(coin.volume24h)}</p>
              </div>
              <div className="bg-gray-700 rounded p-3">
                <div className="flex items-center text-gray-400 text-sm mb-1">
                  <DollarSign className="w-4 h-4 mr-1" />
                  Рын. кап.
                </div>
                <p className="text-white font-semibold">${formatMarketCap(coin.marketCap)}</p>
              </div>
            </div>

            {/* Технические индикаторы */}
            <div className="space-y-3 mb-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-400">RSI:</span>
                <span className={`font-semibold ${getRSIColor(coin.rsi)}`}>
                  {coin.rsi.toFixed(1)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">MACD:</span>
                <span className={`font-semibold ${coin.macd >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {coin.macd.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Поддержка:</span>
                <span className="text-blue-400 font-semibold">
                  ${formatSupportResistance(coin.support, coin.price)}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Сопротивление:</span>
                <span className="text-purple-400 font-semibold">
                  ${formatSupportResistance(coin.resistance, coin.price)}
                </span>
              </div>
            </div>

            {/* Bollinger Bands */}
            <div className="mb-4">
              <div className="text-gray-400 text-sm mb-2">Bollinger Bands:</div>
              <div className="bg-gray-700 rounded p-2">
                <div className="flex justify-between text-xs">
                  <span className="text-red-400">Верх: ${formatPrice(coin.bollinger.upper)}</span>
                  <span className="text-yellow-400">Сред: ${formatPrice(coin.bollinger.middle)}</span>
                  <span className="text-green-400">Низ: ${formatPrice(coin.bollinger.lower)}</span>
                </div>
                <div className="mt-1">
                  <span className="text-xs text-gray-400">Позиция: </span>
                  <span className={`text-xs font-semibold ${
                    coin.bollinger.position === 'upper' ? 'text-red-400' :
                    coin.bollinger.position === 'lower' ? 'text-green-400' : 'text-yellow-400'
                  }`}>
                    {coin.bollinger.position === 'upper' ? 'Верхняя' :
                     coin.bollinger.position === 'lower' ? 'Нижняя' : 'Средняя'}
                  </span>
                </div>
              </div>
            </div>

            {/* Сигналы */}
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-gray-400 text-sm">Технический:</span>
                <div className={`flex items-center ${getSignalColor(coin.signals.technical)}`}>
                  {getSignalIcon(coin.signals.technical)}
                  <span className="ml-1 font-semibold uppercase text-xs">
                    {coin.signals.technical}
                  </span>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400 text-sm">AI сигнал:</span>
                <div className={`flex items-center ${getSignalColor(coin.signals.ai)}`}>
                  {getSignalIcon(coin.signals.ai)}
                  <span className="ml-1 font-semibold uppercase text-xs">
                    {coin.signals.ai}
                  </span>
                </div>
              </div>
              <div className="flex justify-between items-center pt-2 border-t border-gray-600">
                <span className="text-white text-sm font-semibold">Итоговый:</span>
                <div className={`flex items-center ${getSignalColor(coin.signals.combined)} font-bold`}>
                  {getSignalIcon(coin.signals.combined)}
                  <span className="ml-1 uppercase text-sm">
                    {coin.signals.combined}
                  </span>
                </div>
              </div>
            </div>

            {/* Настроение рынка */}
            <div className="mt-4 pt-4 border-t border-gray-600">
              <div className="flex justify-between items-center">
                <span className="text-gray-400 text-sm">Настроение:</span>
                <div className={`flex items-center ${
                  coin.sentiment === 'bullish' ? 'text-green-400' :
                  coin.sentiment === 'bearish' ? 'text-red-400' : 'text-yellow-400'
                }`}>
                  {coin.sentiment === 'bullish' ? <TrendingUp className="w-4 h-4 mr-1" /> :
                   coin.sentiment === 'bearish' ? <TrendingDown className="w-4 h-4 mr-1" /> :
                   <Activity className="w-4 h-4 mr-1" />}
                  <span className="font-semibold capitalize">
                    {coin.sentiment === 'bullish' ? 'Бычье' :
                     coin.sentiment === 'bearish' ? 'Медвежье' : 'Нейтральное'}
                  </span>
                </div>
              </div>
            </div>

            {/* Время последнего обновления */}
            <div className="mt-3 text-xs text-gray-500 text-center">
              Обновлено: {new Date(coin.lastUpdate).toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>

      {/* Добавление новых монет */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Добавить монету для мониторинга</h3>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Например: DOGE/USDT"
            className="flex-1 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500"
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                const value = (e.target as HTMLInputElement).value.trim().toUpperCase();
                if (value) {
                  addCoin(value);
                  (e.target as HTMLInputElement).value = '';
                }
              }
            }}
          />
          <button 
            onClick={(e) => {
              const input = e.currentTarget.previousElementSibling as HTMLInputElement;
              const value = input.value.trim().toUpperCase();
              if (value) {
                addCoin(value);
                input.value = '';
              }
            }}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded transition-colors"
          >
            Добавить
          </button>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          {selectedCoins.map((coin) => (
            <span
              key={coin}
              className="bg-gray-700 text-white px-3 py-1 rounded-full text-sm flex items-center"
            >
              {coin}
              <button
                onClick={() => removeCoin(coin)}
                className="ml-2 text-gray-400 hover:text-red-400"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default CoinMonitor; 