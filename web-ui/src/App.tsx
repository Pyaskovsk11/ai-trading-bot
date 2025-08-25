import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import RealTrading from './pages/RealTrading';
import TradeHistory from './pages/TradeHistory';
import StrategyLibrary from './pages/StrategyLibrary';
import SecurityKeys from './pages/SecurityKeys';
// import StrategyCompare from './pages/StrategyCompare';
import Scanner from './pages/Scanner';
import AdminBacktest from './pages/AdminBacktest';
import Onboarding from './pages/Onboarding';

// Создаем клиент для React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 30 * 1000, // 30 секунд
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="flex min-h-screen bg-gray-900">
          <Sidebar />
          <main className="flex-1">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/settings" element={<SecurityKeys />} />
              <Route path="/real-trading" element={<RealTrading />} />
              <Route path="/trade-history" element={<TradeHistory />} />
              <Route path="/strategies" element={<StrategyLibrary />} />
              <Route path="/security-keys" element={<SecurityKeys />} />
              <Route path="/scanner" element={<Scanner />} />
              <Route path="/admin/backtest" element={<AdminBacktest />} />
              <Route path="/onboarding" element={<Onboarding />} />
            </Routes>
          </main>
        </div>
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#374151',
              color: '#fff',
            },
          }}
        />
      </Router>
    </QueryClientProvider>
  );
}

export default App; 