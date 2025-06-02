import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  Brain, 
  TrendingUp, 
  Newspaper, 
  Settings, 
  Menu, 
  X,
  Activity,
  Cpu,
  BarChart3
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ApiStatus from '../ApiStatus';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  const navigation = [
    { name: 'Дашборд', href: '/', icon: BarChart3 },
    { name: 'Размышления ИИ', href: '/neural-thinking', icon: Brain },
    { name: 'Торговые сигналы', href: '/signals', icon: TrendingUp },
    { name: 'Анализ новостей', href: '/news', icon: Newspaper },
    { name: 'Управление моделями', href: '/models', icon: Cpu },
    { name: 'Настройки', href: '/settings', icon: Settings },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="flex h-screen bg-dark-900">
      {/* Мобильная навигация */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 lg:hidden"
          >
            <div className="fixed inset-0 bg-black/50" onClick={() => setSidebarOpen(false)} />
            <motion.div
              initial={{ x: -300 }}
              animate={{ x: 0 }}
              exit={{ x: -300 }}
              className="fixed left-0 top-0 h-full w-64 bg-dark-800 border-r border-dark-700"
            >
              <div className="flex items-center justify-between p-4 border-b border-dark-700">
                <h1 className="text-xl font-bold gradient-text">AI Trading Bot</h1>
                <button
                  onClick={() => setSidebarOpen(false)}
                  className="p-2 rounded-lg hover:bg-dark-700 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <nav className="p-4 space-y-2">
                {navigation.map((item) => {
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      onClick={() => setSidebarOpen(false)}
                      className={`flex items-center space-x-3 px-3 py-2 rounded-lg transition-all duration-200 ${
                        isActive(item.href)
                          ? 'bg-primary-600 text-white shadow-glow'
                          : 'text-gray-300 hover:bg-dark-700 hover:text-white'
                      }`}
                    >
                      <Icon className="w-5 h-5" />
                      <span>{item.name}</span>
                    </Link>
                  );
                })}
              </nav>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Десктопная навигация */}
      <div className="hidden lg:flex lg:w-64 lg:flex-col">
        <div className="flex flex-col flex-1 bg-dark-800 border-r border-dark-700">
          {/* Логотип */}
          <div className="flex items-center h-16 px-4 border-b border-dark-700">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
                <Activity className="w-5 h-5 text-white" />
              </div>
              <h1 className="text-xl font-bold gradient-text">AI Trading Bot</h1>
            </div>
          </div>

          {/* Навигация */}
          <nav className="flex-1 p-4 space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center space-x-3 px-3 py-2 rounded-lg transition-all duration-200 ${
                    isActive(item.href)
                      ? 'bg-primary-600 text-white shadow-glow'
                      : 'text-gray-300 hover:bg-dark-700 hover:text-white'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* Статус системы */}
          <div className="p-4 border-t border-dark-700">
            <div className="flex items-center space-x-2 text-sm text-gray-400">
              <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse"></div>
              <span>Система активна</span>
            </div>
          </div>
        </div>
      </div>

      {/* Основной контент */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Верхняя панель */}
        <header className="bg-dark-800 border-b border-dark-700 px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSidebarOpen(true)}
                className="lg:hidden p-2 rounded-lg hover:bg-dark-700 transition-colors"
              >
                <Menu className="w-5 h-5" />
              </button>
              
              <div className="hidden lg:block">
                <h2 className="text-lg font-semibold text-gray-100">
                  {navigation.find(item => isActive(item.href))?.name || 'AI Trading Bot'}
                </h2>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* Индикатор подключения к API */}
              <ApiStatus />
            </div>
          </div>
        </header>

        {/* Контент страницы */}
        <main className="flex-1 overflow-auto bg-dark-900 neural-pattern">
          <div className="p-6">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout; 