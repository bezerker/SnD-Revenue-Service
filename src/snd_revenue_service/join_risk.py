"""LLM-based heuristic join risk assessment (OpenAI-compatible Chat Completions API)."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any

from openai import APIError, AsyncOpenAI, RateLimitError

RISK_DISCLAIMER = (
    "Heuristic only — not proof of compromise or automation. "
    "Use with other moderation signals."
)

VALID_CATEGORIES = frozenset(
    {
        "likely_human",
        "uncertain",
        "likely_automation_or_compromise",
    }
)

_SYSTEM_PROMPT = """You assess Discord join risk from API-visible profile data only.
Output a single JSON object with exactly these keys:
- risk_score: integer from 0 (low suspicion) to 100 (high suspicion)
- category: one of: likely_human, uncertain, likely_automation_or_compromise
- rationale: one short paragraph (plain text, no markdown)
- signals: array of short strings listing concrete observations from the data

Rules:
- Discord does not expose compromise status; infer only weak heuristics.
- New accounts and default avatars alone are not definitive.
- Official verified_bot / staff flags reduce suspicion for bots.
- Respond with JSON only, no markdown fences or extra text."""


@dataclass(frozen=True)
class JoinRiskResult:
    risk_score: int
    category: str
    rationale: str
    signals: list[str]


class JoinRiskParseError(ValueError):
    pass


def parse_join_risk_payload(payload: object) -> JoinRiskResult:
    if not isinstance(payload, dict):
        raise JoinRiskParseError("response must be a JSON object")
    data = payload
    try:
        score = int(data["risk_score"])
        category = str(data["category"])
        rationale = str(data["rationale"])
        raw_signals = data["signals"]
    except (KeyError, TypeError, ValueError) as exc:
        raise JoinRiskParseError("missing or invalid required keys") from exc

    if not 0 <= score <= 100:
        raise JoinRiskParseError("risk_score must be 0..100")
    if category not in VALID_CATEGORIES:
        raise JoinRiskParseError(f"invalid category: {category!r}")
    if not isinstance(raw_signals, list):
        raise JoinRiskParseError("signals must be a JSON array")
    signals = [str(s) for s in raw_signals]
    return JoinRiskResult(
        risk_score=score,
        category=category,
        rationale=rationale,
        signals=signals,
    )


def parse_join_risk_response_text(text: str) -> JoinRiskResult:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise JoinRiskParseError("invalid JSON") from exc
    return parse_join_risk_payload(payload)


class JoinRiskService:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float,
        base_url: str | None = None,
    ) -> None:
        client_kw: dict[str, str] = {"api_key": api_key}
        if base_url:
            client_kw["base_url"] = base_url
        self._client = AsyncOpenAI(**client_kw)
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._log = logging.getLogger(__name__)

    async def assess(self, snapshot: dict[str, Any]) -> JoinRiskResult:
        user_content = json.dumps(snapshot, separators=(",", ":"), sort_keys=True)
        try:
            async with asyncio.timeout(self._timeout_seconds):
                completion = await self._client.chat.completions.create(
                    model=self._model,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": user_content},
                    ],
                )
        except TimeoutError:
            self._log.warning("join risk LLM timed out model=%s", self._model)
            raise
        except RateLimitError:
            self._log.warning("join risk LLM rate limited model=%s", self._model)
            raise
        except APIError as exc:
            self._log.warning("join risk LLM API error: %s", exc)
            raise

        message = completion.choices[0].message
        content = message.content
        if not content:
            raise JoinRiskParseError("empty model content")
        return parse_join_risk_response_text(content)
