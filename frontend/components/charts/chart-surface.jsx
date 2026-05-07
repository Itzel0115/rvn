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

const EMPTY_COPY = {
  desktop: {
    title: "目前沒有可呈現的圖表資料",
    body: "請先在左側提出分析問題，或從右上角切換圖表，系統會自動載入對應的可視化內容。",
  },
  mobile: {
    title: "目前沒有可顯示的圖表",
    body: "可以先切換上方圖表，或打開 AI 助理提出問題，系統會自動更新對應圖表。",
  },
};

const VARIANT_CONFIG = {
  desktop: {
    containerClassName: "chart-surface",
    emptyClassName: "chart-empty",
    emptyTitleClassName: "chart-empty-title",
    palette: ["#1f6feb", "#ff6b35", "#0f9d58", "#8e44ad", "#c0392b", "#1b7f8c", "#e0a100"],
    margin: { top: 16, right: 16, left: 0, bottom: 8 },
    gridStroke: "rgba(9, 33, 71, 0.12)",
    axisTick: { fill: "#5f6b7f", fontSize: 12 },
    legendProps: {},
    tooltipProps: {
      contentStyle: {
        borderRadius: 16,
        border: "1px solid rgba(9, 33, 71, 0.12)",
        boxShadow: "0 18px 40px rgba(14, 29, 58, 0.12)",
      },
    },
    tooltipCursor: { fill: "rgba(31, 111, 235, 0.08)" },
    barRadius: [10, 10, 4, 4],
    pieCx: "50%",
    pieCy: "50%",
    pieOuterRadius: "78%",
    pieInnerRadius: "42%",
    lineStrokeWidth: 3,
    areaStrokeWidth: 3,
    lineDot: { r: 2 },
    lineActiveDot: { r: 5 },
  },
  mobile: {
    containerClassName: "mobile-exec-chart-surface",
    emptyClassName: "mobile-exec-chart-empty",
    emptyTitleClassName: "mobile-exec-chart-empty-title",
    palette: ["#2563eb", "#f97316", "#16a34a", "#7c3aed", "#dc2626", "#0891b2", "#ca8a04"],
    margin: { top: 14, right: 10, left: -14, bottom: 0 },
    gridStroke: "rgba(15, 23, 42, 0.1)",
    axisTick: { fill: "#64748b", fontSize: 11 },
    legendProps: { wrapperStyle: { fontSize: 11 } },
    tooltipProps: {
      contentStyle: {
        borderRadius: 8,
        border: "1px solid rgba(15, 23, 42, 0.12)",
        boxShadow: "0 14px 32px rgba(15, 23, 42, 0.14)",
        fontSize: 12,
      },
    },
    tooltipCursor: { fill: "rgba(37, 99, 235, 0.08)" },
    barRadius: [6, 6, 2, 2],
    pieCx: "50%",
    pieCy: "48%",
    pieOuterRadius: "76%",
    pieInnerRadius: "42%",
    lineStrokeWidth: 2.5,
    areaStrokeWidth: 2.5,
    lineDot: { r: 2 },
    lineActiveDot: { r: 4 },
  },
};

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

function buildPieData(data, seriesName, palette) {
  return data.map((item, index) => ({
    name: item.label,
    value: item[seriesName],
    fill: palette[index % palette.length],
  }));
}

function buildTooltipProps(config, includeCursor = false) {
  return includeCursor
    ? {
        cursor: config.tooltipCursor,
        ...config.tooltipProps,
      }
    : config.tooltipProps;
}

export function SharedChartSurface({ payload, variant = "desktop" }) {
  const config = VARIANT_CONFIG[variant] || VARIANT_CONFIG.desktop;
  const emptyCopy = EMPTY_COPY[variant] || EMPTY_COPY.desktop;

  if (!payload?.labels?.length || !payload?.series?.length) {
    return (
      <div className={config.emptyClassName}>
        <div className={config.emptyTitleClassName}>{emptyCopy.title}</div>
        <p>{emptyCopy.body}</p>
      </div>
    );
  }

  const data = buildData(payload);
  const chartType = payload.chart_type;

  return (
    <div className={config.containerClassName}>
      <ResponsiveContainer width="100%" height="100%">
        {chartType === "bar" ? (
          <BarChart data={data} margin={config.margin}>
            <CartesianGrid strokeDasharray="3 3" stroke={config.gridStroke} vertical={false} />
            <XAxis dataKey="label" tick={config.axisTick} axisLine={false} tickLine={false} />
            <YAxis tick={config.axisTick} axisLine={false} tickLine={false} />
            <Tooltip {...buildTooltipProps(config, true)} />
            <Legend {...config.legendProps} />
            {payload.series.map((item, index) => (
              <Bar
                key={item.name}
                dataKey={item.name}
                radius={config.barRadius}
                fill={item.color || config.palette[index % config.palette.length]}
              />
            ))}
          </BarChart>
        ) : chartType === "area" ? (
          <AreaChart data={data} margin={config.margin}>
            <CartesianGrid strokeDasharray="3 3" stroke={config.gridStroke} vertical={false} />
            <XAxis dataKey="label" tick={config.axisTick} axisLine={false} tickLine={false} />
            <YAxis tick={config.axisTick} axisLine={false} tickLine={false} />
            <Tooltip {...buildTooltipProps(config)} />
            <Legend {...config.legendProps} />
            {payload.series.map((item, index) => (
              <Area
                key={item.name}
                type="monotone"
                dataKey={item.name}
                stroke={item.color || config.palette[index % config.palette.length]}
                fill={item.color || config.palette[index % config.palette.length]}
                fillOpacity={0.2}
                strokeWidth={config.areaStrokeWidth}
              />
            ))}
          </AreaChart>
        ) : chartType === "pie" ? (
          <PieChart>
            <Tooltip {...buildTooltipProps(config)} />
            <Legend {...config.legendProps} />
            <Pie
              data={buildPieData(data, payload.series[0]?.name, config.palette)}
              dataKey="value"
              nameKey="name"
              cx={config.pieCx}
              cy={config.pieCy}
              outerRadius={config.pieOuterRadius}
              innerRadius={config.pieInnerRadius}
              paddingAngle={2}
            >
              {data.map((item, index) => (
                <Cell key={`${item.label}-${index}`} fill={config.palette[index % config.palette.length]} />
              ))}
            </Pie>
          </PieChart>
        ) : (
          <LineChart data={data} margin={config.margin}>
            <CartesianGrid strokeDasharray="3 3" stroke={config.gridStroke} vertical={false} />
            <XAxis dataKey="label" tick={config.axisTick} axisLine={false} tickLine={false} />
            <YAxis tick={config.axisTick} axisLine={false} tickLine={false} />
            <Tooltip {...buildTooltipProps(config)} />
            <Legend {...config.legendProps} />
            {payload.series.map((item, index) => (
              <Line
                key={item.name}
                type="monotone"
                dataKey={item.name}
                stroke={item.color || config.palette[index % config.palette.length]}
                strokeWidth={config.lineStrokeWidth}
                dot={config.lineDot}
                activeDot={config.lineActiveDot}
              />
            ))}
          </LineChart>
        )}
      </ResponsiveContainer>
    </div>
  );
}

export function ChartSurface(props) {
  return <SharedChartSurface {...props} variant="desktop" />;
}
