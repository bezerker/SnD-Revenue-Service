from datetime import UTC, datetime
from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from snd_revenue_service.events import (
    build_join_event,
    build_leave_event,
    format_account_age,
)


class DummyMember:
    id = 42
    name = "new-user"
    display_name = "New User"
    bot = False
    mention = "<@42>"
    created_at = datetime(2026, 3, 10, tzinfo=UTC)
    joined_at = datetime(2026, 3, 13, 12, 0, tzinfo=UTC)

    class guild:
        id = 999


class DummyRawPayload:
    guild_id = 999
    user = None
    user_id = 77


def test_format_account_age_returns_human_readable_delta() -> None:
    created_at = datetime(2026, 3, 10, tzinfo=UTC)
    now = datetime(2026, 3, 13, tzinfo=UTC)

    assert format_account_age(created_at, now) == "3 days"


def test_build_join_event_captures_member_fields() -> None:
    event = build_join_event(DummyMember(), now=datetime(2026, 3, 13, 12, 0, tzinfo=UTC))

    assert event.event_type == "member_joined"
    assert event.guild_id == 999
    assert event.user_id == 42
    assert event.account_age == "3 days"


def test_build_leave_event_handles_uncached_raw_payload() -> None:
    event = build_leave_event(
        DummyRawPayload(),
        member=None,
        now=datetime(2026, 3, 13, 12, 0, tzinfo=UTC),
    )

    assert event.event_type == "member_left"
    assert event.guild_id == 999
    assert event.user_id == 77
    assert event.username is None
    assert event.mention is None


def test_build_leave_event_prefers_cached_member_fields_when_present() -> None:
    member = DummyMember()
    event = build_leave_event(
        DummyRawPayload(),
        member=member,
        now=datetime(2026, 3, 13, 12, 0, tzinfo=UTC),
    )

    assert event.user_id == 42
    assert event.username == "new-user"
    assert event.display_name == "New User"
    assert event.mention == "<@42>"
