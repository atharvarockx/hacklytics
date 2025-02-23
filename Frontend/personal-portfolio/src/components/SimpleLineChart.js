import React, { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import chartData from "../jsonFiles/data.json"; 


export const SimpleLineChart = ({barData}) => {

    // const [barData, setBarData] = useState([]);

    // useEffect(() => {
    //     // Extract barChart data
    //     if (chartData?.charts?.lineChart?.data) {
    //     setBarData(chartData.charts.lineChart.data);
    //     }
    // }, []);

    console.log("I am inside", barData);


  const [opacity, setOpacity] = React.useState({
    Income: 1,
    Expenditure: 1,
  });

  const handleMouseEnter = (o) => {
    const { dataKey } = o;

    setOpacity((op) => ({ ...op, [dataKey]: 0.5 }));
  };

  const handleMouseLeave = (o) => {
    const { dataKey } = o;

    setOpacity((op) => ({ ...op, [dataKey]: 1 }));
  };

  return (
    <div style={{ width: '100%' }}>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart
          width={500}
          height={300}
          data={barData.charts.lineChart.data}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend onMouseEnter={handleMouseEnter} onMouseLeave={handleMouseLeave} />
          <Line type="monotone" dataKey="Income" strokeOpacity={opacity.Income} stroke="#8884d8" activeDot={{ r: 8 }} />
          <Line type="monotone" dataKey="Expenditure" strokeOpacity={opacity.Expenditure} stroke="#82ca9d" />
        </LineChart>
      </ResponsiveContainer>
      {/* <p className="notes" style={{marginLeft:'40px'}}>Tip: Hover the legend !</p> */}
    </div>
  );
};
