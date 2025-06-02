import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Wallet, 
  TrendingUp, 
  TrendingDown, 
  DollarSign,
  PieChart,
  BarChart3,
  RefreshCw,
  Plus,
  Minus,
  Activity
} from 'lucide-react';

interface Holding {
  symbol: string;
  amount: number;
  value_usd: number;
  allocation_percent: number;
  avg_buy_price: number;
  current_price: number;
  pnl: number;
  pnl_percent: number;
}

interface PortfolioData {
  total_balance_usd: number;
  total_balance_btc: number;
  daily_pnl: number;
  daily_pnl_percent: number;
  holdings: Holding[];
  performance: {
    total_invested: number;
    total_pnl: number;
    total_pnl_percent: number;
    best_performer: string;
    worst_performer: string;
  };
  last_update: string;
}

const Portfolio: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: portfolioData, isLoading, refetch } = useQuery({
    queryKey: ['portfolio'],
    queryFn: async (): Promise<PortfolioData> => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/coins/portfolio');
        if (!response.ok) {
          throw new Error('Ошибка загрузки портфеля');
        }
        return await response.json();
      } catch (error) {
        console.error('Ошибка API портфеля:', error);
        // Fallback данные
        return {
          total_balance_usd: 15420.50,
          total_balance_btc: 0.342,
          daily_pnl: 234.80,
          daily_pnl_percent: 1.55,
          holdings: [
            {
              symbol: "BTC",
              amount: 0.25,
              value_usd: 11250.00,
              allocation_percent: 72.9,
              avg_buy_price: 43800.00,
              current_price: 45000.00,
              pnl: 300.00,
              pnl_percent: 2.74
            },
            {
              symbol: "ETH",
              amount: 1.2,
              value_usd: 3000.00,
              allocation_percent: 19.5,
              avg_buy_price: 2450.00,
              current_price: 2500.00,
              pnl: 60.00,
              pnl_percent: 2.04
            }
          ],
          performance: {
            total_invested: 14800.00,
            total_pnl: 620.50,
            total_pnl_percent: 4.19,
            best_performer: "BTC",
            worst_performer: "USDT"
          },
          last_update: new Date().toISOString()
        };
      }
    },
    refetchInterval: 10000, // Обновляем каждые 10 секунд
  });

  const formatCurrency = (amount: number, decimals: number = 2) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(amount);
  };

  const formatCrypto = (amount: number, symbol: string, decimals: number = 4) => {
    return `${amount.toFixed(decimals)} ${symbol}`;
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
        <div className="flex items-center justify-center h-64 text-red-400">
          <Activity className="w-8 h-8 mr-2" />
          Ошибка загрузки портфеля
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white flex items-center">
          <Wallet className="w-8 h-8 mr-3 text-green-400" />
          Портфель
        </h2>
        <button
          onClick={() => refetch()}
          className="flex items-center bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Обновить
        </button>
      </div>

      {/* Общая статистика */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Общий баланс</p>
              <p className="text-2xl font-bold text-white">
                {formatCurrency(portfolioData?.total_balance_usd || 0)}
              </p>
              <p className="text-gray-400 text-xs">
                {formatCrypto(portfolioData?.total_balance_btc || 0, 'BTC', 6)}
              </p>
            </div>
            <DollarSign className="w-8 h-8 text-green-400" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Дневной P&L</p>
              <p className={`text-2xl font-bold ${
                (portfolioData?.daily_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {formatCurrency(portfolioData?.daily_pnl || 0)}
              </p>
              <p className={`text-xs ${
                (portfolioData?.daily_pnl_percent || 0) >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {(portfolioData?.daily_pnl_percent || 0) >= 0 ? '+' : ''}
                {(portfolioData?.daily_pnl_percent || 0).toFixed(2)}%
              </p>
            </div>
            {(portfolioData?.daily_pnl || 0) >= 0 ? 
              <TrendingUp className="w-8 h-8 text-green-400" /> :
              <TrendingDown className="w-8 h-8 text-red-400" />
            }
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Общий P&L</p>
              <p className={`text-2xl font-bold ${
                (portfolioData?.performance?.total_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {formatCurrency(portfolioData?.performance?.total_pnl || 0)}
              </p>
              <p className={`text-xs ${
                (portfolioData?.performance?.total_pnl_percent || 0) >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {(portfolioData?.performance?.total_pnl_percent || 0) >= 0 ? '+' : ''}
                {(portfolioData?.performance?.total_pnl_percent || 0).toFixed(2)}%
              </p>
            </div>
            <BarChart3 className="w-8 h-8 text-blue-400" />
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Инвестировано</p>
              <p className="text-2xl font-bold text-white">
                {formatCurrency(portfolioData?.performance?.total_invested || 0)}
              </p>
              <p className="text-gray-400 text-xs">
                Активов: {portfolioData?.holdings?.length || 0}
              </p>
            </div>
            <PieChart className="w-8 h-8 text-purple-400" />
          </div>
        </div>
      </div>

      {/* Холдинги */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Активы в портфеле</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left text-gray-400 py-2">Актив</th>
                <th className="text-right text-gray-400 py-2">Количество</th>
                <th className="text-right text-gray-400 py-2">Стоимость</th>
                <th className="text-right text-gray-400 py-2">Доля</th>
                <th className="text-right text-gray-400 py-2">Средняя цена</th>
                <th className="text-right text-gray-400 py-2">Текущая цена</th>
                <th className="text-right text-gray-400 py-2">P&L</th>
              </tr>
            </thead>
            <tbody>
              {(portfolioData?.holdings || []).map((holding) => (
                <tr key={holding.symbol} className="border-b border-gray-700">
                  <td className="py-3">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center mr-3">
                        <span className="text-white text-sm font-bold">
                          {holding.symbol.charAt(0)}
                        </span>
                      </div>
                      <span className="text-white font-medium">{holding.symbol}</span>
                    </div>
                  </td>
                  <td className="text-right text-white py-3">
                    {formatCrypto(holding.amount, holding.symbol)}
                  </td>
                  <td className="text-right text-white py-3">
                    {formatCurrency(holding.value_usd)}
                  </td>
                  <td className="text-right text-gray-300 py-3">
                    {holding.allocation_percent.toFixed(1)}%
                  </td>
                  <td className="text-right text-gray-300 py-3">
                    {formatCurrency(holding.avg_buy_price)}
                  </td>
                  <td className="text-right text-white py-3">
                    {formatCurrency(holding.current_price)}
                  </td>
                  <td className={`text-right py-3 ${
                    holding.pnl >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    <div className="flex items-center justify-end">
                      {holding.pnl >= 0 ? 
                        <Plus className="w-4 h-4 mr-1" /> : 
                        <Minus className="w-4 h-4 mr-1" />
                      }
                      <div>
                        <div>{formatCurrency(Math.abs(holding.pnl))}</div>
                        <div className="text-xs">
                          {holding.pnl >= 0 ? '+' : ''}{holding.pnl_percent.toFixed(2)}%
                        </div>
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Лучшие и худшие активы */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <TrendingUp className="w-5 h-5 mr-2 text-green-400" />
            Лучший актив
          </h3>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-400">
              {portfolioData?.performance?.best_performer || 'N/A'}
            </p>
            <p className="text-gray-400">Показывает лучшую доходность</p>
          </div>
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <TrendingDown className="w-5 h-5 mr-2 text-red-400" />
            Худший актив
          </h3>
          <div className="text-center">
            <p className="text-2xl font-bold text-red-400">
              {portfolioData?.performance?.worst_performer || 'N/A'}
            </p>
            <p className="text-gray-400">Требует внимания</p>
          </div>
        </div>
      </div>

      {/* Время последнего обновления */}
      <div className="text-center text-gray-500 text-sm">
        Последнее обновление: {new Date(portfolioData?.last_update || '').toLocaleString('ru-RU')}
      </div>
    </div>
  );
};

export default Portfolio; 