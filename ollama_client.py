from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import requests

from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT_SECONDS
from logging_utils import get_logger


@dataclass
class OllamaCallResult:
    ok: bool
    text: str
    data: dict[str, Any] | None
    error: str | None = None


class OllamaClient:
    def __init__(
        self,
        request_id: str,
        model: str = OLLAMA_MODEL,
        base_url: str = OLLAMA_BASE_URL,
        timeout_seconds: int = OLLAMA_TIMEOUT_SECONDS,
    ) -> None:
        self.request_id = request_id
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.logger = get_logger("ollama_client", request_id, domain="llm")

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> OllamaCallResult:
        prompt = self._build_prompt(system_prompt, user_prompt)
        self.logger.info("Calling Ollama model=%s", self.model)
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": temperature},
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            text = payload.get("response", "").strip()
            if not text:
                raise ValueError("Ollama returned an empty response.")
            self.logger.info("Ollama call completed")
            return OllamaCallResult(ok=True, text=text, data=None)
        except Exception as exc:
            error_text = str(exc)
            self.logger.warning("Ollama call failed: %s", error_text)
            return OllamaCallResult(ok=False, text="", data=None, error=error_text)

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
    ) -> OllamaCallResult:
        result = self.generate(system_prompt=system_prompt, user_prompt=user_prompt, temperature=temperature)
        if not result.ok:
            return result

        parsed = self._extract_json_object(result.text)
        if parsed is None:
            error_text = "Failed to parse JSON from Ollama response."
            self.logger.warning(error_text)
            return OllamaCallResult(ok=False, text=result.text, data=None, error=error_text)
        return OllamaCallResult(ok=True, text=result.text, data=parsed)

    @staticmethod
    def _build_prompt(system_prompt: str, user_prompt: str) -> str:
        return (
            f"<system>\n{system_prompt.strip()}\n</system>\n\n"
            f"<user>\n{user_prompt.strip()}\n</user>"
        )

    @staticmethod
    def _extract_json_object(text: str) -> dict[str, Any] | None:
        candidates = [text]
        fenced_match = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
        candidates.extend(fenced_match)

        brace_match = re.search(r"(\{.*\})", text, flags=re.DOTALL)
        if brace_match:
            candidates.append(brace_match.group(1))

        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
            except Exception:
                continue
            if isinstance(parsed, dict):
                return parsed
        return None
