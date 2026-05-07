"use client";

import { useEffect, useMemo, useState } from "react";
import {
  BarChart3,
  Bot,
  ChevronDown,
  MessageCircle,
  RefreshCcw,
  SendHorizonal,
  Sparkles,
  X,
} from "lucide-react";

import { ChartSurface } from "@/components/chart-surface";

const QUICK_PROMPTS = [
  "哪個平台表現最差？",
  "目前有哪些高風險平台？",
  "最近營收趨勢如何？",
];

const DEFAULT_MESSAGE = {
  id: "welcome",
  role: "assistant",
  title: "AI 分析助手",
  text: "我可以協助判斷平台表現、庫存效率、營收趨勢與本月風險。請直接輸入主管想知道的問題。",
};

function newId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function formatNumber(value, options = {}) {
  if (value === null || value === undefined || value === "") return "-";
  const number = Number(value);
  if (!Number.isFinite(number)) return String(value);
  return new Intl.NumberFormat("zh-TW", {
    maximumFractionDigits: 2,
    ...options,
  }).format(number);
}

function formatPercent(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "-";
  const number = Number(value);
  const percent = Math.abs(number) <= 1 ? number * 100 : number;
  return `${formatNumber(percent, { maximumFractionDigits: 2 })}%`;
}

function asList(value) {
  return Array.isArray(value) ? value : [];
}

function extractChartFromResponse(response) {
  const chartDomain = asList(response?.domain_results).find((item) => item.domain === "chart");
  if (!chartDomain) return null;
  return asList(chartDomain.evidence).find((item) => item?.chart_type && item?.series) || null;
}

function buildWelcomeMessage(summary) {
  const latest = summary?.latest_month_analysis || "手機主管版已就緒，可從圖表或 AI 問答快速檢視本月狀況。";
  return {
    ...DEFAULT_MESSAGE,
    text: latest,
  };
}

function MetricTile({ label, value, helper, tone = "neutral" }) {
  return (
    <div className={`metric-tile ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{helper}</small>
    </div>
  );
}

function MessageBubble({ message }) {
  const paragraphs = String(message.text || "")
    .split(/\n{2,}/)
    .map((item) => item.trim())
    .filter(Boolean);

  return (
    <article className={`message-bubble ${message.role}`}>
      <div className="message-eyebrow">{message.title || (message.role === "user" ? "你的問題" : "分析結果")}</div>
      <div className="message-copy">
        {paragraphs.length ? (
          paragraphs.map((paragraph, index) => <p key={`${message.id}-${index}`}>{paragraph}</p>)
        ) : (
          <p>-</p>
        )}
      </div>
    </article>
  );
}

export function MobileConsole() {
  const [summary, setSummary] = useState(null);
  const [chartCatalog, setChartCatalog] = useState([]);
  const [selectedChartKey, setSelectedChartKey] = useState("");
  const [dashboardChart, setDashboardChart] = useState(null);
  const [messages, setMessages] = useState([DEFAULT_MESSAGE]);
  const [draft, setDraft] = useState("");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [chartBusy, setChartBusy] = useState(false);
  const [error, setError] = useState("");

  const latestMonth = summary?.recent_snapshot?.latest_month || summary?.dashboard_snapshot?.latest_month || "-";
  const dashboardSnapshot = summary?.dashboard_snapshot || {};
  const recentSnapshot = summary?.recent_snapshot || {};

  const executiveHeadline = useMemo(() => {
    return summary?.latest_month_analysis || "載入分析摘要中，請確認 Python API 已啟動。";
  }, [summary]);

  const kpiTiles = useMemo(() => {
    const currentMonth = recentSnapshot.current_month || {};
    return [
      {
        label: "本月營收",
        value: formatNumber(currentMonth.revenue),
        helper: `月增率 ${formatPercent(currentMonth.revenue_mom)}`,
        tone: "good",
      },
      {
        label: "本月庫存",
        value: formatNumber(currentMonth.inventory_amount),
        helper: `月增率 ${formatPercent(currentMonth.inventory_amount_mom)}`,
        tone: "watch",
      },
      {
        label: "高風險訊號",
        value: formatNumber(asList(dashboardSnapshot.anomalies).length, { maximumFractionDigits: 0 }),
        helper: `${latestMonth} 最新觀測`,
        tone: asList(dashboardSnapshot.anomalies).length ? "risk" : "good",
      },
    ];
  }, [dashboardSnapshot.anomalies, latestMonth, recentSnapshot.current_month]);

  async function refreshChart(chartKey) {
    if (!chartKey) return;
    setChartBusy(true);
    setError("");
    try {
      setSelectedChartKey(chartKey);
      const payload = await fetch("/api/chart", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chart_key: chartKey, render_image: false }),
      }).then((response) => response.json());
      if (payload.error) throw new Error(payload.error);
      setDashboardChart(payload.chart || null);
    } catch (err) {
      setError(err.message || "圖表載入失敗");
    } finally {
      setChartBusy(false);
    }
  }

  async function submitQuestion(question) {
    const trimmed = question.trim();
    if (!trimmed || busy) return;

    setBusy(true);
    setError("");
    setDraft("");
    setDrawerOpen(true);

    const userMessage = { id: newId(), role: "user", title: "你的問題", text: trimmed };
    setMessages((current) => [...current, userMessage]);

    try {
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: trimmed,
          chart_context: dashboardChart
            ? {
                chart_key: dashboardChart.chart_key,
                chart_type: dashboardChart.chart_type,
                title: dashboardChart.title,
                filters: dashboardChart.filters,
              }
            : null,
        }),
      }).then((item) => item.json());

      if (response.error) throw new Error(response.error);

      const chartPayload = extractChartFromResponse(response);
      if (chartPayload) {
        setDashboardChart(chartPayload);
        setSelectedChartKey(chartPayload.chart_key || "");
      }

      setMessages((current) => [
        ...current,
        {
          id: newId(),
          role: "assistant",
          title: response.routing?.question_type ? `分析結果 · ${response.routing.question_type}` : "分析結果",
          text: response.summary || "目前沒有可呈現的回答。",
        },
      ]);
    } catch (err) {
      const message = err.message || "AI 問答失敗";
      setError(message);
      setMessages((current) => [
        ...current,
        {
          id: newId(),
          role: "assistant",
          title: "系統提醒",
          text: message,
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    let ignore = false;

    async function bootstrap() {
      try {
        const [summaryPayload, chartPayload] = await Promise.all([
          fetch("/api/summary", { cache: "no-store" }).then((response) => response.json()),
          fetch("/api/chart-catalog", { cache: "no-store" }).then((response) => response.json()),
        ]);
        if (ignore) return;
        if (summaryPayload.error) throw new Error(summaryPayload.error);
        if (chartPayload.error) throw new Error(chartPayload.error);

        setSummary(summaryPayload);
        setMessages([buildWelcomeMessage(summaryPayload)]);

        const charts = chartPayload.charts || [];
        setChartCatalog(charts);
        const firstAvailable = charts.find((item) => item.available);
        if (firstAvailable) {
          await refreshChart(firstAvailable.chart_key);
        }
      } catch (err) {
        if (!ignore) setError(err.message || "初始化失敗");
      }
    }

    bootstrap();
    return () => {
      ignore = true;
    };
  }, []);

  const topRevenue = dashboardSnapshot.revenue_extremes?.max;
  const topInventory = dashboardSnapshot.inventory_extremes?.max;
  const anomalies = asList(dashboardSnapshot.anomalies).slice(0, 3);

  return (
    <main className="mobile-shell">
      <header className="mobile-topbar">
        <div className="brand-lockup">
          <div className="brand-mark">
            <BarChart3 size={18} />
          </div>
          <div>
            <div className="brand-title">Revenue Intelligence Console</div>
            <div className="brand-subtitle">主管手機版 Demo</div>
          </div>
        </div>
        <button className="icon-button" type="button" onClick={() => selectedChartKey && refreshChart(selectedChartKey)}>
          <RefreshCcw size={17} />
          <span>更新</span>
        </button>
      </header>

      <section className="executive-brief">
        <div className="section-kicker">Latest Month Review · {latestMonth}</div>
        <h1>營收與庫存重點看板</h1>
        <p>{executiveHeadline}</p>
      </section>

      <section className="metric-strip">
        {kpiTiles.map((item) => (
          <MetricTile key={item.label} {...item} />
        ))}
      </section>

      <section className="chart-card">
        <div className="chart-card-header">
          <div>
            <div className="section-kicker">Dashboard</div>
            <h2>{dashboardChart?.title || "主要圖表"}</h2>
          </div>
          <div className="chart-status">
            <Sparkles size={14} />
            {chartBusy ? "載入中" : "即時"}
          </div>
        </div>

        <label className="select-shell">
          <span>切換圖表</span>
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
        </label>

        <ChartSurface payload={dashboardChart} />
      </section>

      <section className="snapshot-list">
        <div className="snapshot-item">
          <span>營收最高平台</span>
          <strong>{topRevenue?.platform || "-"}</strong>
          <small>{formatNumber(topRevenue?.value ?? topRevenue?.revenue)}</small>
        </div>
        <div className="snapshot-item">
          <span>庫存最高平台</span>
          <strong>{topInventory?.platform || "-"}</strong>
          <small>{formatNumber(topInventory?.value ?? topInventory?.inventory_amount)}</small>
        </div>
      </section>

      <section className="risk-panel">
        <div className="risk-title">本月風險觀測</div>
        {anomalies.length ? (
          <ul>
            {anomalies.map((item, index) => (
              <li key={`${item.platform}-${item.type}-${index}`}>
                <strong>{item.platform || "-"}</strong>
                <span>{item.reason || item.type || "異常訊號"}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p>目前最新月份沒有主要異常訊號。</p>
        )}
      </section>

      {error ? <div className="error-banner">{error}</div> : null}

      <button className="ai-fab" type="button" onClick={() => setDrawerOpen(true)}>
        <MessageCircle size={19} />
        問 AI
      </button>

      {drawerOpen ? <button className="drawer-backdrop" aria-label="關閉 AI 對話" onClick={() => setDrawerOpen(false)} /> : null}

      <aside className={`chat-drawer ${drawerOpen ? "open" : ""}`} aria-hidden={!drawerOpen}>
        <div className="chat-header">
          <div>
            <div className="section-kicker">AI Assistant</div>
            <h2>問 AI 分析助手</h2>
          </div>
          <button className="icon-button square" type="button" onClick={() => setDrawerOpen(false)}>
            <X size={18} />
          </button>
        </div>

        <div className="quick-prompts">
          {QUICK_PROMPTS.map((prompt) => (
            <button key={prompt} type="button" onClick={() => submitQuestion(prompt)} disabled={busy}>
              {prompt}
            </button>
          ))}
        </div>

        <div className="message-thread">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
        </div>

        <form
          className="chat-composer"
          onSubmit={(event) => {
            event.preventDefault();
            submitQuestion(draft);
          }}
        >
          <label htmlFor="mobile-question">輸入問題</label>
          <textarea
            id="mobile-question"
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            placeholder="例如：哪個平台表現最差？"
          />
          <button className="send-button" type="submit" disabled={busy || !draft.trim()}>
            <SendHorizonal size={17} />
            {busy ? "分析中" : "送出"}
          </button>
        </form>
      </aside>
    </main>
  );
}
