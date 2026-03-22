import json
from pathlib import Path
import sys

import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from snd_revenue_service.join_risk import (
    JoinRiskParseError,
    JoinRiskResult,
    parse_join_risk_payload,
    parse_join_risk_response_text,
)


def test_parse_join_risk_response_text_accepts_valid_payload() -> None:
    payload = {
        "risk_score": 42,
        "category": "uncertain",
        "rationale": "Mixed signals.",
        "signals": ["new account", "default avatar"],
    }
    result = parse_join_risk_response_text(json.dumps(payload))
    assert result == JoinRiskResult(
        risk_score=42,
        category="uncertain",
        rationale="Mixed signals.",
        signals=["new account", "default avatar"],
    )


def test_parse_join_risk_rejects_bad_score() -> None:
    with pytest.raises(JoinRiskParseError, match="risk_score"):
        parse_join_risk_payload(
            {"risk_score": 101, "category": "uncertain", "rationale": "x", "signals": []}
        )


def test_parse_join_risk_rejects_bad_category() -> None:
    with pytest.raises(JoinRiskParseError, match="invalid category"):
        parse_join_risk_payload(
            {"risk_score": 0, "category": "nope", "rationale": "x", "signals": []}
        )


def test_parse_join_risk_rejects_non_object() -> None:
    with pytest.raises(JoinRiskParseError, match="JSON object"):
        parse_join_risk_payload([])
