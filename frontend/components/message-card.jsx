"use client";

import clsx from "clsx";

import {
  buildHighlights as buildDisplayHighlights,
  getDisplayBlocks,
  getDisplayHeadline,
  getDisplayLimitations,
  getDisplayTable,
  hasDisplayBlocks,
  uniqueItems,
} from "@/components/chat/display-blocks";

const TEXT = {
  userMeta: "User",
  userTitle: "Question",
  systemMeta: "System",
  systemTitle: "System update",
  agentMeta: "Assistant",
  agentTitle: "Analysis result",
  sectionHeadline: "Executive conclusion",
  sectionHighlights: "Key observations",
  sectionTable: "Comparison table",
  sectionLimitations: "Limitations",
  sectionAgentRuns: "Debug details",
  noData: "N/A",
  confidencePrefix: "confidence:",
};

function cleanParagraph(text) {
  return String(text || "")
    .replace(/^#+\s*/gm, "")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/^[\-\*]\s+/gm, "")
    .replace(/^direct answer:?/gim, "")
    .replace(/^evidence:?/gim, "")
    .replace(/^recommendations?:?/gim, "")
    .replace(/^request id:.*$/gim, "")
    .replace(/^question type:.*$/gim, "")
    .replace(/^router domains:.*$/gim, "")
    .trim();
}

function formatParagraphs(text) {
  return String(text || "")
    .split(/\n{2,}/)
    .map((block) => cleanParagraph(block))
    .filter(Boolean);
}

function flattenFindings(domainResults = []) {
  return uniqueItems(domainResults.flatMap((result) => result.key_findings || []));
}

function flattenWarnings(message) {
  return uniqueItems([
    ...(message.routing?.warnings || []),
    ...((message.domainResults || []).flatMap((result) => result.warnings || [])),
  ]);
}

export function buildHighlights(message) {
  if (getDisplayBlocks(message)) {
    return buildDisplayHighlights(message);
  }

  const findings = flattenFindings(message.domainResults);
  const warnings = flattenWarnings(message);
  const welcome = message.projectSummary?.welcome_highlights || [];
  return uniqueItems([...welcome, ...findings, ...warnings]).slice(0, 8);
}

function buildMeta(message) {
  if (message.role === "user") {
    return {
      eyebrow: TEXT.userMeta,
      title: message.title || TEXT.userTitle,
    };
  }

  if (message.role === "system") {
    return {
      eyebrow: TEXT.systemMeta,
      title: message.title || TEXT.systemTitle,
    };
  }

  return {
    eyebrow: TEXT.agentMeta,
    title: message.title || TEXT.agentTitle,
  };
}

function formatCellValue(value) {
  if (value === null || value === undefined || value === "") {
    return TEXT.noData;
  }

  if (typeof value === "number") {
    return new Intl.NumberFormat("zh-TW", { maximumFractionDigits: 2 }).format(value);
  }

  return String(value);
}

function DisplayTable({ table }) {
  if (!table?.columns?.length || !table?.rows?.length) {
    return null;
  }

  return (
    <div className="message-table-wrap">
      <table className="message-table">
        <thead>
          <tr>
            {table.columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row, rowIndex) => (
            <tr key={`display-row-${rowIndex}`}>
              {table.columns.map((column) => (
                <td key={`${column}-${rowIndex}`}>{formatCellValue(row[column])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DebugDetails({ message }) {
  if (!message.domainResults?.length) {
    return null;
  }

  return (
    <details className="message-section message-debug-details">
      <summary className="message-section-label">{TEXT.sectionAgentRuns}</summary>
      <div className="message-grid">
        {message.domainResults.map((result) => (
          <section key={`${message.id}-${result.domain}`} className="agent-tile">
            <div className="agent-tile-header">
              <span className="agent-domain">{result.domain}</span>
              <span className={`agent-state ${result.status}`}>{result.status}</span>
            </div>
            <div className="agent-task">{result.task}</div>
            <div className="agent-tile-meta">
              {TEXT.confidencePrefix} {result.confidence || TEXT.noData}
            </div>
            <ul className="message-list compact">
              {(result.key_findings || []).slice(0, 3).map((finding) => (
                <li key={finding}>{cleanParagraph(finding)}</li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </details>
  );
}

export function MessageCard({ message }) {
  const meta = buildMeta(message);

  if (message.role === "user") {
    return (
      <article className="message-card message-user">
        <div className="message-meta">{meta.eyebrow}</div>
        <div className="message-title">{message.text}</div>
      </article>
    );
  }

  const paragraphs = formatParagraphs(message.text);
  const highlights = buildHighlights(message);
  const displayBlocksAvailable = hasDisplayBlocks(message);
  const displayHeadline = getDisplayHeadline(message);
  const displayTable = getDisplayTable(message);
  const displayLimitations = getDisplayLimitations(message);
  const showAgentRuns = message.answerContract?.answer_plan?.display_debug_findings !== false;

  return (
    <article
      className={clsx("message-card", {
        "message-system": message.role === "system",
        "message-assistant": message.role === "assistant",
      })}
    >
      <div className="message-header">
        <div>
          <div className="message-meta">{meta.eyebrow}</div>
          <div className="message-title">{meta.title}</div>
        </div>
        <div className="message-badges">
          {message.requestId ? <span className="inline-badge">{message.requestId}</span> : null}
          {message.questionType ? <span className="inline-badge soft">{message.questionType}</span> : null}
        </div>
      </div>

      {displayHeadline ? (
        <section className="message-section">
          <div className="message-section-label">{TEXT.sectionHeadline}</div>
          <div className="message-body report-prose">
            <p>{displayHeadline}</p>
          </div>
        </section>
      ) : null}

      {!displayBlocksAvailable && paragraphs.length ? (
        <section className="message-section">
          <div className="message-body report-prose">
            {paragraphs.map((paragraph) => (
              <p key={paragraph}>{paragraph}</p>
            ))}
          </div>
        </section>
      ) : null}

      {highlights.length ? (
        <section className="message-section">
          <div className="message-section-label">{TEXT.sectionHighlights}</div>
          <ul className="message-list">
            {highlights.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {displayTable ? (
        <section className="message-section">
          <div className="message-section-label">{TEXT.sectionTable}</div>
          <DisplayTable table={displayTable} />
        </section>
      ) : null}

      {displayLimitations.length ? (
        <section className="message-section">
          <div className="message-section-label">{TEXT.sectionLimitations}</div>
          <ul className="message-list">
            {displayLimitations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {showAgentRuns ? <DebugDetails message={message} /> : null}
    </article>
  );
}
