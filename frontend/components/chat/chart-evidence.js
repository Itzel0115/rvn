import { getAnswerContractFromAskResponse, getAnswerSummaryFromAskResponse, getAnswerTextFromAskResponse } from "@/components/chat/chat-utils";

function asList(value) {
  return Array.isArray(value) ? value : [];
}

function looksLikeChartPayload(item) {
  return Boolean(item?.chart_key && item?.chart_type && item?.series);
}

function findChartEvidenceInDomainResults(response) {
  const chartDomain = asList(response?.domain_results).find((item) => item.domain === "chart");
  if (!chartDomain) return null;
  return asList(chartDomain.evidence).find(looksLikeChartPayload) || null;
}

function findChartEvidenceInAnswerContract(response) {
  return asList(response?.answer_contract?.evidence).find(looksLikeChartPayload) || null;
}

export function extractChartPayloadFromAskResponse(response) {
  return findChartEvidenceInDomainResults(response) || findChartEvidenceInAnswerContract(response) || null;
}

export function buildChartContextPayload(chartPayload) {
  if (!chartPayload) return null;

  return {
    chart_key: chartPayload.chart_key,
    chart_type: chartPayload.chart_type,
    title: chartPayload.title,
    filters: chartPayload.filters,
  };
}

export { getAnswerContractFromAskResponse, getAnswerSummaryFromAskResponse, getAnswerTextFromAskResponse };
