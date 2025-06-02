import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Cpu, Play, Settings, Download, Upload, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';

const ModelManagement: React.FC = () => {
  const [trainingParams, setTrainingParams] = useState({
    symbol: 'BTC/USDT',
    timeframe: '1h',
    epochs: 50,
    days_back: 365
  });

  const queryClient = useQueryClient();

  // Получение статуса моделей
  const { data: modelsStatus } = useQuery({
    queryKey: ['models-status'],
    queryFn: async () => {
      const response = await fetch('/api/v1/deep-learning/models/status');
      return response.json();
    },
    refetchInterval: 30000
  });

  // Мутация для обучения моделей
  const trainModelMutation = useMutation(
    async (params: typeof trainingParams) => {
      const response = await fetch('/api/v1/deep-learning/train', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      });
      return response.json();
    },
    {
      onSuccess: (data) => {
        if (data.status === 'success') {
          toast.success('Модель успешно обучена!');
          queryClient.invalidateQueries({ queryKey: ['models-status'] });
        } else {
          toast.error(`Ошибка обучения: ${data.message}`);
        }
      },
      onError: () => {
        toast.error('Ошибка при обучении модели');
      }
    }
  );

  // Мутация для обновления весов
  const updateWeightsMutation = useMutation(
    async (weights: { lstm_weight: number; cnn_weight: number }) => {
      const response = await fetch('/api/v1/deep-learning/models/weights', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(weights)
      });
      return response.json();
    },
    {
      onSuccess: () => {
        toast.success('Веса моделей обновлены!');
        queryClient.invalidateQueries({ queryKey: ['models-status'] });
      },
      onError: () => {
        toast.error('Ошибка при обновлении весов');
      }
    }
  );

  const handleTrainModel = () => {
    trainModelMutation.mutate(trainingParams);
  };

  const handleUpdateWeights = (lstmWeight: number, cnnWeight: number) => {
    updateWeightsMutation.mutate({
      lstm_weight: lstmWeight,
      cnn_weight: cnnWeight
    });
  };

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div>
        <h1 className="text-3xl font-bold gradient-text flex items-center space-x-3">
          <Cpu className="w-8 h-8" />
          <span>Управление моделями</span>
        </h1>
        <p className="text-gray-400 mt-2">
          Обучение, настройка и мониторинг AI моделей
        </p>
      </div>

      {/* Статус моделей */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* LSTM модель */}
        <div className="card">
          <div className="p-6 border-b border-dark-700">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold flex items-center space-x-2">
                <div className="p-2 bg-primary-600 rounded-lg">
                  <Cpu className="w-5 h-5 text-white" />
                </div>
                <span>LSTM Model</span>
              </h3>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-success-400">Активна</span>
              </div>
            </div>
          </div>
          
          <div className="p-6 space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-400">Статус:</span>
                <span className="ml-2 font-medium text-success-400">Обучена</span>
              </div>
              <div>
                <span className="text-gray-400">Точность:</span>
                <span className="ml-2 font-medium">87.3%</span>
              </div>
              <div>
                <span className="text-gray-400">Последнее обучение:</span>
                <span className="ml-2 font-medium">2 часа назад</span>
              </div>
              <div>
                <span className="text-gray-400">Эпохи:</span>
                <span className="ml-2 font-medium">50</span>
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Вес в ансамбле</span>
                <span>{((modelsStatus?.models?.weights?.lstm || 0.6) * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-dark-700 rounded-full h-2">
                <div 
                  className="bg-primary-500 h-2 rounded-full"
                  style={{ width: `${(modelsStatus?.models?.weights?.lstm || 0.6) * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* CNN модель */}
        <div className="card">
          <div className="p-6 border-b border-dark-700">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold flex items-center space-x-2">
                <div className="p-2 bg-success-600 rounded-lg">
                  <Cpu className="w-5 h-5 text-white" />
                </div>
                <span>CNN Model</span>
              </h3>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-success-400">Активна</span>
              </div>
            </div>
          </div>
          
          <div className="p-6 space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-400">Статус:</span>
                <span className="ml-2 font-medium text-success-400">Обучена</span>
              </div>
              <div>
                <span className="text-gray-400">Точность:</span>
                <span className="ml-2 font-medium">82.1%</span>
              </div>
              <div>
                <span className="text-gray-400">Последнее обучение:</span>
                <span className="ml-2 font-medium">2 часа назад</span>
              </div>
              <div>
                <span className="text-gray-400">Эпохи:</span>
                <span className="ml-2 font-medium">50</span>
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Вес в ансамбле</span>
                <span>{((modelsStatus?.models?.weights?.cnn || 0.4) * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-dark-700 rounded-full h-2">
                <div 
                  className="bg-success-500 h-2 rounded-full"
                  style={{ width: `${(modelsStatus?.models?.weights?.cnn || 0.4) * 100}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Обучение моделей */}
      <div className="card">
        <div className="p-6 border-b border-dark-700">
          <h3 className="text-lg font-semibold flex items-center space-x-2">
            <Play className="w-5 h-5 text-primary-400" />
            <span>Обучение моделей</span>
          </h3>
        </div>
        
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium mb-2">Символ</label>
              <select
                value={trainingParams.symbol}
                onChange={(e) => setTrainingParams(prev => ({ ...prev, symbol: e.target.value }))}
                className="input w-full"
              >
                <option value="BTC/USDT">BTC/USDT</option>
                <option value="ETH/USDT">ETH/USDT</option>
                <option value="BNB/USDT">BNB/USDT</option>
                <option value="ADA/USDT">ADA/USDT</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Таймфрейм</label>
              <select
                value={trainingParams.timeframe}
                onChange={(e) => setTrainingParams(prev => ({ ...prev, timeframe: e.target.value }))}
                className="input w-full"
              >
                <option value="1h">1 час</option>
                <option value="4h">4 часа</option>
                <option value="1d">1 день</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Эпохи</label>
              <input
                type="number"
                value={trainingParams.epochs}
                onChange={(e) => setTrainingParams(prev => ({ ...prev, epochs: parseInt(e.target.value) }))}
                className="input w-full"
                min="1"
                max="200"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Дней истории</label>
              <input
                type="number"
                value={trainingParams.days_back}
                onChange={(e) => setTrainingParams(prev => ({ ...prev, days_back: parseInt(e.target.value) }))}
                className="input w-full"
                min="30"
                max="1000"
              />
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <button
              onClick={handleTrainModel}
              disabled={trainModelMutation.isLoading}
              className="btn btn-primary flex items-center space-x-2"
            >
              {trainModelMutation.isLoading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              <span>
                {trainModelMutation.isLoading ? 'Обучение...' : 'Начать обучение'}
              </span>
            </button>
            
            <div className="text-sm text-gray-400">
              Обучение может занять несколько минут
            </div>
          </div>
        </div>
      </div>

      {/* Настройка весов */}
      <div className="card">
        <div className="p-6 border-b border-dark-700">
          <h3 className="text-lg font-semibold flex items-center space-x-2">
            <Settings className="w-5 h-5 text-warning-400" />
            <span>Настройка весов ансамбля</span>
          </h3>
        </div>
        
        <div className="p-6">
          <div className="space-y-6">
            <div>
              <div className="flex justify-between mb-2">
                <label className="text-sm font-medium">LSTM вес</label>
                <span className="text-sm text-gray-400">
                  {((modelsStatus?.models?.weights?.lstm || 0.6) * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                defaultValue={modelsStatus?.models?.weights?.lstm || 0.6}
                className="w-full"
                onChange={(e) => {
                  const lstmWeight = parseFloat(e.target.value);
                  const cnnWeight = 1 - lstmWeight;
                  handleUpdateWeights(lstmWeight, cnnWeight);
                }}
              />
            </div>
            
            <div>
              <div className="flex justify-between mb-2">
                <label className="text-sm font-medium">CNN вес</label>
                <span className="text-sm text-gray-400">
                  {((modelsStatus?.models?.weights?.cnn || 0.4) * 100).toFixed(0)}%
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                defaultValue={modelsStatus?.models?.weights?.cnn || 0.4}
                className="w-full"
                onChange={(e) => {
                  const cnnWeight = parseFloat(e.target.value);
                  const lstmWeight = 1 - cnnWeight;
                  handleUpdateWeights(lstmWeight, cnnWeight);
                }}
              />
            </div>
            
            <div className="text-sm text-gray-400">
              Веса автоматически нормализуются до суммы 100%
            </div>
          </div>
        </div>
      </div>

      {/* Действия с моделями */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card p-6 text-center">
          <Download className="w-8 h-8 mx-auto mb-4 text-primary-400" />
          <h3 className="font-semibold mb-2">Экспорт моделей</h3>
          <p className="text-sm text-gray-400 mb-4">
            Сохранить обученные модели на диск
          </p>
          <button className="btn btn-primary w-full">
            Экспортировать
          </button>
        </div>
        
        <div className="card p-6 text-center">
          <Upload className="w-8 h-8 mx-auto mb-4 text-success-400" />
          <h3 className="font-semibold mb-2">Импорт моделей</h3>
          <p className="text-sm text-gray-400 mb-4">
            Загрузить предобученные модели
          </p>
          <button className="btn btn-success w-full">
            Импортировать
          </button>
        </div>
        
        <div className="card p-6 text-center">
          <RefreshCw className="w-8 h-8 mx-auto mb-4 text-warning-400" />
          <h3 className="font-semibold mb-2">Сброс моделей</h3>
          <p className="text-sm text-gray-400 mb-4">
            Сбросить модели к начальному состоянию
          </p>
          <button className="btn btn-danger w-full">
            Сбросить
          </button>
        </div>
      </div>
    </div>
  );
};

export default ModelManagement; 