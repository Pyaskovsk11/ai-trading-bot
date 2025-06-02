import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Filter, 
  Download, 
  RefreshCw, 
  DollarSign,
  Clock,
  Target,
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react';
import { motion } from 'framer-motion';

const TradingDeals: React.FC = () => {
  const [filter, setFilter] = useState('all');
  const [viewMode, setViewMode] = useState('positions'); // 'positions' или 'history'

  // Получение данных о портфеле
  const { data: portfolio, refetch: refetchPortfolio, isLoading: portfolioLoading } = useQuery({
    queryKey: ['portfolio'],
    queryFn: async () => {
      const response = await fetch('/api/v1/trading/portfolio');
      return response.json();
    },
    refetchInterval: 5000
  });

  // Получение данных о производительности
  const { data: performance, refetch: refetchPerformance, isLoading: performanceLoading } = useQuery({
    queryKey: ['trading-performance'],
    queryFn: async () => {
      const response = await fetch('/api/v1/trading/performance');
      return response.json();
    },
    refetchInterval: 10000
  });

  const refreshAll = () => {
    refetchPortfolio();
    refetchPerformance();
  };

  const isLoading = portfolioLoading || performanceLoading;

  const getPositionIcon = (side: string) => {
    switch (side.toLowerCase()) {
      case 'long': 
      case 'buy': 
        return <TrendingUp className="w-5 h-5 text-success-400" />;
      case 'short': 
      case 'sell': 
        return <TrendingDown className="w-5 h-5 text-danger-400" />;
      default: 
        return <Activity className="w-5 h-5 text-warning-400" />;
    }
  };

  const getPositionColor = (side: string) => {
    switch (side.toLowerCase()) {
      case 'long': 
      case 'buy': 
        return 'bg-success-600 text-white';
      case 'short': 
      case 'sell': 
        return 'bg-danger-600 text-white';
      default: 
        return 'bg-warning-600 text-white';
    }
  };

  const getPnLColor = (pnl: number) => {
    if (pnl > 0) return 'text-success-400';
    if (pnl < 0) return 'text-danger-400';
    return 'text-gray-400';
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  const getTradeStatusIcon = (reason: string) => {
    switch (reason) {
      case 'TAKE_PROFIT':
        return <CheckCircle className="w-4 h-4 text-success-400" />;
      case 'STOP_LOSS':
        return <XCircle className="w-4 h-4 text-danger-400" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-warning-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold gradient-text flex items-center space-x-3">
            <DollarSign className="w-8 h-8" />
            <span>Сделки</span>
          </h1>
          <p className="text-gray-400 mt-2">
            Текущие позиции и история торговых операций
          </p>
        </div>

        <div className="flex items-center space-x-4">
          <button
            onClick={refreshAll}
            disabled={isLoading}
            className="btn btn-secondary flex items-center space-x-2"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Обновить</span>
          </button>
          
          <button className="btn btn-primary flex items-center space-x-2">
            <Download className="w-4 h-4" />
            <span>Экспорт</span>
          </button>
        </div>
      </div>

      {/* Статистика портфеля */}
      {portfolio?.portfolio_stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Общий баланс</p>
                <p className="text-2xl font-bold">
                  {formatCurrency(portfolio.portfolio_stats.current_balance)}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-primary-400" />
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Нереализованная P&L</p>
                <p className={`text-2xl font-bold ${getPnLColor(portfolio.portfolio_stats.unrealized_pnl)}`}>
                  {formatCurrency(portfolio.portfolio_stats.unrealized_pnl)}
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-success-400" />
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Активные позиции</p>
                <p className="text-2xl font-bold">
                  {portfolio.portfolio_stats.active_positions}
                </p>
              </div>
              <Activity className="w-8 h-8 text-warning-400" />
            </div>
          </div>

          <div className="card p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Общая P&L</p>
                <p className={`text-2xl font-bold ${getPnLColor(portfolio.portfolio_stats.total_pnl)}`}>
                  {formatPercentage(portfolio.portfolio_stats.total_pnl_percent)}
                </p>
              </div>
              <Target className="w-8 h-8 text-primary-400" />
            </div>
          </div>
        </div>
      )}

      {/* Переключатель режимов */}
      <div className="card p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex bg-dark-800 rounded-lg p-1">
              <button
                onClick={() => setViewMode('positions')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'positions' 
                    ? 'bg-primary-600 text-white' 
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                Текущие позиции
              </button>
              <button
                onClick={() => setViewMode('history')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  viewMode === 'history' 
                    ? 'bg-primary-600 text-white' 
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                История сделок
              </button>
            </div>

            {viewMode === 'history' && (
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="input px-3 py-2"
              >
                <option value="all">Все сделки</option>
                <option value="profitable">Прибыльные</option>
                <option value="loss">Убыточные</option>
              </select>
            )}
          </div>

          <div className="text-sm text-gray-400">
            {viewMode === 'positions' 
              ? `Активных: ${portfolio?.active_positions?.length || 0}` 
              : `Сделок: ${performance?.performance_summary?.total_trades || 0}`
            }
          </div>
        </div>
      </div>

      {/* Текущие позиции */}
      {viewMode === 'positions' && (
        <div className="card">
          <div className="p-6 border-b border-dark-700">
            <h2 className="text-xl font-semibold">Активные позиции</h2>
          </div>
          
          <div className="divide-y divide-dark-700">
            {portfolio?.active_positions?.map((position: any, index: number) => (
              <motion.div
                key={position.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="p-6 hover:bg-dark-700/50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      {getPositionIcon(position.side)}
                    </div>
                    
                    <div>
                      <div className="flex items-center space-x-3">
                        <h3 className="font-semibold text-lg">{position.symbol}</h3>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getPositionColor(position.side)}`}>
                          {position.side}
                        </span>
                      </div>
                      <p className="text-gray-400 text-sm mt-1">
                        Открыта: {new Date(position.entry_time).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <div className="text-right">
                    <div className={`text-lg font-semibold ${getPnLColor(position.unrealized_pnl)}`}>
                      {formatCurrency(position.unrealized_pnl)}
                    </div>
                    <div className={`text-sm ${getPnLColor(position.pnl_percent)}`}>
                      {formatPercentage(position.pnl_percent)}
                    </div>
                  </div>
                </div>

                <div className="mt-4 p-4 bg-dark-800 rounded-lg">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-400">Цена входа:</span>
                      <span className="ml-2 font-medium">{formatCurrency(position.entry_price)}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Текущая цена:</span>
                      <span className="ml-2 font-medium">{formatCurrency(position.current_price)}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Количество:</span>
                      <span className="ml-2 font-medium">{position.quantity}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Stop Loss:</span>
                      <span className="ml-2 font-medium">{position.stop_loss ? formatCurrency(position.stop_loss) : 'Не установлен'}</span>
                    </div>
                  </div>
                  
                  {position.take_profit && (
                    <div className="mt-3 text-sm">
                      <span className="text-gray-400">Take Profit: </span>
                      <span className="text-success-400 font-medium">{formatCurrency(position.take_profit)}</span>
                    </div>
                  )}
                </div>
              </motion.div>
            )) || []}
            
            {(!portfolio?.active_positions || portfolio.active_positions.length === 0) && (
              <div className="p-12 text-center text-gray-400">
                <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Нет активных позиций</p>
                <p className="text-sm mt-2">Открытые позиции будут отображаться здесь</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* История сделок */}
      {viewMode === 'history' && (
        <div className="card">
          <div className="p-6 border-b border-dark-700">
            <h2 className="text-xl font-semibold">История сделок</h2>
          </div>
          
          <div className="divide-y divide-dark-700">
            {portfolio?.recent_trades?.map((trade: any, index: number) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className="p-6 hover:bg-dark-700/50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      {trade.type === 'CLOSE' ? getTradeStatusIcon(trade.reason) : getPositionIcon(trade.side)}
                    </div>
                    
                    <div>
                      <div className="flex items-center space-x-3">
                        <h3 className="font-semibold text-lg">{trade.symbol}</h3>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getPositionColor(trade.side)}`}>
                          {trade.side}
                        </span>
                        <span className="px-2 py-1 bg-dark-700 text-xs rounded">
                          {trade.type}
                        </span>
                      </div>
                      <p className="text-gray-400 text-sm mt-1">
                        {new Date(trade.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <div className="text-right">
                    {trade.realized_pnl !== undefined && (
                      <>
                        <div className={`text-lg font-semibold ${getPnLColor(trade.realized_pnl)}`}>
                          {formatCurrency(trade.realized_pnl)}
                        </div>
                        <div className={`text-sm ${getPnLColor(trade.pnl_percent)}`}>
                          {formatPercentage(trade.pnl_percent)}
                        </div>
                      </>
                    )}
                  </div>
                </div>

                <div className="mt-4 p-4 bg-dark-800 rounded-lg">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-400">Цена:</span>
                      <span className="ml-2 font-medium">
                        {trade.close_price ? formatCurrency(trade.close_price) : formatCurrency(trade.price)}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-400">Количество:</span>
                      <span className="ml-2 font-medium">{trade.quantity}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Стоимость:</span>
                      <span className="ml-2 font-medium">{formatCurrency(trade.value || trade.quantity * (trade.close_price || trade.price))}</span>
                    </div>
                    {trade.hold_time_minutes && (
                      <div>
                        <span className="text-gray-400">Время удержания:</span>
                        <span className="ml-2 font-medium">{Math.round(trade.hold_time_minutes)} мин</span>
                      </div>
                    )}
                  </div>
                  
                  {trade.reason && (
                    <div className="mt-3 text-sm">
                      <span className="text-gray-400">Причина закрытия: </span>
                      <span className="text-gray-200 font-medium">{trade.reason}</span>
                    </div>
                  )}
                </div>
              </motion.div>
            )) || []}
            
            {(!portfolio?.recent_trades || portfolio.recent_trades.length === 0) && (
              <div className="p-12 text-center text-gray-400">
                <Clock className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Нет истории сделок</p>
                <p className="text-sm mt-2">Завершённые сделки будут отображаться здесь</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default TradingDeals; 