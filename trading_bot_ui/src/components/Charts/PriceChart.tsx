import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts';
import { Price } from '../../types/Price'; // Adjusted path

interface PriceChartProps {
  prices: Price[];
  entryPrice?: number;
  targetPrice?: number;
  stopLoss?: number;
}

const PriceChart: React.FC<PriceChartProps> = ({ 
  prices, 
  entryPrice, 
  targetPrice, 
  stopLoss 
}) => {
  return (
    <div className="h-64 w-full md:h-96"> {/* Added md:h-96 for larger screens */}
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={prices}
          margin={{ top: 5, right: 30, left: 0, bottom: 5 }} // Adjusted margins
        >
          <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
          <XAxis 
            dataKey="timestamp" 
            tickFormatter={(timestamp) => {
              const date = new Date(timestamp);
              // Show HH:MM for recent, or DD/MM for older data if span is large
              return `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
            }}
            minTickGap={30} // Adjusted tick gap
            // Consider adding scale="time" type="number" if timestamps are numeric
          />
          <YAxis domain={['auto', 'auto']} tickFormatter={(value) => `$${value}`} />
          <Tooltip
            labelFormatter={(timestamp) => {
              const date = new Date(timestamp);
              return date.toLocaleString();
            }}
            formatter={(value: number) => [`$${value.toFixed(2)}`, 'Цена']}
          />
          <Line 
            type="monotone" 
            dataKey="price" 
            stroke="#3b82f6" // Tailwind blue-500
            dot={false} 
            strokeWidth={2}
          />
          {entryPrice && (
            <ReferenceLine 
              y={entryPrice} 
              stroke="#6366f1" // Tailwind indigo-500
              strokeDasharray="4 4" 
              label={{ value: 'Вход', position: 'insideTopRight', fill: '#6366f1' }}
            />
          )}
          {targetPrice && (
            <ReferenceLine 
              y={targetPrice} 
              stroke="#10b981" // Tailwind green-500
              strokeDasharray="4 4" 
              label={{ value: 'Цель', position: 'insideTopRight', fill: '#10b981' }}
            />
          )}
          {stopLoss && (
            <ReferenceLine 
              y={stopLoss} 
              stroke="#ef4444" // Tailwind red-500
              strokeDasharray="4 4" 
              label={{ value: 'Стоп', position: 'insideBottomRight', fill: '#ef4444' }}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default PriceChart; 