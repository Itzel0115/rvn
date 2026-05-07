const DEFAULT_API_BASE = "http://127.0.0.1:8765";

function getApiBase() {
  return process.env.PYTHON_API_BASE || DEFAULT_API_BASE;
}

export async function proxyPythonJson(path, init = {}) {
  const response = await fetch(`${getApiBase()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers || {}),
    },
    cache: "no-store",
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = payload?.error || `Python API request failed: ${response.status}`;
    throw new Error(error);
  }
  return payload;
}
