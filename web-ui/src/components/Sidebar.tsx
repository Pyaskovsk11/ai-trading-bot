import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  BarChart3, 
  TrendingUp, 
  Settings, 
  Activity,
  HomeIcon,
  ChartBarIcon,
  MagnifyingGlassIcon,
  CurrencyDollarIcon,
  KeyIcon,
  UserIcon,
  CogIcon
} from 'lucide-react';

const Sidebar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const handleNavigation = (path: string) => {
    navigate(path);
  };

  const menuItems = [
	{ name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
	{ name: 'Strategies', href: '/strategies', icon: ChartBarIcon },
	{ name: 'Scanner', href: '/scanner', icon: MagnifyingGlassIcon },
	{ name: 'Real Trading', href: '/real-trading', icon: CurrencyDollarIcon },
	{ name: 'API-ключи', href: '/security-keys', icon: KeyIcon },
	{ name: 'Onboarding', href: '/onboarding', icon: UserIcon },
	{ name: 'Admin · Бэктест', href: '/admin/backtest', icon: CogIcon },
];

  return (
    <div className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col">
      {/* Логотип */}
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center space-x-3">
          <Activity className="w-8 h-8 text-blue-400" />
          <div>
            <h1 className="text-xl font-bold text_white">AI Trading Bot</h1>
            <p className="text-sm text-gray-400">MVP / Beta</p>
          </div>
        </div>
      </div>

      {/* Навигация */}
      <nav className="flex-1">
        <div className="space-y-2">
          <button
            onClick={() => handleNavigation('/dashboard')}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
              location.pathname === '/dashboard' || location.pathname === '/'
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-700 hover:text-white'
            }`}
          >
            <BarChart3 className="w-5 h-5" />
            <span>Дашборд</span>
          </button>

          <button
            onClick={() => handleNavigation('/strategies')}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
              location.pathname === '/strategies'
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-700 hover:text-white'
            }`}
          >
            <Settings className="w-5 h-5" />
            <span>Стратегии</span>
          </button>

          <button
            onClick={() => handleNavigation('/scanner')}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
              location.pathname === '/scanner'
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-700 hover:text-white'
            }`}
          >
            <TrendingUp className="w-5 h-5" />
            <span>Сканер</span>
          </button>

          <button
            onClick={() => handleNavigation('/real-trading')}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
              location.pathname === '/real-trading'
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-700 hover:text-white'
            }`}
          >
            <TrendingUp className="w-5 h-5" />
            <span>Реальная торговля</span>
          </button>

          <button
            onClick={() => handleNavigation('/security-keys')}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
              location.pathname === '/security-keys' || location.pathname === '/settings'
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-700 hover:text-white'
            }`}
          >
            <Settings className="w-5 h-5" />
            <span>API-ключи</span>
          </button>

          <button
            onClick={() => handleNavigation('/admin/backtest')}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
              location.pathname === '/admin/backtest'
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-700 hover:text-white'
            }`}
          >
            <BarChart3 className="w-5 h-5" />
            <span>Admin · Бэктест</span>
          </button>
        </div>
      </nav>

      {/* Статус системы */}
      <div className="p-4 border-t border-gray-700">
        <div className="flex items-center space-x-2 text-sm">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          <span className="text-gray-400">Система активна</span>
        </div>
      </div>
    </div>
  );
};

export default Sidebar; 