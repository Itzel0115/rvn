"use client";

import { useEffect, useRef, useState } from "react";
import {
  BarChart3,
  Bot,
  ChevronDown,
  LayoutPanelTop,
  RefreshCcw,
  SendHorizonal,
  Sparkles,
} from "lucide-react";

import { ChartSurface } from "@/components/chart-surface";
import {
  buildAskRequestBody,
  buildAssistantMessage,
  buildConversationHistory,
  buildUserMessage,
} from "@/components/chat/chat-utils";
import { buildChartContextPayload, extractChartPayloadFromAskResponse } from "@/components/chat/chart-evidence";
import { ANALYST_QUICK_PROMPTS } from "@/components/chat/quick-prompts";
import { KpiCard } from "@/components/kpi/kpi-card";
import { SnapshotItem as SharedSnapshotItem } from "@/components/kpi/snapshot-item";
import { buildKpiItems, buildSnapshotItems, getExecutiveHeadline, getLatestMonthLabel } from "@/components/kpi/kpi-utils";
import { MessageCard } from "@/components/message-card";

const TEXT = {
  loadingTitle: "系統載入中",
  loadingBody: "正在整理資料摘要、近期觀測與可用圖表，稍後即可開始分析。",
  loadError: "資料載入失敗，請重新整理頁面後再試。",
  submitError: "送出分析請求時發生問題。",
  noData: "N/A",
  topbarSubtitle: "整合營收、庫存、異常訊號與 Chart Agent 的分析工作台",
  heroTitle: "最新月份分析摘要",
  emptySummary: "目前尚無可呈現的摘要內容。",
  refreshChart: "更新圖表",
  conversationPanelTitle: "分析對話",
  structuredReport: "結構化回覆",
  promptLabel: "輸入分析需求",
  promptPlaceholder:
    "例如：比較最新月份各事業群營收與庫存、畫出產品線營收長條圖，或觀察哪個事業群最近異常最多。",
  metaIdle: "可直接提問、要求重畫圖表，或在下方資料觀察區做自訂比較。",
  metaBusy: "正在協調 Agent 分析並整理結果…",
  send: "送出分析",
  sending: "分析中",
  suggestionTitle: "快速操作",
  suggestionSubtitle: "用常見問題快速切入資料觀察與繪圖。",
  dashboardTitle: "圖表儀表板",
  dashboardTag: "即時圖表",
  selectChart: "切換右側圖表",
  chartTableTitle: "圖表對應表格",
  chartNotLoaded: "尚未載入圖表",
  chartFiltered: "目前圖表已套用條件篩選",
  chartIdle: "可透過左側對話或右上選單切換圖表視角",
  snapshotTitle: "本月極值與異常",
  currentMonthAnomalies: "本月異常訊號",
  noCurrentMonthAnomalies: "本月未偵測到異常訊號",
  monthOverMonth: "月增率",
  minRevenuePlatform: "本月最低營收事業群",
  minRevenueProductLine: "本月最低營收產品線",
  minInventoryPlatform: "本月最低庫存事業群",
  statCurrentRevenue: "最新月份總營收",
  statCurrentInventory: "最新月份總庫存",
  statRecentRevenue: "近三月累積營收",
  statRecentInventory: "近三月累積庫存",
  statTopRevenuePlatform: "本月最高營收事業群",
  statTopRevenueProductLine: "本月最高營收產品線",
  statTopInventoryPlatform: "本月最高庫存事業群",
  observationTitle: "資料觀察區",
  observationSubtitle: "依月份、事業群、產品線與指標組合，自行切換比較視角。",
  observationApply: "更新觀察",
  observationLoading: "正在整理觀察表…",
  observationEmpty: "目前條件下沒有可供比較的資料。",
  observationMessageDefault: "可自由切換維度與比較條件，觀察各月份、事業群或產品線表現。",
  observationRowDimension: "觀察維度",
  observationMetric: "比較指標",
  observationCompareMode: "比較方式",
  observationCurrentMonth: "當期月份",
  observationCompareMonth: "比較月份",
  observationBusinessGroupFilter: "事業群篩選",
  observationProductLineFilter: "產品線篩選",
  allBusinessGroups: "全部事業群",
  allProductLines: "全部產品線",
};

const QUICK_PROMPTS = [
  "請整理最新月份各事業群的營收與庫存重點",
  "比較最新月份各產品線營收與庫存",
  "畫出 2025年2月各事業群營收圓餅圖",
  "列出 3通路方案 2026/2 營收",
];

const INITIAL_SYSTEM_MESSAGE = {
  id: "welcome",
  role: "system",
  title: TEXT.loadingTitle,
  text: TEXT.loadingBody,
};

const SHARED_QUICK_PROMPTS = ANALYST_QUICK_PROMPTS;

function formatCompactNumber(value, options = {}) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return TEXT.noData;
  }

  return new Intl.NumberFormat("zh-TW", {
    maximumFractionDigits: options.maximumFractionDigits ?? 0,
  }).format(Number(value));
}

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return TEXT.noData;
  }

  return new Intl.NumberFormat("zh-TW", {
    style: "percent",
    maximumFractionDigits: 1,
    minimumFractionDigits: 1,
  }).format(Number(value));
}

function formatMonthRange(months = []) {
  if (!months.length) {
    return TEXT.noData;
  }
  if (months.length === 1) {
    return months[0];
  }
  return `${months[0]} - ${months.at(-1)}`;
}

function formatPlatformMetric(item) {
  if (!item?.platform) {
    return TEXT.noData;
  }
  return `${item.platform} ｜ ${formatCompactNumber(item.value)}`;
}

function formatPlatformHelper(label, item) {
  if (!item?.platform) {
    return label;
  }
  return `${label} ｜ ${item.platform} ｜ ${formatCompactNumber(item.value)}`;
}

function normalizeMessage(response, fallbackQuestion) {
  return {
    id: response.request_id || crypto.randomUUID(),
    role: response.routing?.question_type === "overview" ? "system" : "assistant",
    text: response.summary || TEXT.emptySummary,
    title: response.routing?.question_type === "overview" ? "系統摘要" : "分析結果",
    requestId: response.request_id,
    questionType: response.routing?.question_type,
    answerContract: response.answer_contract || null,
    routing: response.routing || null,
    subtasks: response.routing?.subtasks || [],
    domainResults: response.domain_results || [],
    projectSummary: response.project_summary || null,
    originalQuestion: fallbackQuestion,
  };
}

function extractChartFromResponse(response) {
  const chartDomain = (response.domain_results || []).find((item) => item.domain === "chart");
  if (!chartDomain) {
    return null;
  }

  return (chartDomain.evidence || []).find((item) => item?.chart_type && item?.series) || null;
}

function buildWelcomeMessage(summary) {
  const overview = summary?.project_overview || {};
  const recentSnapshot = summary?.recent_snapshot || {};
  const supportedDomains = Object.entries(overview.supported_domains || {})
    .filter(([, enabled]) => enabled)
    .map(([name]) => name);

  return {
    id: "welcome",
    role: "system",
    title: "工作台已就緒",
    text:
      `目前已載入 ${supportedDomains.length} 個可用分析領域，資料月份範圍為 ${formatMonthRange(overview.months)}。` +
      ` 最新月份為 ${recentSnapshot.current_month?.month || TEXT.noData}，可直接開始提問、切換圖表或在下方觀察區比較資料。`,
    projectSummary: summary,
  };
}

const DEFAULT_COMPARE_MODES = [{ value: "previous_period", label: "前一期比較" }];

function normalizeObservationDimension(value) {
  if (value === "month") return "month";
  if (value === "product_line" || value === "product_line_5") return "product_line_5";
  return "business_group";
}

function getComparisonOptions(options, rowDimension) {
  const modes = options?.compare_modes?.length ? options.compare_modes : DEFAULT_COMPARE_MODES;
  const normalizedDimension = normalizeObservationDimension(rowDimension);
  if (normalizedDimension === "month") {
    const previousOnly = modes.filter((item) => item.value === "previous_period");
    return previousOnly.length ? previousOnly : modes.slice(0, 1);
  }
  return modes;
}

function getValidCompareMode(options, rowDimension, compareMode) {
  const modes = getComparisonOptions(options, rowDimension);
  return modes.some((item) => item.value === compareMode) ? compareMode : modes[0]?.value || "previous_period";
}

function getObservationFilterConfig(rowDimension) {
  const normalizedDimension = normalizeObservationDimension(rowDimension);
  if (normalizedDimension === "product_line_5") {
    return {
      stateKey: "product_line_5",
      label: TEXT.observationProductLineFilter,
      allLabel: TEXT.allProductLines,
      optionsKey: "product_lines",
    };
  }

  return {
    stateKey: "platform",
    label: TEXT.observationBusinessGroupFilter,
    allLabel: TEXT.allBusinessGroups,
    optionsKey: "business_groups",
  };
}

function getObservationFilterOptions(options, rowDimension) {
  const config = getObservationFilterConfig(rowDimension);
  if (config.optionsKey === "product_lines") {
    return options?.product_lines || [];
  }
  return options?.business_groups || options?.platforms || [];
}

function syncPreviousCompareMonth(selection, options) {
  if (selection.compare_mode !== "previous_period" || !options?.compare_month_pairs?.length) {
    return selection;
  }

  const matched = options.compare_month_pairs.find((item) => item.current_month === selection.current_month);
  return { ...selection, compare_month: matched?.compare_month || selection.compare_month };
}

function buildObservationSelection(options, current = {}) {
  const months = options?.months || [];
  const comparePairs = options?.compare_month_pairs || [];
  const latestMonth = months.at(-1) || "";
  const previousMonth =
    comparePairs.find((item) => item.current_month === latestMonth)?.compare_month ||
    months.at(-2) ||
    "";
  const rowDimension = normalizeObservationDimension(current.row_dimension || "business_group");

  return {
    row_dimension: rowDimension,
    metric: current.metric || "revenue",
    compare_mode: getValidCompareMode(options, rowDimension, current.compare_mode || "previous_period"),
    current_month: current.current_month || latestMonth,
    compare_month: current.compare_month || previousMonth,
    platform: current.platform || "",
    group_code: current.group_code || "",
    product_line_5: current.product_line_5 || current.product_line || "",
  };
}

function buildObservationPayload(selection) {
  const rowDimension = normalizeObservationDimension(selection.row_dimension);
  const compareMode = selection.compare_mode || "previous_period";
  const usesBusinessGroupFilter = rowDimension === "business_group" || rowDimension === "month";

  return {
    row_dimension: rowDimension,
    metric: selection.metric,
    compare_mode: compareMode,
    current_month: selection.current_month || null,
    compare_month: rowDimension === "month" || compareMode !== "custom_month" ? null : selection.compare_month || null,
    platform: usesBusinessGroupFilter ? selection.platform || null : null,
    group_code: usesBusinessGroupFilter ? selection.group_code || null : null,
    product_line_5: rowDimension === "product_line_5" ? selection.product_line_5 || null : null,
  };
}

function formatObservationValue(column, value) {
  if (value === null || value === undefined || value === "") {
    return TEXT.noData;
  }

  if (typeof value === "number") {
    if (column.includes("成長率")) {
      return formatPercent(value);
    }
    return formatCompactNumber(value, { maximumFractionDigits: 1 });
  }

  return String(value);
}

function valueTone(column, value) {
  if (typeof value !== "number") {
    return "";
  }
  if (column.includes("成長率") || column.includes("變化")) {
    if (value > 0) return "positive";
    if (value < 0) return "negative";
  }
  return "";
}

function StatCard({ label, value, helper }) {
  return (
    <article className="stat-card">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-helper">{helper}</div>
    </article>
  );
}

function SnapshotItem({ label, value, helper }) {
  return (
    <div className="snapshot-item">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{helper}</small>
    </div>
  );
}

export function InsightConsole() {
  const [summary, setSummary] = useState(null);
  const [chartCatalog, setChartCatalog] = useState([]);
  const [selectedChartKey, setSelectedChartKey] = useState("");
  const [dashboardChart, setDashboardChart] = useState(null);
  const [messages, setMessages] = useState([INITIAL_SYSTEM_MESSAGE]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [observationOptions, setObservationOptions] = useState(null);
  const [observationSelection, setObservationSelection] = useState(null);
  const [observationResult, setObservationResult] = useState(null);
  const [observationBusy, setObservationBusy] = useState(false);
  const messageThreadRef = useRef(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const frameId = requestAnimationFrame(() => {
      const thread = messageThreadRef.current;
      if (thread) {
        thread.scrollTo({ top: thread.scrollHeight, behavior: "smooth" });
        return;
      }
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    });

    return () => cancelAnimationFrame(frameId);
  }, [messages, busy]);

  async function fetchObservationTable(selection) {
    if (!selection) return;

    setObservationBusy(true);
    try {
      const payload = await fetch("/api/observe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildObservationPayload(selection)),
      }).then(async (res) => {
        const body = await res.json();
        if (!res.ok) {
          throw new Error(body.error || TEXT.loadError);
        }
        return body;
      });
      setObservationResult(payload);
    } catch (observationError) {
      setError(observationError.message || TEXT.loadError);
    } finally {
      setObservationBusy(false);
    }
  }

  useEffect(() => {
    async function bootstrap() {
      try {
        const [summaryResponse, chartResponse, observeOptionsResponse] = await Promise.all([
          fetch("/api/summary", { cache: "no-store" }).then((res) => res.json()),
          fetch("/api/chart-catalog", { cache: "no-store" }).then((res) => res.json()),
          fetch("/api/observe-options", { cache: "no-store" }).then((res) => res.json()),
        ]);

        setSummary(summaryResponse);
        setMessages([buildWelcomeMessage(summaryResponse)]);

        const charts = chartResponse.charts || [];
        setChartCatalog(charts);

        const firstAvailable = charts.find((item) => item.available);
        if (firstAvailable) {
          setSelectedChartKey(firstAvailable.chart_key);
          const defaultChart = await fetch("/api/chart", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ chart_key: firstAvailable.chart_key, render_image: false }),
          }).then((res) => res.json());
          setDashboardChart(defaultChart.chart || null);
        }

        setObservationOptions(observeOptionsResponse);
        const defaultSelection = buildObservationSelection(observeOptionsResponse);
        setObservationSelection(defaultSelection);
        await fetchObservationTable(defaultSelection);
      } catch (bootstrapError) {
        setError(bootstrapError.message || TEXT.loadError);
      }
    }

    bootstrap();
  }, []);

  async function refreshChart(chartKey) {
    if (!chartKey) return;

    setSelectedChartKey(chartKey);
    const payload = await fetch("/api/chart", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chart_key: chartKey, render_image: false }),
    }).then((res) => res.json());

    setDashboardChart(payload.chart || null);
  }

  async function submitQuestion(question) {
    const trimmed = question.trim();
    if (!trimmed) return;

    setBusy(true);
    setError("");
    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "user", title: "使用者訊息", text: trimmed },
    ]);
    setDraft("");

    try {
      const conversationHistory = messages
        .filter((item) => item.role === "user" || item.role === "assistant")
        .slice(-6)
        .map((item) => ({
          role: item.role,
          text: item.text,
        }));

      const response = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: trimmed,
          history: conversationHistory,
          chart_context: dashboardChart
            ? {
                chart_key: dashboardChart.chart_key,
                chart_type: dashboardChart.chart_type,
                title: dashboardChart.title,
                filters: dashboardChart.filters,
              }
            : null,
        }),
      }).then(async (res) => {
        const payload = await res.json();
        if (!res.ok) {
          throw new Error(payload.error || TEXT.submitError);
        }
        return payload;
      });

      setMessages((current) => [...current, normalizeMessage(response, trimmed)]);

      const chartPayload = extractChartFromResponse(response);
      if (chartPayload) {
        setDashboardChart(chartPayload);
        setSelectedChartKey(chartPayload.chart_key || "");
      }
    } catch (submitError) {
      setError(submitError.message || TEXT.submitError);
    } finally {
      setBusy(false);
    }
  }

  async function submitQuestionShared(question) {
    const trimmed = question.trim();
    if (!trimmed) return;

    setBusy(true);
    setError("");
    setMessages((current) => [...current, buildUserMessage(trimmed, { title: "使用者提問" })]);
    setDraft("");

    try {
      const conversationHistory = buildConversationHistory(messages);
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          buildAskRequestBody(trimmed, {
            history: conversationHistory,
            chartContext: buildChartContextPayload(dashboardChart),
          }),
        ),
      }).then(async (res) => {
        const payload = await res.json();
        if (!res.ok) {
          throw new Error(payload.error || TEXT.submitError);
        }
        return payload;
      });

      setMessages((current) => [
        ...current,
        buildAssistantMessage(response, {
          originalQuestion: trimmed,
          fallbackText: TEXT.emptySummary,
          overviewTitle: "系統摘要",
          assistantTitle: "AI 分析回覆",
        }),
      ]);

      const chartPayload = extractChartPayloadFromAskResponse(response);
      if (chartPayload) {
        setDashboardChart(chartPayload);
        setSelectedChartKey(chartPayload.chart_key || "");
      }
    } catch (submitError) {
      setError(submitError.message || TEXT.submitError);
    } finally {
      setBusy(false);
    }
  }

  function updateObservationSelection(field, value) {
    setObservationSelection((current) => {
      if (!current) return current;

      const next = { ...current, [field]: value };

      if (field === "row_dimension") {
        next.row_dimension = normalizeObservationDimension(value);
        next.platform = "";
        next.group_code = "";
        next.product_line_5 = "";
        next.compare_mode = getValidCompareMode(observationOptions, next.row_dimension, next.compare_mode);
      }

      if (field === "compare_mode") {
        next.compare_mode = getValidCompareMode(observationOptions, next.row_dimension, value);
        if (next.compare_mode === "none") {
          next.compare_month = "";
        }
      }

      if (field === "current_month" || field === "compare_mode" || field === "row_dimension") {
        return syncPreviousCompareMonth(next, observationOptions);
      }

      return next;
    });
  }

  const projectOverview = summary?.project_overview || {};
  const recentSnapshot = summary?.recent_snapshot || {};
  const dashboardSnapshot = summary?.dashboard_snapshot || {};
  const latestMonth = getLatestMonthLabel(summary, TEXT.noData);

  const topSummaryCards = buildKpiItems(
    summary,
    {
      noData: TEXT.noData,
      momLabel: TEXT.monthOverMonth,
      currentRevenueLabel: TEXT.statCurrentRevenue,
      currentInventoryLabel: TEXT.statCurrentInventory,
      recentRevenueLabel: TEXT.statRecentRevenue,
      recentInventoryLabel: TEXT.statRecentInventory,
      topRevenuePlatformLabel: TEXT.statTopRevenuePlatform,
      topRevenueProductLineLabel: TEXT.statTopRevenueProductLine,
      topInventoryPlatformLabel: TEXT.statTopInventoryPlatform,
      minRevenuePlatformLabel: TEXT.minRevenuePlatform,
      minRevenueProductLineLabel: TEXT.minRevenueProductLine,
      minInventoryPlatformLabel: TEXT.minInventoryPlatform,
    },
    { mode: "desktop" },
  );

  const snapshotItems = buildSnapshotItems(
    summary,
    {
      noData: TEXT.noData,
      topRevenuePlatformLabel: TEXT.statTopRevenuePlatform,
      topRevenueProductLineLabel: TEXT.statTopRevenueProductLine,
      topInventoryPlatformLabel: TEXT.statTopInventoryPlatform,
      minRevenuePlatformLabel: TEXT.minRevenuePlatform,
      minRevenueProductLineLabel: TEXT.minRevenueProductLine,
      minInventoryPlatformLabel: TEXT.minInventoryPlatform,
    },
    { mode: "desktop" },
  );

  const executiveHeadline = getExecutiveHeadline(summary, TEXT.emptySummary);

  const observationRowDimension = normalizeObservationDimension(observationSelection?.row_dimension);
  const comparisonOptions = getComparisonOptions(observationOptions, observationRowDimension);
  const filterConfig = getObservationFilterConfig(observationRowDimension);
  const filterOptions = getObservationFilterOptions(observationOptions, observationRowDimension);
  const showCompareMonth =
    observationRowDimension !== "month" && observationSelection?.compare_mode === "custom_month";

  return (
    <main className="product-shell">
      <div className="product-backdrop product-backdrop-a" />
      <div className="product-backdrop product-backdrop-b" />

      <header className="topbar">
        <div className="topbar-brand">
          <div className="topbar-mark">
            <LayoutPanelTop size={18} />
          </div>
          <div>
            <div className="topbar-title">Revenue Intelligence Console</div>
            <div className="topbar-subtitle">{TEXT.topbarSubtitle}</div>
          </div>
        </div>

        <div className="topbar-actions">
          <button className="ghost-action" type="button" onClick={() => selectedChartKey && refreshChart(selectedChartKey)}>
            <RefreshCcw size={16} />
            {TEXT.refreshChart}
          </button>
          <div className="model-pill">
            <Bot size={16} />
            Multi-Agent + Chart Agent
          </div>
        </div>
      </header>

      <section className="hero-strip hero-strip-summary">
        <div className="summary-heading">
          <div className="section-kicker">Latest Month Review</div>
          <h1>{TEXT.heroTitle}</h1>
          <p>{executiveHeadline}</p>
        </div>

        <div className="hero-metrics summary-metrics-grid">
          {topSummaryCards.map((card) => (
            <KpiCard key={card.label} label={card.label} value={card.value} helper={card.helper} variant="desktop" />
          ))}
        </div>
      </section>

      <section className="workspace-grid">
        <section className="conversation-panel">
          <div className="panel-heading">
            <div>
              <div className="section-kicker">Conversation</div>
              <h2>{TEXT.conversationPanelTitle}</h2>
            </div>
            <div className="inline-tag">
              <Sparkles size={16} />
              {TEXT.structuredReport}
            </div>
          </div>

          <div className="message-thread" ref={messageThreadRef}>
            {messages.map((message) => (
              <MessageCard key={message.id} message={message} />
            ))}
            <div ref={messagesEndRef} aria-hidden="true" />
          </div>

          <form
            className="composer-shell"
            onSubmit={(event) => {
              event.preventDefault();
              submitQuestionShared(draft);
            }}
          >
            <label className="composer-label" htmlFor="analysis-question">
              {TEXT.promptLabel}
            </label>
            <textarea
              id="analysis-question"
              className="composer-input"
              placeholder={TEXT.promptPlaceholder}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
            />
            <div className="composer-footer">
              <div className="composer-meta">{busy ? TEXT.metaBusy : TEXT.metaIdle}</div>
              <button className="primary-action" type="submit" disabled={busy || !draft.trim()}>
                <SendHorizonal size={16} />
                {busy ? TEXT.sending : TEXT.send}
              </button>
            </div>
          </form>

          <section className="suggestion-panel">
            <div className="suggestion-header">
              <div className="suggestion-title">{TEXT.suggestionTitle}</div>
              <div className="suggestion-subtitle">{TEXT.suggestionSubtitle}</div>
            </div>
            <div className="quick-actions quick-actions-bottom">
              {SHARED_QUICK_PROMPTS.map((prompt) => (
                <button key={prompt} type="button" className="quick-prompt" onClick={() => submitQuestionShared(prompt)} disabled={busy}>
                  {prompt}
                </button>
              ))}
            </div>
          </section>

          {error ? <div className="error-banner">{error}</div> : null}
        </section>

        <aside className="dashboard-panel">
          <div className="panel-heading">
            <div>
              <div className="section-kicker">Dashboard</div>
              <h2>{TEXT.dashboardTitle}</h2>
            </div>
            <div className="dashboard-filter">
              <BarChart3 size={16} />
              {TEXT.dashboardTag}
            </div>
          </div>

          <div className="dashboard-toolbar">
            <div className="select-shell">
              <span>{TEXT.selectChart}</span>
              <div className="select-wrap">
                <select value={selectedChartKey} onChange={(event) => refreshChart(event.target.value)}>
                  {chartCatalog.map((item) => (
                    <option key={item.chart_key} value={item.chart_key} disabled={!item.available}>
                      {item.title}
                    </option>
                  ))}
                </select>
                <ChevronDown size={16} />
              </div>
            </div>
          </div>

          <section className="chart-panel">
            <div className="chart-panel-header">
              <div>
                <div className="chart-title">{dashboardChart?.title || TEXT.chartNotLoaded}</div>
                <div className="chart-subtitle">
                  {dashboardChart?.filters?.month || dashboardChart?.filters?.platform || dashboardChart?.filters?.group_code
                    ? TEXT.chartFiltered
                    : TEXT.chartIdle}
                </div>
              </div>
            </div>
            <ChartSurface payload={dashboardChart} />
            {dashboardChart?.table_preview?.length ? (
              <div className="chart-table-shell">
                <div className="chart-table-title">{TEXT.chartTableTitle}</div>
                <div className="chart-table-wrap">
                  <table className="chart-table">
                    <thead>
                      <tr>
                        {Object.keys(dashboardChart.table_preview[0]).map((column) => (
                          <th key={column}>{column}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {dashboardChart.table_preview.slice(0, 8).map((row, index) => (
                        <tr key={`${dashboardChart.chart_key || "chart"}-${index}`}>
                          {Object.entries(row).map(([column, value]) => (
                            <td key={`${column}-${index}`}>{value ?? TEXT.noData}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : null}
          </section>

          <section className="dashboard-card">
            <div className="dashboard-card-title">{TEXT.snapshotTitle}</div>
            <div className="snapshot-grid">
              {snapshotItems.map((item) => (
                <SharedSnapshotItem
                  key={item.label}
                  label={item.label}
                  value={item.value}
                  helper={item.helper}
                  variant="desktop"
                />
              ))}
            </div>

            <div className="anomaly-panel">
              <div className="anomaly-title">
                {TEXT.currentMonthAnomalies} ({dashboardSnapshot.latest_month || latestMonth})
              </div>
              {dashboardSnapshot.anomalies?.length ? (
                <ul className="anomaly-list">
                  {dashboardSnapshot.anomalies.map((item, index) => (
                    <li key={`${item.month}-${item.platform}-${item.type}-${index}`}>
                      <strong>{item.platform || "未標示事業群"}</strong>
                      <span>{item.reason || item.type || TEXT.noData}</span>
                      <em>{formatCompactNumber(item.signal, { maximumFractionDigits: 2 })}</em>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="anomaly-empty">{TEXT.noCurrentMonthAnomalies}</div>
              )}
            </div>
          </section>
        </aside>
      </section>

      <section className="observation-shell">
        <div className="observation-header">
          <div>
            <div className="section-kicker">Observation</div>
            <h2>{TEXT.observationTitle}</h2>
            <p>{TEXT.observationSubtitle}</p>
          </div>
          <button
            className="primary-action"
            type="button"
            onClick={() => fetchObservationTable(observationSelection)}
            disabled={!observationSelection || observationBusy}
          >
            <RefreshCcw size={16} />
            {observationBusy ? TEXT.observationLoading : TEXT.observationApply}
          </button>
        </div>

        <div className="observation-controls">
          <label className="observation-field">
            <span>{TEXT.observationRowDimension}</span>
            <select
              value={observationSelection?.row_dimension || "business_group"}
              onChange={(event) => updateObservationSelection("row_dimension", event.target.value)}
            >
              {(observationOptions?.row_dimensions || []).map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <label className="observation-field">
            <span>{TEXT.observationMetric}</span>
            <select
              value={observationSelection?.metric || "revenue"}
              onChange={(event) => updateObservationSelection("metric", event.target.value)}
            >
              {(observationOptions?.metrics || []).map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <label className="observation-field">
            <span>{TEXT.observationCompareMode}</span>
            <select
              value={observationSelection?.compare_mode || "previous_period"}
              onChange={(event) => updateObservationSelection("compare_mode", event.target.value)}
            >
              {comparisonOptions.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <label className="observation-field">
            <span>{TEXT.observationCurrentMonth}</span>
            <select
              value={observationSelection?.current_month || ""}
              onChange={(event) => updateObservationSelection("current_month", event.target.value)}
            >
              {(observationOptions?.months || []).map((month) => (
                <option key={month} value={month}>
                  {month}
                </option>
              ))}
            </select>
          </label>

          {showCompareMonth ? (
            <label className="observation-field">
              <span>{TEXT.observationCompareMonth}</span>
              <select
                value={observationSelection?.compare_month || ""}
                onChange={(event) => updateObservationSelection("compare_month", event.target.value)}
              >
                {(observationOptions?.months || []).map((month) => (
                  <option key={month} value={month}>
                    {month}
                  </option>
                ))}
              </select>
            </label>
          ) : null}

          <label className="observation-field">
            <span>{filterConfig.label}</span>
            <select
              value={observationSelection?.[filterConfig.stateKey] || ""}
              onChange={(event) => updateObservationSelection(filterConfig.stateKey, event.target.value)}
            >
              <option value="">{filterConfig.allLabel}</option>
              {filterOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>

        </div>

        <div className="observation-board">
          <div className="observation-board-header">
            <div>
              <div className="observation-board-title">{observationResult?.title || TEXT.observationTitle}</div>
              <div className="observation-board-subtitle">
                {observationResult?.message || TEXT.observationMessageDefault}
              </div>
            </div>
          </div>

          {observationResult?.rows?.length ? (
            <div className="observation-table-wrap">
              <table className="observation-table">
                <thead>
                  <tr>
                    {(observationResult.columns || []).map((column) => (
                      <th key={column}>{column}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {observationResult.rows.map((row, index) => (
                    <tr key={`observe-row-${index}`}>
                      {(observationResult.columns || []).map((column) => {
                        const rawValue = row[column];
                        const tone = valueTone(column, rawValue);
                        return (
                          <td key={`${column}-${index}`} className={tone ? `tone-${tone}` : ""}>
                            {formatObservationValue(column, rawValue)}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="observation-empty">
              {observationBusy ? TEXT.observationLoading : observationResult?.message || TEXT.observationEmpty}
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
