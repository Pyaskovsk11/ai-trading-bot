import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { CheckCircle, XCircle, Clock } from 'lucide-react';

const ApiStatus: React.FC = () => {
  const { data: apiStatus, isLoading, error } = useQuery({
    queryKey: ['api-status'],
    queryFn: async () => {
      try {
        const response = await fetch('/api/v1/health', {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
          throw new Error('API недоступен');
        }
        
        return { status: 'connected', message: 'API подключен' };
      } catch (error) {
        return { status: 'disconnected', message: 'API недоступен' };
      }
    },
    refetchInterval: 30000, // Проверяем каждые 30 секунд
    retry: 1
  });

  const getStatusIcon = () => {
    if (isLoading) return <Clock className="w-4 h-4 text-yellow-400 animate-spin" />;
    if (error || apiStatus?.status === 'disconnected') {
      return <XCircle className="w-4 h-4 text-red-400" />;
    }
    return <CheckCircle className="w-4 h-4 text-green-400" />;
  };

  const getStatusText = () => {
    if (isLoading) return 'Проверка...';
    if (error || apiStatus?.status === 'disconnected') {
      return 'API недоступен';
    }
    return 'API подключен';
  };

  const getStatusColor = () => {
    if (isLoading) return 'text-yellow-400';
    if (error || apiStatus?.status === 'disconnected') {
      return 'text-red-400';
    }
    return 'text-green-400';
  };

  return (
    <div className="flex items-center space-x-2 text-sm">
      {getStatusIcon()}
      <span className={getStatusColor()}>
        {getStatusText()}
      </span>
    </div>
  );
};

export default ApiStatus; 