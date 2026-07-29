const DEFAULT_API_BASE = "http://127.0.0.1:8765";

function getApiBase() {
  return process.env.PYTHON_API_BASE || DEFAULT_API_BASE;
}

/**
 * 將 dashboard/mobile request 轉送至 Python API，統一處理 JSON 與錯誤。
 * Frontend 不直接讀取 Excel；backend URL 可由 PYTHON_API_BASE 設定。
 */
export async function proxyPythonJson(path, init = {}) {
  const response = await fetch(`${getApiBase()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers || {}),
    },
    cache: "no-store",
  });

  const rawText = await response.text();
  const payload = parsePythonJson(rawText);
  if (!response.ok) {
    const error = payload?.error || `Python API request failed: ${response.status}`;
    throw new Error(error);
  }
  return payload;
}

function parsePythonJson(rawText) {
  if (!rawText) {
    return {};
  }

  try {
    return JSON.parse(rawText);
  } catch {
    const sanitized = rawText
      .replace(/\bNaN\b/g, "null")
      .replace(/\b-Infinity\b/g, "null")
      .replace(/\bInfinity\b/g, "null");
    return JSON.parse(sanitized);
  }
}
