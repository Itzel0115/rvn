export function createMessageId(prefix = "msg") {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2, 10)}`;
}

export function buildAskRequestBody(question, options = {}) {
  const payload = { question };

  if (Array.isArray(options.history) && options.history.length) {
    payload.history = options.history;
  }

  if (options.chartContext) {
    payload.chart_context = options.chartContext;
  }

  return payload;
}

export function buildConversationHistory(messages, { limit = 6, roles = ["user", "assistant"] } = {}) {
  return (messages || [])
    .filter((item) => roles.includes(item.role))
    .slice(-limit)
    .map((item) => ({
      role: item.role,
      text: item.text,
    }));
}

export function getAnswerContractFromAskResponse(response) {
  return response?.answer_contract || null;
}

export function getAnswerSummaryFromAskResponse(response, fallbackText = "") {
  return response?.summary || fallbackText;
}

export function getAnswerTextFromAskResponse(response, fallbackText = "") {
  return getAnswerContractFromAskResponse(response)?.answer || getAnswerSummaryFromAskResponse(response, fallbackText);
}

export function getErrorMessage(error, fallbackText) {
  return error?.message || fallbackText;
}

export function createUserMessage(text, overrides = {}) {
  return {
    id: overrides.id || createMessageId("user"),
    role: "user",
    title: overrides.title,
    text,
    ...overrides,
  };
}

export function createAssistantMessage(response, options = {}) {
  const questionType = response?.routing?.question_type;
  const role = questionType === "overview" ? options.overviewRole || "system" : options.role || "assistant";
  const title =
    questionType === "overview"
      ? options.overviewTitle || options.systemTitle || "System"
      : typeof options.assistantTitle === "function"
        ? options.assistantTitle(response)
        : options.assistantTitle || "AI Assistant";

  return {
    id: response?.request_id || options.id || createMessageId(role),
    role,
    title,
    text: getAnswerTextFromAskResponse(response, options.fallbackText || ""),
    answerContract: response?.answer_contract || null,
    requestId: response?.request_id,
    questionType,
    routing: response?.routing || null,
    subtasks: response?.routing?.subtasks || [],
    domainResults: response?.domain_results || [],
    projectSummary: response?.project_summary || null,
    originalQuestion: options.originalQuestion || null,
  };
}

export function createErrorMessage(error, options = {}) {
  return {
    id: options.id || createMessageId("error"),
    role: options.role || "assistant",
    title: options.title || "Error",
    text: getErrorMessage(error, options.fallbackText || "Something went wrong."),
  };
}

// Backward-compatible aliases for the initial Phase 5D-2 rollout.
export const buildUserMessage = createUserMessage;
export const buildAssistantMessage = createAssistantMessage;
export const buildErrorMessage = createErrorMessage;
