import React from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { SignalDistribution } from '../../types/Stats'; // Adjusted path

interface SignalTypeDistributionProps {
  distribution?: SignalDistribution;
}

const COLORS = {
  BUY: '#10b981', // green-500
  SELL: '#ef4444', // red-500
  HOLD: '#6b7280'  // gray-500
};

const SignalTypeDistribution: React.FC<SignalTypeDistributionProps> = ({ distribution }) => {
  if (!distribution) {
    return <div className="p-4 bg-white shadow-lg rounded-lg">Loading distribution...</div>;
  }

  const data = [
    { name: 'BUY', value: distribution.BUY },
    { name: 'SELL', value: distribution.SELL },
    { name: 'HOLD', value: distribution.HOLD },
  ].filter(item => item.value > 0);

  return (
    <div className="bg-white shadow-lg rounded-lg p-4 h-64 md:h-80">
      <h3 className="text-md font-semibold mb-2 text-gray-700">Signal Types</h3>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
            label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[entry.name as keyof typeof COLORS]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

export default SignalTypeDistribution; 