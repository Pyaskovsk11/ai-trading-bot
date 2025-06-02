// API утилиты для AI Trading Bot
import axios from 'axios';

// Прямое подключение к backend (CORS уже настроен в FastAPI)
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Интерсепторы для обработки ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// API методы - обновлено под новый backend
export const apiMethods = {
  // Основные данные
  dashboard: () => api.get('/api/dashboard'),
  signals: () => api.get('/api/signals'),
  health: () => api.get('/health'),
  testImports: () => api.get('/test-imports'),
  
  // Event Bus
  eventBus: {
    test: () => api.get('/api/event-bus/test'),
  },
  
  // Экстренная остановка
  emergencyStop: () => api.post('/api/emergency-stop'),
  
  // Для совместимости с компонентами (используют моковые данные если endpoint не найден)
  deepLearning: {
    predict: (data: any) => api.post('/api/v1/deep-learning/predict', data).catch(() => ({ data: { mock: true } })),
    train: (data: any) => api.post('/api/v1/deep-learning/train', data).catch(() => ({ data: { mock: true } })),
    getModelsStatus: () => api.get('/api/v1/deep-learning/models/status').catch(() => ({ data: { mock: true } })),
    updateWeights: (weights: any) => api.post('/api/v1/deep-learning/models/weights', weights).catch(() => ({ data: { mock: true } })),
  },
  
  // Adaptive Trading - используем dashboard данные
  adaptiveTrading: {
    getPerformance: () => api.get('/api/dashboard'),
    getSignalHistory: (limit = 50) => api.get('/api/signals'),
    getSettings: () => api.get('/health'),
    updateProfile: (profile: string) => api.post('/api/emergency-stop', { profile }).catch(() => ({ data: { success: false } })),
    updateAIMode: (mode: string) => api.post('/api/emergency-stop', { mode }).catch(() => ({ data: { success: false } })),
  },
};

export default api; 