const SCORE_COLUMNS = ["health_score", "risk_score"];
const DEFAULT_EXECUTIVE_COLUMNS = [
  "platform",
  "revenue",
  "inventory_amount",
  "revenue_inventory_ratio",
  "health_score",
  "risk_score",
];

export function uniqueItems(values = []) {
  return [...new Set(values.filter(Boolean))];
}

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

export function getDisplayBlocks(message) {
  return message?.answerContract?.display_blocks || null;
}

export function hasDisplayBlocks(message) {
  const blocks = getDisplayBlocks(message);
  if (!blocks) return false;

  return Boolean(
    blocks.headline ||
      asArray(blocks.key_observations).length ||
      asArray(blocks.limitations).length ||
      asArray(blocks.table?.rows).length,
  );
}

export function buildDomainFindingsFallback(message) {
  return uniqueItems((message?.domainResults || []).flatMap((result) => result.key_findings || []));
}

export function shouldUseDomainFindingsFallback(message) {
  const blocks = getDisplayBlocks(message);
  return !blocks || !asArray(blocks.key_observations).length;
}

export function buildHighlights(message, extras = []) {
  const blocks = getDisplayBlocks(message);
  const displayHighlights = uniqueItems(asArray(blocks?.key_observations));
  if (displayHighlights.length) {
    return displayHighlights;
  }

  return uniqueItems([...asArray(extras), ...buildDomainFindingsFallback(message)]).slice(0, 8);
}

export function getDisplayHeadline(message) {
  return getDisplayBlocks(message)?.headline || "";
}

export function getDisplayLimitations(message) {
  return uniqueItems(asArray(getDisplayBlocks(message)?.limitations));
}

export function getDisplayTable(message, { compact = true } = {}) {
  const table = getDisplayBlocks(message)?.table;
  const rows = asArray(table?.rows);
  if (!table || !rows.length) {
    return null;
  }

  const sourceColumns = asArray(table.columns).length ? table.columns : Object.keys(rows[0] || {});
  let columns = sourceColumns;

  if (compact) {
    const preferred = DEFAULT_EXECUTIVE_COLUMNS.filter((column) => sourceColumns.includes(column));
    const scoreColumns = SCORE_COLUMNS.filter((column) => sourceColumns.includes(column) && !preferred.includes(column));
    columns = preferred.length ? uniqueItems([...preferred, ...scoreColumns]) : sourceColumns.slice(0, 6);
  }

  return {
    columns,
    rows,
  };
}
