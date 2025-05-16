import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface SuccessRateChartProps {
  successRate?: number;
  // Could also take historical success rates for a time series bar chart
}

const SuccessRateChart: React.FC<SuccessRateChartProps> = ({ successRate }) => {
  if (typeof successRate === 'undefined') {
    return <div className="p-4 bg-white shadow-lg rounded-lg">Loading success rate...</div>;
  }

  const data = [
    {
      name: 'Success Rate',
      rate: successRate * 100,
    },
  ];

  return (
    <div className="bg-white shadow-lg rounded-lg p-4 h-64 md:h-80">
       <h3 className="text-md font-semibold mb-2 text-gray-700">Signal Success Rate</h3>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart 
          data={data}
          layout="vertical" // For a single prominent bar
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
          <XAxis type="number" domain={[0, 100]} tickFormatter={(value) => `${value}%`} />
          <YAxis type="category" dataKey="name" hide />
          <Tooltip formatter={(value: number) => [`${value.toFixed(1)}%`, "Success Rate"]} />
          <Legend />
          <Bar dataKey="rate" fill="#22c55e" barSize={60} /> {/* green-500 */}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default SuccessRateChart; 