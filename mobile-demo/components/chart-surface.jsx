"use client";

import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const EMPTY_TITLE = "目前沒有可呈現的圖表資料";
const EMPTY_BODY = "請先切換圖表，或從右下角呼叫 AI 提出分析問題。";
const PALETTE = ["#2563eb", "#f97316", "#16a34a", "#7c3aed", "#dc2626", "#0891b2", "#ca8a04"];

function buildData(payload) {
  const labels = payload?.labels || [];
  const series = payload?.series || [];

  return labels.map((label, index) => {
    const row = { label };
    series.forEach((item) => {
      row[item.name] = item.data?.[index] ?? null;
    });
    return row;
  });
}

function chartMargin() {
  return { top: 14, right: 10, left: -14, bottom: 0 };
}

function tooltipProps() {
  return {
    contentStyle: {
      borderRadius: 8,
      border: "1px solid rgba(15, 23, 42, 0.12)",
      boxShadow: "0 14px 32px rgba(15, 23, 42, 0.14)",
      fontSize: 12,
    },
  };
}

export function ChartSurface({ payload }) {
  if (!payload?.labels?.length || !payload?.series?.length) {
    return (
      <div className="chart-empty">
        <div className="chart-empty-title">{EMPTY_TITLE}</div>
        <p>{EMPTY_BODY}</p>
      </div>
    );
  }

  const data = buildData(payload);
  const chartType = payload.chart_type;

  return (
    <div className="chart-surface">
      <ResponsiveContainer width="100%" height="100%">
        {chartType === "bar" ? (
          <BarChart data={data} margin={chartMargin()}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(15, 23, 42, 0.1)" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip cursor={{ fill: "rgba(37, 99, 235, 0.08)" }} {...tooltipProps()} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            {payload.series.map((item, index) => (
              <Bar
                key={item.name}
                dataKey={item.name}
                radius={[6, 6, 2, 2]}
                fill={item.color || PALETTE[index % PALETTE.length]}
              />
            ))}
          </BarChart>
        ) : chartType === "area" ? (
          <AreaChart data={data} margin={chartMargin()}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(15, 23, 42, 0.1)" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip {...tooltipProps()} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            {payload.series.map((item, index) => (
              <Area
                key={item.name}
                type="monotone"
                dataKey={item.name}
                stroke={item.color || PALETTE[index % PALETTE.length]}
                fill={item.color || PALETTE[index % PALETTE.length]}
                fillOpacity={0.2}
                strokeWidth={2.5}
              />
            ))}
          </AreaChart>
        ) : chartType === "pie" ? (
          <PieChart>
            <Tooltip {...tooltipProps()} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Pie
              data={data.map((item, index) => ({
                name: item.label,
                value: item[payload.series[0]?.name],
                fill: PALETTE[index % PALETTE.length],
              }))}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="48%"
              outerRadius="76%"
              innerRadius="42%"
              paddingAngle={2}
            >
              {data.map((item, index) => (
                <Cell key={`${item.label}-${index}`} fill={PALETTE[index % PALETTE.length]} />
              ))}
            </Pie>
          </PieChart>
        ) : (
          <LineChart data={data} margin={chartMargin()}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(15, 23, 42, 0.1)" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip {...tooltipProps()} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            {payload.series.map((item, index) => (
              <Line
                key={item.name}
                type="monotone"
                dataKey={item.name}
                stroke={item.color || PALETTE[index % PALETTE.length]}
                strokeWidth={2.5}
                dot={{ r: 2 }}
                activeDot={{ r: 4 }}
              />
            ))}
          </LineChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}
