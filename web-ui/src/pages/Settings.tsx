import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Settings as SettingsIcon, 
  Save, 
  Database, 
  Shield, 
  Bell, 
  Palette,
  Send,
  Check,
  AlertTriangle,
  MessageCircle,
  Play,
  StopCircle
} from 'lucide-react';
import toast from 'react-hot-toast';

interface TradingSettings {
  profile?: string;
  ai_mode?: string;
}

interface AlertSettings {
  enabled_alerts: string[];
  whale_threshold_usd: number;
  manipulation_threshold: number;
  institutional_threshold_usd: number;
  smart_money_consensus_threshold: number;
  dedupe_window_minutes: number;
  max_alerts_per_hour: number;
  telegram_enabled: boolean;
  webhook_url?: string;
}

const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState('trading');
  const [telegramBotToken, setTelegramBotToken] = useState('');
  const [telegramChatId, setTelegramChatId] = useState('');
  const queryClient = useQueryClient();

  // Получение текущих настроек
  const { data: currentSettings } = useQuery<TradingSettings>({
    queryKey: ['adaptive-trading-settings'],
    queryFn: async () => {
      const response = await fetch('/api/v1/trading-settings/current');
      return response.json();
    }
  });

  // Получение настроек алертов
  const { data: alertSettings, isLoading: alertsLoading } = useQuery<{status: string, settings: AlertSettings, service_running: boolean}>({
    queryKey: ['alert-settings'],
    queryFn: async () => {
      const response = await fetch('/api/v1/alerts/settings');
      return response.json();
    }
  });

  // Мутация для обновления профиля
  const updateProfileMutation = useMutation(
    async (profile: string) => {
      const response = await fetch('/api/v1/trading-settings/profile/' + profile, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile })
      });
      return response.json();
    },
    {
      onSuccess: () => {
        toast.success('Профиль обновлен!');
        queryClient.invalidateQueries({ queryKey: ['adaptive-trading-settings'] });
      }
    }
  );

  // Мутация для обновления AI режима
  const updateAIModeMutation = useMutation(
    async (mode: string) => {
      const response = await fetch('/api/v1/trading-settings/mode/' + mode, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode })
      });
      return response.json();
    },
    {
      onSuccess: () => {
        toast.success('Режим торговли обновлен!');
        queryClient.invalidateQueries({ queryKey: ['adaptive-trading-settings'] });
      }
    }
  );

  // Мутация для настройки Telegram
  const configureTelegramMutation = useMutation(
    async ({ bot_token, chat_id }: { bot_token: string; chat_id: string }) => {
      const response = await fetch('/api/v1/alerts/configure-telegram', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bot_token, chat_id })
      });
      return response.json();
    },
    {
      onSuccess: () => {
        toast.success('Telegram бот настроен!');
        queryClient.invalidateQueries({ queryKey: ['alert-settings'] });
        setTelegramBotToken('');
        setTelegramChatId('');
      },
      onError: () => {
        toast.error('Ошибка настройки Telegram');
      }
    }
  );

  // Мутация для обновления настроек алертов
  const updateAlertSettingsMutation = useMutation(
    async (settings: Partial<AlertSettings>) => {
      const response = await fetch('/api/v1/alerts/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      return response.json();
    },
    {
      onSuccess: () => {
        toast.success('Настройки алертов обновлены!');
        queryClient.invalidateQueries({ queryKey: ['alert-settings'] });
      },
      onError: () => {
        toast.error('Ошибка обновления настроек');
      }
    }
  );

  // Мутация для отправки тестового алерта
  const sendTestAlertMutation = useMutation(
    async () => {
      const response = await fetch('/api/v1/alerts/test', {
        method: 'POST'
      });
      return response.json();
    },
    {
      onSuccess: () => {
        toast.success('Тестовый алерт отправлен!');
      },
      onError: () => {
        toast.error('Ошибка отправки тестового алерта');
      }
    }
  );

  // Мутация для старта/стопа сервиса алертов
  const toggleAlertServiceMutation = useMutation(
    async (action: 'start' | 'stop') => {
      const response = await fetch(`/api/v1/alerts/${action}`, {
        method: 'POST'
      });
      return response.json();
    },
    {
      onSuccess: (data, variables) => {
        toast.success(variables === 'start' ? 'Сервис алертов запущен!' : 'Сервис алертов остановлен!');
        queryClient.invalidateQueries({ queryKey: ['alert-settings'] });
      },
      onError: () => {
        toast.error('Ошибка управления сервисом');
      }
    }
  );

  // Мутации для включения/выключения торговли
  const enableTradingMutation = useMutation(
    async () => {
      const response = await fetch('/api/v1/trading-settings/enable', { method: 'POST' });
      return response.json();
    },
    {
      onSuccess: () => {
        toast.success('Торговля включена');
        queryClient.invalidateQueries({ queryKey: ['adaptive-trading-settings'] });
      },
      onError: () => toast.error('Ошибка включения торговли')
    }
  );

  const disableTradingMutation = useMutation(
    async () => {
      const response = await fetch('/api/v1/trading-settings/disable', { method: 'POST' });
      return response.json();
    },
    {
      onSuccess: () => {
        toast.success('Торговля выключена');
        queryClient.invalidateQueries({ queryKey: ['adaptive-trading-settings'] });
      },
      onError: () => toast.error('Ошибка выключения торговли')
    }
  );

  const handleToggleAlertType = (alertType: string, enabled: boolean) => {
    const currentAlerts = alertSettings?.settings?.enabled_alerts || [];
    const newAlerts = enabled 
      ? [...currentAlerts, alertType]
      : currentAlerts.filter(a => a !== alertType);
    
    updateAlertSettingsMutation.mutate({ enabled_alerts: newAlerts });
  };

  const handleUpdateThreshold = (key: keyof AlertSettings, value: number) => {
    updateAlertSettingsMutation.mutate({ [key]: value });
  };

  const tabs = [
    { id: 'trading', name: 'Торговля', icon: SettingsIcon },
    { id: 'data', name: 'Данные', icon: Database },
    { id: 'security', name: 'Безопасность', icon: Shield },
    { id: 'notifications', name: 'Уведомления', icon: Bell },
    { id: 'appearance', name: 'Внешний вид', icon: Palette },
  ];

  const alertTypes = [
    { id: 'whale_movement', name: '🐋 Движения китов', desc: 'Уведомления о крупных переводах' },
    { id: 'manipulation', name: '🚨 Манипуляции', desc: 'Обнаружение рыночных манипуляций' },
    { id: 'institutional_flow', name: '🏦 Институциональные потоки', desc: 'Движения институциональных средств' },
    { id: 'smart_money', name: '🧠 Умные деньги', desc: 'Сигналы от успешных трейдеров' },
    { id: 'trade_open', name: '💹 Открытие позиций', desc: 'Уведомления об открытых сделках' },
    { id: 'trade_close', name: '🔒 Закрытие позиций', desc: 'Уведомления о закрытых сделках' },
    { id: 'risk_alert', name: '⚠️ Риски', desc: 'Предупреждения о рисках' },
  ];

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div>
        <h1 className="text-3xl font-bold gradient-text flex items-center space-x-3">
          <SettingsIcon className="w-8 h-8" />
          <span>Настройки</span>
        </h1>
        <p className="text-gray-400 mt-2">
          Конфигурация AI Trading Bot и системных параметров
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Навигация по вкладкам */}
        <div className="lg:col-span-1">
          <div className="card p-4">
            <nav className="space-y-2">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                      activeTab === tab.id
                        ? 'bg-primary-600 text-white'
                        : 'text-gray-300 hover:bg-dark-700'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{tab.name}</span>
                  </button>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Содержимое вкладок */}
        <div className="lg:col-span-3">
          {activeTab === 'trading' && (
            <div className="space-y-6">
              {/* Профиль агрессивности */}
              <div className="card">
                <div className="p-6 border-b border-dark-700 flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold">Профиль агрессивности</h3>
                    <p className="text-gray-400 text-sm mt-1">
                      Настройка уровня риска и агрессивности торговли
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => enableTradingMutation.mutate()}
                      className="btn btn-success flex items-center gap-2"
                    >
                      <Play className="w-4 h-4" /> Включить
                    </button>
                    <button
                      onClick={() => disableTradingMutation.mutate()}
                      className="btn btn-danger flex items-center gap-2"
                    >
                      <StopCircle className="w-4 h-4" /> Выключить
                    </button>
                  </div>
                </div>
                <div className="p-6 space-y-4">
                  {['conservative', 'moderate', 'aggressive'].map((profile) => (
                    <div key={profile} className="flex items-center space-x-3">
                      <input
                        type="radio"
                        id={profile}
                        name="profile"
                        checked={currentSettings?.profile === profile}
                        onChange={() => updateProfileMutation.mutate(profile)}
                        className="w-4 h-4 text-primary-600"
                      />
                      <label htmlFor={profile} className="flex-1">
                        <div className="font-medium capitalize">{profile}</div>
                        <div className="text-sm text-gray-400">
                          {profile === 'conservative' && 'Низкий риск, высокие пороги уверенности'}
                          {profile === 'moderate' && 'Умеренный риск, сбалансированные параметры'}
                          {profile === 'aggressive' && 'Высокий риск, низкие пороги уверенности'}
                        </div>
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              {/* AI режим */}
              <div className="card">
                <div className="p-6 border-b border-dark-700">
                  <h3 className="text-lg font-semibold">AI режим</h3>
                  <p className="text-gray-400 text-sm mt-1">
                    Уровень автоматизации торговых решений
                  </p>
                </div>
                <div className="p-6 space-y-4">
                  {[
                    { id: 'manual', name: 'Ручной', desc: 'Только ручные сигналы' },
                    { id: 'semi_auto', name: 'Полуавтоматический', desc: 'Подтверждение сигналов' },
                    { id: 'full_auto', name: 'Автоматический', desc: 'Автоматическая торговля' },
                    { id: 'ai_adaptive', name: 'AI-адаптивный', desc: 'Полная автономность с ML' }
                  ].map((mode) => (
                    <div key={mode.id} className="flex items-center space-x-3">
                      <input
                        type="radio"
                        id={mode.id}
                        name="ai_mode"
                        checked={currentSettings?.ai_mode === mode.id}
                        onChange={() => updateAIModeMutation.mutate(mode.id)}
                        className="w-4 h-4 text-primary-600"
                      />
                      <label htmlFor={mode.id} className="flex-1">
                        <div className="font-medium">{mode.name}</div>
                        <div className="text-sm text-gray-400">{mode.desc}</div>
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'data' && (
            <div className="space-y-6">
              {/* Источники данных */}
              <div className="card">
                <div className="p-6 border-b border-dark-700">
                  <h3 className="text-lg font-semibold">Источники рыночных данных</h3>
                  <p className="text-gray-400 text-sm mt-1">
                    Настройка источников получения рыночной информации
                  </p>
                </div>
                <div className="p-6 space-y-4">
                  {[
                    { id: 'demo', name: 'Demo данные', desc: 'Синтетические данные для тестирования' },
                    { id: 'binance', name: 'Binance API', desc: 'Реальные данные с Binance' },
                    { id: 'bingx', name: 'BingX API', desc: 'Реальные данные с BingX' },
                    { id: 'yahoo', name: 'Yahoo Finance', desc: 'Финансовые данные Yahoo' }
                  ].map((source) => (
                    <div key={source.id} className="flex items-center space-x-3">
                      <input
                        type="radio"
                        id={source.id}
                        name="data_source"
                        className="w-4 h-4 text-primary-600"
                      />
                      <label htmlFor={source.id} className="flex-1">
                        <div className="font-medium">{source.name}</div>
                        <div className="text-sm text-gray-400">{source.desc}</div>
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              {/* Кэширование */}
              <div className="card">
                <div className="p-6 border-b border-dark-700">
                  <h3 className="text-lg font-semibold">Кэширование данных</h3>
                </div>
                <div className="p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">Время жизни кэша</div>
                      <div className="text-sm text-gray-400">Время хранения данных в кэше</div>
                    </div>
                    <select className="input">
                      <option value="300">5 минут</option>
                      <option value="600">10 минут</option>
                      <option value="1800">30 минут</option>
                      <option value="3600">1 час</option>
                    </select>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">Автоочистка кэша</div>
                      <div className="text-sm text-gray-400">Автоматическая очистка устаревших данных</div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" className="sr-only peer" defaultChecked />
                      <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="space-y-6">
              {/* API ключи */}
              <div className="card">
                <div className="p-6 border-b border-dark-700">
                  <h3 className="text-lg font-semibold">API ключи</h3>
                  <p className="text-gray-400 text-sm mt-1">
                    Настройка ключей для подключения к биржам
                  </p>
                </div>
                <div className="p-6 space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Binance API Key</label>
                    <input
                      type="password"
                      placeholder="Введите API ключ"
                      className="input w-full"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Binance Secret Key</label>
                    <input
                      type="password"
                      placeholder="Введите секретный ключ"
                      className="input w-full"
                    />
                  </div>
                  <div className="text-sm text-gray-400">
                    ⚠️ Ключи хранятся в зашифрованном виде
                  </div>
                </div>
              </div>

              {/* Безопасность */}
              <div className="card">
                <div className="p-6 border-b border-dark-700">
                  <h3 className="text-lg font-semibold">Настройки безопасности</h3>
                </div>
                <div className="p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">Двухфакторная аутентификация</div>
                      <div className="text-sm text-gray-400">Дополнительная защита аккаунта</div>
                    </div>
                    <button className="btn btn-primary">Настроить</button>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">Логирование действий</div>
                      <div className="text-sm text-gray-400">Запись всех торговых операций</div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" className="sr-only peer" defaultChecked />
                      <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="space-y-6">
              {/* Статус сервиса */}
              <div className="card">
                <div className="p-6 border-b border-dark-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-semibold">Сервис уведомлений</h3>
                      <p className="text-gray-400 text-sm mt-1">
                        Управление системой алертов и уведомлений
                      </p>
                    </div>
                    <div className="flex items-center space-x-3">
                      <div className={`flex items-center space-x-2 text-sm ${
                        alertSettings?.service_running ? 'text-success-400' : 'text-gray-400'
                      }`}>
                        <div className={`w-2 h-2 rounded-full ${
                          alertSettings?.service_running ? 'bg-success-400 animate-pulse' : 'bg-gray-400'
                        }`}></div>
                        <span>{alertSettings?.service_running ? 'Активен' : 'Остановлен'}</span>
                      </div>
                      <button
                        onClick={() => toggleAlertServiceMutation.mutate(
                          alertSettings?.service_running ? 'stop' : 'start'
                        )}
                        disabled={toggleAlertServiceMutation.isLoading}
                        className={`btn ${alertSettings?.service_running ? 'btn-danger' : 'btn-success'} flex items-center space-x-2`}
                      >
                        {alertSettings?.service_running ? <StopCircle className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                        <span>{alertSettings?.service_running ? 'Остановить' : 'Запустить'}</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Настройка Telegram */}
              <div className="card">
                <div className="p-6 border-b border-dark-700">
                  <h3 className="text-lg font-semibold flex items-center space-x-2">
                    <MessageCircle className="w-5 h-5" />
                    <span>Telegram бот</span>
                  </h3>
                  <p className="text-gray-400 text-sm mt-1">
                    Настройка Telegram бота для отправки уведомлений
                  </p>
                </div>
                <div className="p-6 space-y-4">
                  {alertSettings?.settings?.telegram_enabled ? (
                    <div className="flex items-center space-x-3 p-3 bg-success-900/20 border border-success-600/30 rounded-lg">
                      <Check className="w-5 h-5 text-success-400" />
                      <span className="text-success-400">Telegram бот настроен и активен</span>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="flex items-center space-x-3 p-3 bg-warning-900/20 border border-warning-600/30 rounded-lg">
                        <AlertTriangle className="w-5 h-5 text-warning-400" />
                        <span className="text-warning-400">Telegram бот не настроен</span>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium mb-2">Bot Token</label>
                          <input
                            type="password"
                            value={telegramBotToken}
                            onChange={(e) => setTelegramBotToken(e.target.value)}
                            placeholder="1234567890:XXXXXXXXXX"
                            className="input w-full"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium mb-2">Chat ID</label>
                          <input
                            type="text"
                            value={telegramChatId}
                            onChange={(e) => setTelegramChatId(e.target.value)}
                            placeholder="-1001234567890"
                            className="input w-full"
                          />
                        </div>
                      </div>
                      
                      <button
                        onClick={() => configureTelegramMutation.mutate({
                          bot_token: telegramBotToken,
                          chat_id: telegramChatId
                        })}
                        disabled={!telegramBotToken || !telegramChatId || configureTelegramMutation.isLoading}
                        className="btn btn-primary"
                      >
                        Настроить Telegram
                      </button>
                    </div>
                  )}
                  
                  {alertSettings?.settings?.telegram_enabled && (
                    <div className="flex space-x-3">
                      <button
                        onClick={() => sendTestAlertMutation.mutate()}
                        disabled={sendTestAlertMutation.isLoading}
                        className="btn btn-secondary flex items-center space-x-2"
                      >
                        <Send className="w-4 h-4" />
                        <span>Тестовый алерт</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Типы алертов */}
              <div className="card">
                <div className="p-6 border-b border-dark-700">
                  <h3 className="text-lg font-semibold">Типы уведомлений</h3>
                  <p className="text-gray-400 text-sm mt-1">
                    Выберите типы событий для уведомлений
                  </p>
                </div>
                <div className="p-6 space-y-4">
                  {alertTypes.map((alertType) => (
                    <div key={alertType.id} className="flex items-center justify-between">
                      <div>
                        <div className="font-medium">{alertType.name}</div>
                        <div className="text-sm text-gray-400">{alertType.desc}</div>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input 
                          type="checkbox" 
                          className="sr-only peer" 
                          checked={alertSettings?.settings?.enabled_alerts?.includes(alertType.id) || false}
                          onChange={(e) => handleToggleAlertType(alertType.id, e.target.checked)}
                        />
                        <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              {/* Пороги уведомлений */}
              <div className="card">
                <div className="p-6 border-b border-dark-700">
                  <h3 className="text-lg font-semibold">Пороги уведомлений</h3>
                  <p className="text-gray-400 text-sm mt-1">
                    Настройка порогов срабатывания алертов
                  </p>
                </div>
                <div className="p-6 space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-medium mb-2">Порог китов (USD)</label>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm text-gray-400">$</span>
                        <input
                          type="number"
                          value={alertSettings?.settings?.whale_threshold_usd || 1000000}
                          onChange={(e) => handleUpdateThreshold('whale_threshold_usd', Number(e.target.value))}
                          className="input flex-1"
                          min="100000"
                          step="100000"
                        />
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium mb-2">Порог манипуляций</label>
                      <div className="flex items-center space-x-2">
                        <input
                          type="range"
                          min="0.1"
                          max="1.0"
                          step="0.1"
                          value={alertSettings?.settings?.manipulation_threshold || 0.3}
                          onChange={(e) => handleUpdateThreshold('manipulation_threshold', Number(e.target.value))}
                          className="flex-1"
                        />
                        <span className="text-sm font-medium w-12">
                          {Math.round((alertSettings?.settings?.manipulation_threshold || 0.3) * 100)}%
                        </span>
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium mb-2">Институциональные потоки (USD)</label>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm text-gray-400">$</span>
                        <input
                          type="number"
                          value={alertSettings?.settings?.institutional_threshold_usd || 5000000}
                          onChange={(e) => handleUpdateThreshold('institutional_threshold_usd', Number(e.target.value))}
                          className="input flex-1"
                          min="1000000"
                          step="1000000"
                        />
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium mb-2">Консенсус умных денег</label>
                      <div className="flex items-center space-x-2">
                        <input
                          type="range"
                          min="0.5"
                          max="1.0"
                          step="0.1"
                          value={alertSettings?.settings?.smart_money_consensus_threshold || 0.7}
                          onChange={(e) => handleUpdateThreshold('smart_money_consensus_threshold', Number(e.target.value))}
                          className="flex-1"
                        />
                        <span className="text-sm font-medium w-12">
                          {Math.round((alertSettings?.settings?.smart_money_consensus_threshold || 0.7) * 100)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Настройки частоты */}
              <div className="card">
                <div className="p-6 border-b border-dark-700">
                  <h3 className="text-lg font-semibold">Частота уведомлений</h3>
                  <p className="text-gray-400 text-sm mt-1">
                    Контроль частоты и дедупликации алертов
                  </p>
                </div>
                <div className="p-6 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">Окно дедупликации (минуты)</label>
                      <input
                        type="number"
                        value={alertSettings?.settings?.dedupe_window_minutes || 15}
                        onChange={(e) => handleUpdateThreshold('dedupe_window_minutes', Number(e.target.value))}
                        className="input w-full"
                        min="5"
                        max="60"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium mb-2">Максимум алертов в час</label>
                      <input
                        type="number"
                        value={alertSettings?.settings?.max_alerts_per_hour || 10}
                        onChange={(e) => handleUpdateThreshold('max_alerts_per_hour', Number(e.target.value))}
                        className="input w-full"
                        min="1"
                        max="50"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'appearance' && (
            <div className="space-y-6">
              {/* Внешний вид */}
              <div className="card">
                <div className="p-6 border-b border-dark-700">
                  <h3 className="text-lg font-semibold">Тема интерфейса</h3>
                </div>
                <div className="p-6 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 border border-dark-600 rounded-lg cursor-pointer hover:border-primary-500 transition-colors">
                      <div className="w-full h-20 bg-dark-800 rounded mb-3"></div>
                      <div className="font-medium">Темная тема</div>
                      <div className="text-sm text-gray-400">Текущая тема</div>
                    </div>
                    <div className="p-4 border border-dark-600 rounded-lg cursor-pointer hover:border-primary-500 transition-colors opacity-50">
                      <div className="w-full h-20 bg-gray-200 rounded mb-3"></div>
                      <div className="font-medium">Светлая тема</div>
                      <div className="text-sm text-gray-400">Скоро доступна</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Настройки дисплея */}
              <div className="card">
                <div className="p-6 border-b border-dark-700">
                  <h3 className="text-lg font-semibold">Настройки дисплея</h3>
                </div>
                <div className="p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">Анимации</div>
                      <div className="text-sm text-gray-400">Плавные переходы и эффекты</div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" className="sr-only peer" defaultChecked />
                      <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                    </label>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">Компактный режим</div>
                      <div className="text-sm text-gray-400">Уменьшенные отступы и размеры</div>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input type="checkbox" className="sr-only peer" />
                      <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Кнопка сохранения */}
          <div className="flex justify-end">
            <button className="btn btn-primary flex items-center space-x-2">
              <Save className="w-4 h-4" />
              <span>Сохранить настройки</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings; 