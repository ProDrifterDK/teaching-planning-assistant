import json
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from api.core.config import settings


@dataclass(frozen=True)
class AIUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    prompt_cache_hit_tokens: int = 0
    prompt_cache_miss_tokens: int = 0


@dataclass(frozen=True)
class AITextResult:
    text: str
    model: str
    usage: AIUsage


@dataclass(frozen=True)
class AIJsonResult:
    data: Dict[str, Any]
    raw_text: str
    model: str
    usage: AIUsage


class DeepSeekAIAdapter:
    """OpenAI-compatible adapter for DeepSeek JSON generation."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        client: Optional[Any] = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.AI_API_KEY
        self.base_url = (base_url or settings.AI_BASE_URL).rstrip("/")
        self.model = model or settings.AI_MODEL
        self.timeout_seconds = timeout_seconds or settings.AI_REQUEST_TIMEOUT_SECONDS
        self._client = client

    @property
    def chat_completions_url(self) -> str:
        return f"{self.base_url}/chat/completions"

    async def generate_json(
        self,
        prompt: str,
        *,
        schema: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.4,
        max_tokens: Optional[int] = None,
    ) -> AIJsonResult:
        """Generate and parse a JSON object using DeepSeek JSON mode."""
        if not self.api_key:
            raise RuntimeError(
                "DEEPSEEK_API_KEY is not configured. Set it in Railway or the local environment."
            )

        user_prompt = self._build_json_prompt(prompt, schema)
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt or self._default_system_prompt(),
                },
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        response_payload = await self._post(payload)
        content = self._extract_content(response_payload)
        return AIJsonResult(
            data=self._parse_json_object(content),
            raw_text=content,
            model=response_payload.get("model") or self.model,
            usage=self._extract_usage(response_payload),
        )

    async def generate_text(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AITextResult:
        """Generate plain text/markdown using DeepSeek's chat-completions endpoint."""
        if not self.api_key:
            raise RuntimeError(
                "DEEPSEEK_API_KEY is not configured. Set it in Railway or the local environment."
            )

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                    or "You are an expert Chilean curriculum and lesson-planning assistant.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        response_payload = await self._post(payload)
        return AITextResult(
            text=self._extract_content(response_payload),
            model=response_payload.get("model") or self.model,
            usage=self._extract_usage(response_payload),
        )

    async def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self._client is not None:
            response = await self._client.post(
                self.chat_completions_url,
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
        else:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.chat_completions_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout_seconds,
                )
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _default_system_prompt() -> str:
        return (
            "You are an expert Chilean curriculum and educational content assistant. "
            "Return only one valid JSON object. Do not include markdown, prose, comments, "
            "or text outside the JSON object."
        )

    @staticmethod
    def _build_json_prompt(prompt: str, schema: Optional[Dict[str, Any]]) -> str:
        parts = [
            prompt,
            "",
            "Respond with valid JSON only. The response must be a single JSON object.",
        ]
        if schema:
            parts.extend(
                [
                    "",
                    "JSON Schema to follow:",
                    json.dumps(schema, ensure_ascii=False),
                ]
            )
        return "\n".join(parts)

    @staticmethod
    def _extract_content(response_payload: Dict[str, Any]) -> str:
        choices = response_payload.get("choices") or []
        if not choices:
            raise ValueError("DeepSeek response did not include choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not content:
            raise ValueError("DeepSeek response did not include message content")
        return content

    @staticmethod
    def _parse_json_object(content: str) -> Dict[str, Any]:
        text = content.strip()
        fence_match = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
        if fence_match:
            text = fence_match.group(1).strip()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                raise
            parsed = json.loads(text[start : end + 1])

        if not isinstance(parsed, dict):
            raise ValueError("Expected DeepSeek JSON response to be an object")
        return parsed

    @staticmethod
    def _extract_usage(response_payload: Dict[str, Any]) -> AIUsage:
        usage = response_payload.get("usage") or {}
        details = usage.get("completion_tokens_details") or {}
        return AIUsage(
            prompt_tokens=usage.get("prompt_tokens", 0) or 0,
            completion_tokens=usage.get("completion_tokens", 0) or 0,
            reasoning_tokens=details.get("reasoning_tokens", 0) or 0,
            prompt_cache_hit_tokens=usage.get("prompt_cache_hit_tokens", 0) or 0,
            prompt_cache_miss_tokens=usage.get("prompt_cache_miss_tokens", 0) or 0,
        )


ai_adapter = DeepSeekAIAdapter()
