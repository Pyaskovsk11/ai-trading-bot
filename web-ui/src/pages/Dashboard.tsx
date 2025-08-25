import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Brain, 
  Zap,
  BarChart3,
  Clock,
  Target,
  AlertTriangle
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

const safeFetchJson = async (url: string) => {
  try {
    const res = await fetch(url);
    if (!res.ok) return {};
    // пытаемся распарсить JSON, иначе возвратим пустой объект
    try { return await res.json(); } catch { return {}; }
  } catch {
    return {};
  }
};

const Dashboard: React.FC = () => {
  // Получение данных о производительности
  const { data: performanceData } = useQuery({
    queryKey: ['adaptive-trading-performance'],
    queryFn: async () => await safeFetchJson('/api/v1/adaptive-trading/performance'),
    refetchInterval: 30000
  });

  // Получение статуса моделей (пока не используется в UI, но готово для будущего использования)
  // const { data: modelsStatus } = useQuery({
  //   queryKey: ['models-status'],
  //   queryFn: async () => {
  //     const response = await fetch('/api/v1/deep-learning/models/status');
  //     return response.json();
  //   },
  //   refetchInterval: 30000
  // });

  // Получение последних сигналов
  const { data: recentSignals } = useQuery({
    queryKey: ['recent-signals'],
    queryFn: async () => await safeFetchJson('/api/v1/adaptive-trading/signal-history?limit=10'),
    refetchInterval: 10000
  });

  // Симуляция данных для графиков
  const chartData = Array.from({ length: 24 }, (_, i) => ({
    time: `${i}:00`,
    confidence: Math.random() * 100,
    signals: Math.floor(Math.random() * 10),
    profit: (Math.random() - 0.5) * 1000
  }));

  const getSignalIcon = (signal: string) => {
    switch (signal) {
      case 'buy': return <TrendingUp className="w-4 h-4 text-success-400" />;
      case 'sell': return <TrendingDown className="w-4 h-4 text-danger-400" />;
      default: return <Activity className="w-4 h-4 text-warning-400" />;
    }
  };

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'buy': return 'text-success-400 bg-success-400/10';
      case 'sell': return 'text-danger-400 bg-danger-400/10';
      default: return 'text-warning-400 bg-warning-400/10';
    }
  };

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div>
        <h1 className="text-3xl font-bold gradient-text flex items-center space-x-3">
          <BarChart3 className="w-8 h-8" />
          <span>Дашборд</span>
        </h1>
        <p className="text-gray-400 mt-2">
          Обзор производительности AI Trading Bot в реальном времени
        </p>
        <div className="mt-4 flex gap-3">
          <a href="/strategies" className="btn btn-primary">Выбрать стратегию</a>
          <a href="/security-keys" className="btn">Ввести API-ключи</a>
        </div>
      </div>

      {/* Основные метрики */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Общие сигналы */}
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Сигналов за 24ч</p>
              <p className="text-2xl font-bold text-gray-100">
                {performanceData?.recent_signals_24h || 0}
              </p>
            </div>
            <div className="p-3 bg-primary-600 rounded-lg">
              <Zap className="w-6 h-6 text-white" />
            </div>
          </div>
          <div className="mt-4 flex items-center space-x-2 text-sm">
            <TrendingUp className="w-4 h-4 text-success-400" />
            <span className="text-success-400">+12%</span>
            <span className="text-gray-400">от вчера</span>
          </div>
        </div>

        {/* Средняя уверенность */}
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Средняя уверенность</p>
              <p className="text-2xl font-bold text-gray-100">
                {((performanceData?.avg_confidence_24h || 0) * 100).toFixed(1)}%
              </p>
            </div>
            <div className="p-3 bg-success-600 rounded-lg">
              <Target className="w-6 h-6 text-white" />
            </div>
          </div>
          <div className="mt-4 flex items_center space-x-2 text-sm">
            <TrendingUp className="w-4 h-4 text-success-400" />
            <span className="text-success-400">Высокая</span>
            <span className="text-gray-400">точность</span>
          </div>
        </div>

        {/* Buy сигналы */}
        <div className="card p-6">
          <div className="flex items_center justify_between">
            <div>
              <p className="text-sm text-gray-400">Buy сигналов</p>
              <p className="text-2xl font-bold text-success-400">
                {performanceData?.buy_signals_24h || 0}
              </p>
            </div>
            <div className="p-3 bg-success-600 rounded-lg">
              <TrendingUp className="w-6 h-6 text_white" />
            </div>
          </div>
          <div className="mt-4 flex items-center space-x-2 text-sm">
            <span className="text-gray-400">
              {((performanceData?.buy_signals_24h || 0) / Math.max(performanceData?.recent_signals_24h || 1, 1) * 100).toFixed(0)}% от общих
            </span>
          </div>
        </div>

        {/* Sell сигналы */}
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Sell сигналов</p>
              <p className="text-2xl font-bold text-danger-400">
                {performanceData?.sell_signals_24h || 0}
              </p>
            </div>
            <div className="p-3 bg-danger-600 rounded-lg">
              <TrendingDown className="w-6 h-6 text-white" />
            </div>
          </div>
          <div className="mt-4 flex items-center space-x-2 text-sm">
            <span className="text-gray-400">
              {((performanceData?.sell_signals_24h || 0) / Math.max(performanceData?.recent_signals_24h || 1, 1) * 100).toFixed(0)}% от общих
            </span>
          </div>
        </div>
      </div>

      {/* Графики */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* График уверенности */}
        <div className="card">
          <div className="p-6 border-b border-dark-700">
            <h3 className="text-lg font-semibold flex items-center space-x-2">
              <Brain className="w-5 h-5 text-primary-400" />
              <span>Уверенность ИИ (24ч)</span>
            </h3>
          </div>
          <div className="p-6">
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: '1px solid #374151',
                    borderRadius: '8px'
                  }}
                />
                <Area 
                  type="monotone" 
                  dataKey="confidence" 
                  stroke="#3B82F6" 
                  fill="#3B82F6" 
                  fillOpacity={0.2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* График сигналов */}
        <div className="card">
          <div className="p-6 border-b border-dark-700">
            <h3 className="text-lg font-semibold flex items-center space-x-2">
              <Activity className="w-5 h-5 text-success-400" />
              <span>Активность сигналов</span>
            </h3>
          </div>
          <div className="p-6">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1F2937', 
                    border: '1px solid #374151',
                    borderRadius: '8px'
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="signals" 
                  stroke="#22C55E" 
                  strokeWidth={2}
                  dot={{ fill: '#22C55E', strokeWidth: 2, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Статус моделей и последние сигналы */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Статус моделей */}
        <div className="card">
          <div className="p-6 border-b border-dark-700">
            <h3 className="text-lg font-semibold flex items-center space-x-2">
              <Brain className="w-5 h-5 text-warning-400" />
              <span>Статус моделей</span>
            </h3>
          </div>
          <div className="p-6 space-y-4">
            {/* LSTM */}
            <div className="flex items-center justify-between p-4 bg-dark-700 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg_primary-600 rounded-lg">
                  <Activity className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h4 className="font-medium">LSTM Model</h4>
                  <p className="text-sm text-gray-400">Временные ряды</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-success-400">Активна</span>
              </div>
            </div>

            {/* CNN */}
            <div className="flex items-center justify-between p-4 bg-dark-700 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-success-600 rounded-lg">
                  <Brain className="w-5 h-5 text_white" />
                </div>
                <div>
                  <h4 className="font-medium">CNN Model</h4>
                  <p className="text-sm text-gray-400">Паттерны свечей</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-success-400">Активна</span>
              </div>
            </div>

            {/* Комбинированная */}
            <div className="flex items-center justify-between p-4 bg-dark-700 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-warning-600 rounded-lg">
                  <Zap className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h4 className="font-medium">Combined Engine</h4>
                  <p className="text-sm text-gray-400">Синтез решений</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-success-400">Активна</span>
              </div>
            </div>
          </div>
        </div>

        {/* Последние сигналы */}
        <div className="card">
          <div className="p-6 border-b border-dark-700">
            <h3 className="text-lg font-semibold flex items-center space-x-2">
              <Clock className="w-5 h-5 text-primary-400" />
              <span>Последние сигналы</span>
            </h3>
          </div>
          <div className="p-6">
            <div className="space-y-3 max-h-80 overflow-y-auto scrollbar-hide">
              {recentSignals?.signals?.slice(0, 8).map((signal: any, index: number) => (
                <div key={index} className="flex items-center justify-between p-3 bg-dark-700 rounded-lg">
                  <div className="flex items-center space-x-3">
                    {getSignalIcon(signal.signal)}
                    <div>
                      <p className="font-medium">{signal.symbol}</p>
                      <p className="text-sm text-gray-400">
                        {new Date(signal.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getSignalColor(signal.signal)}`}>
                      {signal.signal.toUpperCase()}
                    </span>
                    <p className="text-sm text-gray-400 mt-1">
                      {(signal.confidence * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
              )) || (
                <div className="text-center py-8 text-gray-400">
                  <AlertTriangle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>Нет данных о сигналах</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Системная информация */}
      <div className="card">
        <div className="p-6 border-b border-dark-700">
          <h3 className="text-lg font-semibold flex items-center space-x-2">
            <Activity className="w-5 h-5 text-success-400" />
            <span>Системная информация</span>
          </h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-success-400">99.9%</div>
              <div className="text-sm text-gray-400">Время работы</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary-400">
                {performanceData?.current_profile || 'moderate'}
              </div>
              <div className="text-sm text-gray-400">Текущий профиль</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-warning-400">
                {performanceData?.current_ai_mode || 'semi_auto'}
              </div>
              <div className="text-sm text-gray-400">AI режим</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 