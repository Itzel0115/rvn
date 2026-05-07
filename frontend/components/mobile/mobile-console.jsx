"use client";

import { useEffect, useMemo, useState } from "react";
import {
  BarChart3,
  ChevronDown,
  MessageCircle,
  RefreshCcw,
  SendHorizonal,
  Sparkles,
  X,
} from "lucide-react";

import {
  buildAskRequestBody,
  createAssistantMessage,
  createErrorMessage,
  createUserMessage,
} from "@/components/chat/chat-utils";
import { buildChartContextPayload, extractChartPayloadFromAskResponse } from "@/components/chat/chart-evidence";
import {
  buildHighlights,
  getDisplayHeadline,
  getDisplayLimitations,
  getDisplayTable,
  hasDisplayBlocks,
} from "@/components/chat/display-blocks";
import { EXECUTIVE_QUICK_PROMPTS } from "@/components/chat/quick-prompts";
import { KpiCard } from "@/components/kpi/kpi-card";
import { SnapshotItem } from "@/components/kpi/snapshot-item";
import { buildKpiItems, buildSnapshotItems, getExecutiveHeadline, getLatestMonthLabel } from "@/components/kpi/kpi-utils";
import { MobileChartSurface } from "@/components/mobile/mobile-chart-surface";

const DEFAULT_MESSAGE = {
  id: "welcome",
  role: "assistant",
  title: "AI Assistant",
  text: "資料載入後，這裡會顯示最新月份摘要，也可以直接打開抽屜提問。",
};

function asList(value) {
  return Array.isArray(value) ? value : [];
}

function buildWelcomeMessage(summary) {
  return {
    ...DEFAULT_MESSAGE,
    text: getExecutiveHeadline(summary, "目前尚未載入摘要資料。"),
  };
}

function LegacyMessageBubble({ message }) {
  const paragraphs = String(message.text || "")
    .split(/\n{2,}/)
    .map((item) => item.trim())
    .filter(Boolean);

  return (
    <article className={`mobile-exec-message-bubble ${message.role}`}>
      <div className="mobile-exec-message-eyebrow">
        {message.title || (message.role === "user" ? "你的問題" : "AI 助理")}
      </div>
      <div className="mobile-exec-message-copy">
        {paragraphs.length ? paragraphs.map((paragraph, index) => <p key={`${message.id}-${index}`}>{paragraph}</p>) : <p>-</p>}
      </div>
    </article>
  );
}

function formatMobileCell(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  if (typeof value === "number") {
    return new Intl.NumberFormat("zh-TW", { maximumFractionDigits: 2 }).format(value);
  }
  return String(value);
}

function MessageBubble({ message }) {
  const paragraphs = String(message.text || "")
    .split(/\n{2,}/)
    .map((item) => item.trim())
    .filter(Boolean);
  const displayBlocksAvailable = hasDisplayBlocks(message);
  const headline = getDisplayHeadline(message);
  const highlights = buildHighlights(message);
  const table = getDisplayTable(message, { compact: true });
  const limitations = getDisplayLimitations(message);

  return (
    <article className={`mobile-exec-message-bubble ${message.role}`}>
      <div className="mobile-exec-message-eyebrow">
        {message.title || (message.role === "user" ? "User" : "AI Assistant")}
      </div>
      <div className="mobile-exec-message-copy">
        {headline ? <p className="mobile-exec-message-headline">{headline}</p> : null}
        {!displayBlocksAvailable && paragraphs.length
          ? paragraphs.map((paragraph, index) => <p key={`${message.id}-${index}`}>{paragraph}</p>)
          : null}
        {!displayBlocksAvailable && !paragraphs.length && !headline ? <p>-</p> : null}
      </div>

      {highlights.length ? (
        <ul className="mobile-exec-message-list">
          {highlights.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : null}

      {table ? (
        <div className="mobile-exec-message-table-wrap">
          <table className="mobile-exec-message-table">
            <thead>
              <tr>
                {table.columns.map((column) => (
                  <th key={column}>{column}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {table.rows.map((row, rowIndex) => (
                <tr key={`mobile-display-row-${rowIndex}`}>
                  {table.columns.map((column) => (
                    <td key={`${column}-${rowIndex}`}>{formatMobileCell(row[column])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {limitations.length ? (
        <details className="mobile-exec-message-details">
          <summary>Limitations</summary>
          <ul>
            {limitations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </details>
      ) : null}
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

  const latestMonth = getLatestMonthLabel(summary, "-");
  const dashboardSnapshot = summary?.dashboard_snapshot || {};
  const executiveHeadline = useMemo(
    () => getExecutiveHeadline(summary, "資料載入後，這裡會顯示最新月份的 executive summary。"),
    [summary],
  );
  const anomalies = asList(dashboardSnapshot.anomalies).slice(0, 3);

  const kpiTiles = useMemo(
    () =>
      buildKpiItems(
        summary,
        {
          noData: "-",
          momLabel: "月變化",
          currentRevenueLabel: "本月營收",
          currentInventoryLabel: "本月庫存",
          anomalyLabel: "風險訊號",
          latestDetectedLabel: "最新偵測",
        },
        { mode: "mobile" },
      ),
    [summary],
  );

  const snapshotItems = useMemo(
    () =>
      buildSnapshotItems(
        summary,
        {
          noData: "-",
          topRevenuePlatformLabel: "營收最高平台",
          topInventoryPlatformLabel: "庫存最高平台",
        },
        { mode: "mobile" },
      ),
    [summary],
  );

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

      if (payload.error) {
        throw new Error(payload.error);
      }

      setDashboardChart(payload.chart || null);
    } catch (err) {
      setError(err.message || "圖表目前無法更新。");
    } finally {
      setChartBusy(false);
    }
  }

  async function submitQuestionShared(question) {
    const trimmed = question.trim();
    if (!trimmed || busy) return;

    setBusy(true);
    setError("");
    setDraft("");
    setDrawerOpen(true);
    setMessages((current) => [...current, createUserMessage(trimmed, { title: "你的問題" })]);

    try {
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          buildAskRequestBody(trimmed, {
            chartContext: buildChartContextPayload(dashboardChart),
          }),
        ),
      }).then(async (item) => {
        const payload = await item.json();
        if (!item.ok) {
          throw new Error(payload.error || "AI 助理目前無法回應。");
        }
        if (payload.error) {
          throw new Error(payload.error);
        }
        return payload;
      });

      const chartPayload = extractChartPayloadFromAskResponse(response);
      if (chartPayload) {
        setDashboardChart(chartPayload);
        setSelectedChartKey(chartPayload.chart_key || "");
      }

      setMessages((current) => [
        ...current,
        createAssistantMessage(response, {
          assistantTitle: (payload) =>
            payload.routing?.question_type ? `AI 助理 · ${payload.routing.question_type}` : "AI 助理",
          fallbackText: "目前沒有可顯示的回覆。",
        }),
      ]);
    } catch (err) {
      const message = err.message || "AI 助理目前無法回應。";
      setError(message);
      setMessages((current) => [
        ...current,
        createErrorMessage(err, {
          title: "系統提醒",
          fallbackText: "AI 助理目前無法回應。",
        }),
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
        if (!ignore) {
          setError(err.message || "初始化資料時發生問題。");
        }
      }
    }

    bootstrap();
    return () => {
      ignore = true;
    };
  }, []);

  return (
    <div className="mobile-route">
      <main className="mobile-exec-shell">
        <header className="mobile-exec-topbar">
          <div className="mobile-exec-brand-lockup">
            <div className="mobile-exec-brand-mark">
              <BarChart3 size={18} />
            </div>
            <div>
              <div className="mobile-exec-brand-title">Revenue Intelligence Console</div>
              <div className="mobile-exec-brand-subtitle">Mobile executive demo</div>
            </div>
          </div>
          <button className="mobile-exec-icon-button" type="button" onClick={() => selectedChartKey && refreshChart(selectedChartKey)}>
            <RefreshCcw size={17} />
            <span>刷新</span>
          </button>
        </header>

        <section className="mobile-exec-brief">
          <div className="mobile-exec-section-kicker">Latest Month Review · {latestMonth}</div>
          <h1>營運摘要 executive view</h1>
          <p>{executiveHeadline}</p>
        </section>

        <section className="mobile-exec-metric-strip">
          {kpiTiles.map((item) => (
            <KpiCard key={item.label} {...item} variant="mobile" />
          ))}
        </section>

        <section className="mobile-exec-chart-card">
          <div className="mobile-exec-chart-card-header">
            <div>
              <div className="mobile-exec-section-kicker">Dashboard</div>
              <h2>{dashboardChart?.title || "尚未載入圖表"}</h2>
            </div>
            <div className="mobile-exec-chart-status">
              <Sparkles size={14} />
              {chartBusy ? "載入中" : "就緒"}
            </div>
          </div>

          <label className="mobile-exec-select-shell">
            <span>圖表</span>
            <div className="mobile-exec-select-wrap">
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

          <MobileChartSurface payload={dashboardChart} />
        </section>

        <section className="mobile-exec-snapshot-list">
          {snapshotItems.map((item) => (
            <SnapshotItem key={item.label} label={item.label} value={item.value} helper={item.helper} variant="mobile" />
          ))}
        </section>

        <section className="mobile-exec-risk-panel">
          <div className="mobile-exec-risk-title">最近風險訊號</div>
          {anomalies.length ? (
            <ul>
              {anomalies.map((item, index) => (
                <li key={`${item.platform}-${item.type}-${index}`}>
                  <strong>{item.platform || "-"}</strong>
                  <span>{item.reason || item.type || "風險訊號"}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p>目前最新月份尚未偵測到需要特別追蹤的風險訊號。</p>
          )}
        </section>

        {error ? <div className="mobile-exec-error-banner">{error}</div> : null}

        <button className="mobile-exec-ai-fab" type="button" onClick={() => setDrawerOpen(true)}>
          <MessageCircle size={19} />
          AI
        </button>

        {drawerOpen ? (
          <button className="mobile-exec-drawer-backdrop" aria-label="Close AI drawer" onClick={() => setDrawerOpen(false)} />
        ) : null}

        <aside className={`mobile-exec-chat-drawer ${drawerOpen ? "open" : ""}`} aria-hidden={!drawerOpen}>
          <div className="mobile-exec-chat-header">
            <div>
              <div className="mobile-exec-section-kicker">AI Assistant</div>
              <h2>營運分析助理</h2>
            </div>
            <button className="mobile-exec-icon-button mobile-exec-square-button" type="button" onClick={() => setDrawerOpen(false)}>
              <X size={18} />
            </button>
          </div>

          <div className="mobile-exec-quick-prompts">
            {EXECUTIVE_QUICK_PROMPTS.map((prompt) => (
              <button key={prompt} type="button" onClick={() => submitQuestionShared(prompt)} disabled={busy}>
                {prompt}
              </button>
            ))}
          </div>

          <div className="mobile-exec-message-thread">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
          </div>

          <form
            className="mobile-exec-chat-composer"
            onSubmit={(event) => {
              event.preventDefault();
              submitQuestionShared(draft);
            }}
          >
            <label htmlFor="mobile-question">輸入問題</label>
            <textarea
              id="mobile-question"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="例如：最近有什麼營運風險？"
            />
            <button className="mobile-exec-send-button" type="submit" disabled={busy || !draft.trim()}>
              <SendHorizonal size={17} />
              {busy ? "送出中" : "送出"}
            </button>
          </form>
        </aside>
      </main>
    </div>
  );
}
