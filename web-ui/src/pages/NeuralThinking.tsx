import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Brain, 
  Activity, 
  Zap, 
  Eye, 
  TrendingUp, 
  TrendingDown,
  Minus,
  Play,
  Pause,
  RotateCcw
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import JSONPretty from 'react-json-pretty';

interface NeuralThought {
  id: string;
  timestamp: string;
  type: 'lstm' | 'cnn' | 'combined';
  symbol: string;
  thought: string;
  confidence: number;
  data: any;
  signal?: 'buy' | 'sell' | 'hold';
}

interface ModelState {
  lstm: {
    active: boolean;
    confidence: number;
    lastThought: string;
    processing: boolean;
  };
  cnn: {
    active: boolean;
    confidence: number;
    lastThought: string;
    processing: boolean;
  };
}

const NeuralThinking: React.FC = () => {
  const [thoughts, setThoughts] = useState<NeuralThought[]>([]);
  const [isMonitoring, setIsMonitoring] = useState(true);
  const [selectedSymbol, setSelectedSymbol] = useState('BTC/USDT');
  const [modelState, setModelState] = useState<ModelState>({
    lstm: { active: true, confidence: 0, lastThought: '', processing: false },
    cnn: { active: true, confidence: 0, lastThought: '', processing: false }
  });

  // Симуляция получения размышлений ИИ
  useQuery({
    queryKey: ['neural-thinking', selectedSymbol],
    queryFn: async () => {
      const response = await fetch(`/api/v1/deep-learning/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: selectedSymbol,
          timeframe: '1h',
          periods: 100
        })
      });
      return response.json();
    },
    refetchInterval: isMonitoring ? 5000 : false,
    onSuccess: (data) => {
      if (data && !data.error) {
        generateThoughts(data);
      }
    }
  });

  const generateThoughts = (predictionData: any) => {
    const newThoughts: NeuralThought[] = [];
    
    // LSTM размышления
    if (predictionData.models?.lstm && !predictionData.models.lstm.error) {
      const lstm = predictionData.models.lstm;
      newThoughts.push({
        id: `lstm-${Date.now()}`,
        timestamp: new Date().toISOString(),
        type: 'lstm',
        symbol: selectedSymbol,
        thought: generateLSTMThought(lstm),
        confidence: lstm.confidence,
        data: lstm,
        signal: lstm.signal
      });

      setModelState(prev => ({
        ...prev,
        lstm: {
          active: true,
          confidence: lstm.confidence,
          lastThought: generateLSTMThought(lstm),
          processing: false
        }
      }));
    }

    // CNN размышления
    if (predictionData.models?.cnn && !predictionData.models.cnn.error) {
      const cnn = predictionData.models.cnn;
      newThoughts.push({
        id: `cnn-${Date.now() + 1}`,
        timestamp: new Date().toISOString(),
        type: 'cnn',
        symbol: selectedSymbol,
        thought: generateCNNThought(cnn),
        confidence: cnn.confidence,
        data: cnn
      });

      setModelState(prev => ({
        ...prev,
        cnn: {
          active: true,
          confidence: cnn.confidence,
          lastThought: generateCNNThought(cnn),
          processing: false
        }
      }));
    }

    // Комбинированное размышление
    if (predictionData.combined) {
      const combined = predictionData.combined;
      newThoughts.push({
        id: `combined-${Date.now() + 2}`,
        timestamp: new Date().toISOString(),
        type: 'combined',
        symbol: selectedSymbol,
        thought: generateCombinedThought(combined),
        confidence: combined.confidence,
        data: combined,
        signal: combined.signal
      });
    }

    setThoughts(prev => [...newThoughts, ...prev].slice(0, 50)); // Храним последние 50 мыслей
  };

  const generateLSTMThought = (lstm: any): string => {
    const thoughts = [
      `Анализирую временные ряды... Вижу паттерн с вероятностью ${(lstm.probability * 100).toFixed(1)}%`,
      `Последовательность данных указывает на ${lstm.signal === 'buy' ? 'восходящий' : lstm.signal === 'sell' ? 'нисходящий' : 'боковой'} тренд`,
      `Моя уверенность в прогнозе составляет ${(lstm.confidence * 100).toFixed(1)}%`,
      `Обрабатываю ${lstm.sequence_length || 60} временных точек для прогноза`,
      `Нейронные веса указывают на ${lstm.signal} сигнал с силой ${(lstm.probability * 100).toFixed(1)}%`
    ];
    return thoughts[Math.floor(Math.random() * thoughts.length)];
  };

  const generateCNNThought = (cnn: any): string => {
    const thoughts = [
      `Распознаю ${cnn.pattern} паттерн на графике свечей`,
      `Последняя свеча показывает ${cnn.last_candle_type} настроение рынка`,
      `Сила тренда составляет ${(cnn.trend_strength * 100).toFixed(1)}%`,
      `Визуальный анализ указывает на ${cnn.pattern} формацию`,
      `Паттерн-матчинг дает уверенность ${(cnn.confidence * 100).toFixed(1)}%`
    ];
    return thoughts[Math.floor(Math.random() * thoughts.length)];
  };

  const generateCombinedThought = (combined: any): string => {
    const thoughts = [
      `Объединяя анализ временных рядов и паттернов, рекомендую: ${combined.signal}`,
      `Итоговая уверенность после синтеза моделей: ${(combined.confidence * 100).toFixed(1)}%`,
      `Консенсус моделей указывает на ${combined.signal} с высокой точностью`,
      `Мультимодальный анализ завершен. Решение: ${combined.signal}`,
      combined.recommendation
    ];
    return thoughts[Math.floor(Math.random() * thoughts.length)];
  };

  const getSignalIcon = (signal?: string) => {
    switch (signal) {
      case 'buy': return <TrendingUp className="w-4 h-4 text-success-400" />;
      case 'sell': return <TrendingDown className="w-4 h-4 text-danger-400" />;
      default: return <Minus className="w-4 h-4 text-warning-400" />;
    }
  };

  const getSignalColor = (signal?: string) => {
    switch (signal) {
      case 'buy': return 'signal-buy';
      case 'sell': return 'signal-sell';
      default: return 'signal-hold';
    }
  };

  const getModelIcon = (type: string) => {
    switch (type) {
      case 'lstm': return <Activity className="w-5 h-5" />;
      case 'cnn': return <Eye className="w-5 h-5" />;
      default: return <Brain className="w-5 h-5" />;
    }
  };

  const getModelName = (type: string) => {
    switch (type) {
      case 'lstm': return 'LSTM (Временные ряды)';
      case 'cnn': return 'CNN (Паттерны)';
      default: return 'Комбинированный анализ';
    }
  };

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold gradient-text flex items-center space-x-3">
            <Brain className="w-8 h-8" />
            <span>Размышления ИИ</span>
          </h1>
          <p className="text-gray-400 mt-2">
            Наблюдайте за процессом принятия решений нейронной сетью в реальном времени
          </p>
        </div>

        <div className="flex items-center space-x-4">
          {/* Выбор символа */}
          <select
            value={selectedSymbol}
            onChange={(e) => setSelectedSymbol(e.target.value)}
            className="input px-3 py-2"
          >
            <option value="BTC/USDT">BTC/USDT</option>
            <option value="ETH/USDT">ETH/USDT</option>
            <option value="BNB/USDT">BNB/USDT</option>
            <option value="ADA/USDT">ADA/USDT</option>
          </select>

          {/* Управление мониторингом */}
          <button
            onClick={() => setIsMonitoring(!isMonitoring)}
            className={`btn ${isMonitoring ? 'btn-danger' : 'btn-success'} flex items-center space-x-2`}
          >
            {isMonitoring ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            <span>{isMonitoring ? 'Пауза' : 'Старт'}</span>
          </button>

          <button
            onClick={() => setThoughts([])}
            className="btn btn-secondary flex items-center space-x-2"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Очистить</span>
          </button>
        </div>
      </div>

      {/* Состояние моделей */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* LSTM модель */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-primary-600 rounded-lg">
                <Activity className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold">LSTM</h3>
                <p className="text-sm text-gray-400">Временные ряды</p>
              </div>
            </div>
            <div className={`w-3 h-3 rounded-full ${modelState.lstm.active ? 'bg-success-500 animate-pulse' : 'bg-gray-500'}`} />
          </div>
          
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Уверенность</span>
                <span>{(modelState.lstm.confidence * 100).toFixed(1)}%</span>
              </div>
              <div className="w-full bg-dark-700 rounded-full h-2">
                <div 
                  className="bg-primary-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${modelState.lstm.confidence * 100}%` }}
                />
              </div>
            </div>
            
            {modelState.lstm.lastThought && (
              <div className="text-sm text-gray-300 bg-dark-700 p-3 rounded-lg">
                "{modelState.lstm.lastThought}"
              </div>
            )}
          </div>
        </div>

        {/* CNN модель */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-success-600 rounded-lg">
                <Eye className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold">CNN</h3>
                <p className="text-sm text-gray-400">Паттерны</p>
              </div>
            </div>
            <div className={`w-3 h-3 rounded-full ${modelState.cnn.active ? 'bg-success-500 animate-pulse' : 'bg-gray-500'}`} />
          </div>
          
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Уверенность</span>
                <span>{(modelState.cnn.confidence * 100).toFixed(1)}%</span>
              </div>
              <div className="w-full bg-dark-700 rounded-full h-2">
                <div 
                  className="bg-success-500 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${modelState.cnn.confidence * 100}%` }}
                />
              </div>
            </div>
            
            {modelState.cnn.lastThought && (
              <div className="text-sm text-gray-300 bg-dark-700 p-3 rounded-lg">
                "{modelState.cnn.lastThought}"
              </div>
            )}
          </div>
        </div>

        {/* Общий статус */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-warning-600 rounded-lg">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold">Статус</h3>
                <p className="text-sm text-gray-400">Общий</p>
              </div>
            </div>
            <div className="w-3 h-3 bg-warning-500 rounded-full animate-ping" />
          </div>
          
          <div className="space-y-3">
            <div className="text-sm">
              <div className="flex justify-between mb-1">
                <span>Мыслей сгенерировано</span>
                <span className="font-mono">{thoughts.length}</span>
              </div>
              <div className="flex justify-between mb-1">
                <span>Мониторинг</span>
                <span className={isMonitoring ? 'text-success-400' : 'text-danger-400'}>
                  {isMonitoring ? 'Активен' : 'Приостановлен'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Символ</span>
                <span className="font-mono">{selectedSymbol}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Поток размышлений */}
      <div className="card">
        <div className="p-6 border-b border-dark-700">
          <h2 className="text-xl font-semibold flex items-center space-x-2">
            <Zap className="w-5 h-5 text-warning-400" />
            <span>Поток размышлений</span>
          </h2>
        </div>
        
        <div className="p-6">
          <div className="space-y-4 max-h-96 overflow-y-auto scrollbar-hide">
            <AnimatePresence>
              {thoughts.map((thought) => (
                <motion.div
                  key={thought.id}
                  initial={{ opacity: 0, y: -20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 20 }}
                  className="flex items-start space-x-4 p-4 bg-dark-700 rounded-lg"
                >
                  <div className="flex-shrink-0">
                    <div className={`p-2 rounded-lg ${
                      thought.type === 'lstm' ? 'bg-primary-600' :
                      thought.type === 'cnn' ? 'bg-success-600' : 'bg-warning-600'
                    }`}>
                      {getModelIcon(thought.type)}
                    </div>
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium">{getModelName(thought.type)}</span>
                        {thought.signal && getSignalIcon(thought.signal)}
                      </div>
                      <span className="text-xs text-gray-400">
                        {new Date(thought.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    
                    <p className="text-gray-300 mb-2">{thought.thought}</p>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <span className="text-sm text-gray-400">
                          Уверенность: {(thought.confidence * 100).toFixed(1)}%
                        </span>
                        {thought.signal && (
                          <span className={`text-sm font-medium ${getSignalColor(thought.signal)}`}>
                            {thought.signal.toUpperCase()}
                          </span>
                        )}
                      </div>
                      
                      <details className="text-xs">
                        <summary className="cursor-pointer text-gray-400 hover:text-gray-300">
                          Данные
                        </summary>
                        <div className="mt-2 p-2 bg-dark-800 rounded max-w-md overflow-auto">
                          <JSONPretty 
                            data={thought.data}
                            theme={{
                              main: 'line-height:1.3;color:#66d9ef;background:transparent;overflow:auto;',
                              error: 'line-height:1.3;color:#66d9ef;background:transparent;overflow:auto;',
                              key: 'color:#f92672;',
                              string: 'color:#a6e22e;',
                              value: 'color:#ae81ff;',
                              boolean: 'color:#ac81fe;'
                            }}
                            style={{ fontSize: '10px' }}
                          />
                        </div>
                      </details>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
            
            {thoughts.length === 0 && (
              <div className="text-center py-12 text-gray-400">
                <Brain className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Ожидание размышлений ИИ...</p>
                <p className="text-sm mt-2">
                  {isMonitoring ? 'Мониторинг активен' : 'Нажмите "Старт" для начала мониторинга'}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NeuralThinking; 