import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
 
export const LineChart2 = ({ barData }) => {
  // Handle undefined data gracefully
  const data = barData?.charts?.savingsChart?.data || [];
 
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart width={500} height={300} data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" padding={{ left: 30, right: 30 }} />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="amount" stroke="#82ca9d" />
      </LineChart>
    </ResponsiveContainer>
  );
};