function asList(value) {
  return Array.isArray(value) ? value : [];
}

export function formatMetricValue(value, options = {}) {
  const fallback = options.fallback ?? "-";
  const number = Number(value);

  if (value === null || value === undefined || value === "" || Number.isNaN(number)) {
    return fallback;
  }

  return new Intl.NumberFormat("zh-TW", {
    maximumFractionDigits: options.maximumFractionDigits ?? 0,
    minimumFractionDigits: options.minimumFractionDigits,
  }).format(number);
}

export function formatPercentValue(value, options = {}) {
  const fallback = options.fallback ?? "-";
  const number = Number(value);

  if (value === null || value === undefined || value === "" || Number.isNaN(number)) {
    return fallback;
  }

  if (options.scalePercent === false) {
    return `${formatMetricValue(number, { ...options, fallback })}%`;
  }

  return new Intl.NumberFormat("zh-TW", {
    style: "percent",
    maximumFractionDigits: options.maximumFractionDigits ?? 1,
    minimumFractionDigits: options.minimumFractionDigits ?? 1,
  }).format(number);
}

export function getLatestMonthLabel(summary, fallback = "-") {
  return (
    summary?.recent_snapshot?.current_month?.month ||
    summary?.recent_snapshot?.latest_month ||
    summary?.dashboard_snapshot?.latest_month ||
    asList(summary?.project_overview?.months).at(-1) ||
    fallback
  );
}

export function getExecutiveHeadline(summary, fallback = "目前尚未載入摘要資料。") {
  return summary?.latest_month_analysis || fallback;
}

function getEntityName(item) {
  return item?.platform || item?.product_line_5 || item?.product_line || item?.entity || item?.name;
}

function getEntityMetricValue(item) {
  return item?.value ?? item?.revenue ?? item?.inventory_amount;
}

function hasMetricValue(value) {
  return value !== null && value !== undefined && value !== "" && !Number.isNaN(Number(value));
}

export function formatPlatformMetric(item, options = {}) {
  const fallback = options.fallback ?? "-";
  const entityName = getEntityName(item);
  const rawValue = getEntityMetricValue(item);
  if (!entityName || !hasMetricValue(rawValue)) {
    return fallback;
  }

  return `${entityName} · ${formatMetricValue(rawValue, options)}`;
}

export function formatPlatformValue(item, options = {}) {
  return getEntityName(item) || options.fallback || "-";
}

export function formatPlatformHelper(label, item, options = {}) {
  const entityName = getEntityName(item);
  if (!entityName) {
    return label || options.fallback || "-";
  }

  const rawValue = getEntityMetricValue(item);
  if (!hasMetricValue(rawValue)) {
    return label || options.fallback || "-";
  }

  return `${label} · ${entityName} · ${formatMetricValue(rawValue, options)}`;
}

export function buildKpiItems(summary, copy = {}, options = {}) {
  const recentSnapshot = summary?.recent_snapshot || {};
  const dashboardSnapshot = summary?.dashboard_snapshot || {};
  const currentMonth = recentSnapshot.current_month || {};
  const recentPeriod = recentSnapshot.recent_period || {};
  const latestMonth = getLatestMonthLabel(summary, copy.noData || "-");
  const anomalies = asList(dashboardSnapshot.anomalies);
  const revenueProductLineExtremes = dashboardSnapshot.product_line_revenue_extremes || {};

  const mode = options.mode || "desktop";
  if (mode === "mobile") {
    return [
      {
        label: copy.currentRevenueLabel,
        value: formatMetricValue(currentMonth.revenue, { fallback: copy.noData || "-" }),
        helper: `${copy.momLabel} ${formatPercentValue(currentMonth.revenue_mom, {
          fallback: copy.noData || "-",
          scalePercent: false,
          maximumFractionDigits: 2,
        })}`,
        tone: "good",
      },
      {
        label: copy.currentInventoryLabel,
        value: formatMetricValue(currentMonth.inventory_amount, { fallback: copy.noData || "-" }),
        helper: `${copy.momLabel} ${formatPercentValue(currentMonth.inventory_amount_mom, {
          fallback: copy.noData || "-",
          scalePercent: false,
          maximumFractionDigits: 2,
        })}`,
        tone: "watch",
      },
      {
        label: copy.anomalyLabel,
        value: formatMetricValue(anomalies.length, {
          fallback: copy.noData || "-",
          maximumFractionDigits: 0,
        }),
        helper: `${latestMonth} ${copy.latestDetectedLabel || ""}`.trim(),
        tone: anomalies.length ? "risk" : "good",
      },
    ];
  }

  return [
    {
      label: copy.currentRevenueLabel,
      value: formatMetricValue(currentMonth.revenue, { fallback: copy.noData || "-" }),
      helper: `${copy.momLabel} ${formatPercentValue(currentMonth.revenue_mom, {
        fallback: copy.noData || "-",
      })}`,
    },
    {
      label: copy.currentInventoryLabel,
      value: formatMetricValue(currentMonth.inventory_amount, { fallback: copy.noData || "-" }),
      helper: `${copy.momLabel} ${formatPercentValue(currentMonth.inventory_amount_mom, {
        fallback: copy.noData || "-",
      })}`,
    },
    {
      label: copy.recentRevenueLabel,
      value: formatMetricValue(recentPeriod.revenue_total, { fallback: copy.noData || "-" }),
      helper: asList(recentPeriod.months).join(" / ") || copy.noData || "-",
    },
    {
      label: copy.recentInventoryLabel,
      value: formatMetricValue(recentPeriod.inventory_amount_total, { fallback: copy.noData || "-" }),
      helper: `QTY ${formatMetricValue(recentPeriod.inventory_qty_total, { fallback: copy.noData || "-" })}`,
    },
    {
      label: copy.topRevenuePlatformLabel,
      value: formatPlatformMetric(dashboardSnapshot.revenue_extremes?.max, { fallback: copy.noData || "-" }),
      helper: formatPlatformHelper(copy.minRevenuePlatformLabel, dashboardSnapshot.revenue_extremes?.min, {
        fallback: copy.noData || "-",
      }),
    },
    {
      label: copy.topRevenueProductLineLabel || copy.topInventoryPlatformLabel,
      value: formatPlatformMetric(revenueProductLineExtremes.max, { fallback: copy.noData || "-" }),
      helper: formatPlatformHelper(copy.minRevenueProductLineLabel, revenueProductLineExtremes.min, {
        fallback: copy.noData || "-",
      }),
    },
  ];
}

export function buildSnapshotItems(summary, copy = {}, options = {}) {
  const dashboardSnapshot = summary?.dashboard_snapshot || {};
  const mode = options.mode || "desktop";

  const revenueMax = dashboardSnapshot.revenue_extremes?.max;
  const inventoryMax = dashboardSnapshot.inventory_extremes?.max;
  const revenueProductLineExtremes = dashboardSnapshot.product_line_revenue_extremes || {};
  const revenueProductLineMax = revenueProductLineExtremes.max;

  if (mode === "mobile") {
    return [
      {
        label: copy.topRevenuePlatformLabel,
        value: formatPlatformValue(revenueMax, { fallback: copy.noData || "-" }),
        helper: formatMetricValue(revenueMax?.value ?? revenueMax?.revenue, {
          fallback: copy.noData || "-",
        }),
      },
      {
        label: copy.topRevenueProductLineLabel || copy.topInventoryPlatformLabel,
        value: formatPlatformValue(revenueProductLineMax, { fallback: copy.noData || "-" }),
        helper: formatMetricValue(revenueProductLineMax?.value ?? revenueProductLineMax?.revenue, {
          fallback: copy.noData || "-",
        }),
      },
    ];
  }

  return [
    {
      label: copy.topRevenuePlatformLabel,
      value: formatPlatformMetric(revenueMax, { fallback: copy.noData || "-" }),
      helper: formatPlatformHelper(copy.minRevenuePlatformLabel, dashboardSnapshot.revenue_extremes?.min, {
        fallback: copy.noData || "-",
      }),
    },
    {
      label: copy.topRevenueProductLineLabel || copy.topInventoryPlatformLabel,
      value: formatPlatformMetric(revenueProductLineMax, { fallback: copy.noData || "-" }),
      helper: formatPlatformHelper(copy.minRevenueProductLineLabel, revenueProductLineExtremes.min, {
        fallback: copy.noData || "-",
      }),
    },
  ];
}
