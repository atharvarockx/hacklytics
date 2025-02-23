import React from 'react';
import { BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid } from 'recharts';

const colors = ['#8884d8', '#82ca9d', '#8884d8', '#82ca9d', '#8884d8'];

const getPath = (x, y, width, height) => {
  return `M${x},${y + height}C${x + width / 3},${y + height} ${x + width / 2},${y + height / 3}
  ${x + width / 2}, ${y}
  C${x + width / 2},${y + height / 3} ${x + (2 * width) / 3},${y + height} ${x + width}, ${y + height}
  Z`;
};

const TriangleBar = (props) => {
  const { fill, x, y, width, height } = props;
  return <path d={getPath(x, y, width, height)} stroke="none" fill={fill} />;
};

export const BarChartFinal = ({ barData }) => {
  // ✅ Ensure barData is defined and has the expected structure
  const chartData = barData?.charts?.barChart?.data || [];

  return (
    <BarChart
      width={500}
      height={300}
      data={chartData} // ✅ Use the safely extracted array
      margin={{
        top: 20,
        right: 30,
        left: 20,
        bottom: 60,
      }}
    >
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="name" interval={0} tick={{ angle: -30, textAnchor: "end", dy: 0 }}  />
      <YAxis />
      <Bar dataKey="amount" fill="#8884d8" shape={<TriangleBar />} label={{ position: 'top' }}>
        {chartData.map((entry, index) => (
          <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
        ))}
      </Bar>
    </BarChart>
  );
};
