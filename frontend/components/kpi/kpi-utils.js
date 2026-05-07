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

export function formatPlatformMetric(item, options = {}) {
  const fallback = options.fallback ?? "-";
  if (!item?.platform) {
    return fallback;
  }

  const rawValue = item.value ?? item.revenue ?? item.inventory_amount;
  return `${item.platform} · ${formatMetricValue(rawValue, options)}`;
}

export function formatPlatformValue(item, options = {}) {
  return item?.platform || options.fallback || "-";
}

export function formatPlatformHelper(label, item, options = {}) {
  if (!item?.platform) {
    return label;
  }

  const rawValue = item.value ?? item.revenue ?? item.inventory_amount;
  return `${label} · ${item.platform} · ${formatMetricValue(rawValue, options)}`;
}

export function buildKpiItems(summary, copy = {}, options = {}) {
  const recentSnapshot = summary?.recent_snapshot || {};
  const dashboardSnapshot = summary?.dashboard_snapshot || {};
  const currentMonth = recentSnapshot.current_month || {};
  const recentPeriod = recentSnapshot.recent_period || {};
  const latestMonth = getLatestMonthLabel(summary, copy.noData || "-");
  const anomalies = asList(dashboardSnapshot.anomalies);

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
      label: copy.topInventoryPlatformLabel,
      value: formatPlatformMetric(dashboardSnapshot.inventory_extremes?.max, { fallback: copy.noData || "-" }),
      helper: formatPlatformHelper(copy.minInventoryPlatformLabel, dashboardSnapshot.inventory_extremes?.min, {
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
        label: copy.topInventoryPlatformLabel,
        value: formatPlatformValue(inventoryMax, { fallback: copy.noData || "-" }),
        helper: formatMetricValue(inventoryMax?.value ?? inventoryMax?.inventory_amount, {
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
      label: copy.topInventoryPlatformLabel,
      value: formatPlatformMetric(inventoryMax, { fallback: copy.noData || "-" }),
      helper: formatPlatformHelper(copy.minInventoryPlatformLabel, dashboardSnapshot.inventory_extremes?.min, {
        fallback: copy.noData || "-",
      }),
    },
  ];
}
