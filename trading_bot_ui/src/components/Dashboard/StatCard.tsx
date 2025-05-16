import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  description?: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, description }) => {
  return (
    <div className="bg-white shadow-lg rounded-lg p-4 md:p-6">
      <h3 className="text-sm md:text-base font-medium text-gray-500">{title}</h3>
      <p className="text-xl md:text-2xl font-semibold text-gray-800 mt-1">{value}</p>
      {description && <p className="text-xs text-gray-400 mt-1">{description}</p>}
    </div>
  );
};

export default StatCard; 