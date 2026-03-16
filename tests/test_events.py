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


def test_format_account_age_uses_singular_day_for_one_day_delta() -> None:
    created_at = datetime(2026, 3, 12, tzinfo=UTC)
    now = datetime(2026, 3, 13, tzinfo=UTC)

    assert format_account_age(created_at, now) == "1 day"


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


def test_build_leave_event_uses_member_fields_when_only_member_is_available() -> None:
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


def test_build_leave_event_mixes_payload_user_and_member_fields() -> None:
    class PayloadUser:
        id = 77
        name = "payload-user"
        bot = True
        created_at = datetime(2026, 3, 1, tzinfo=UTC)

    class MixedPayload(DummyRawPayload):
        user = PayloadUser()

    member = DummyMember()
    event = build_leave_event(
        MixedPayload(),
        member=member,
        now=datetime(2026, 3, 13, 12, 0, tzinfo=UTC),
    )

    assert event.user_id == 77
    assert event.username == "payload-user"
    assert event.is_bot is True
    assert event.account_created_at == datetime(2026, 3, 1, tzinfo=UTC)
    assert event.display_name == "New User"
    assert event.mention == "<@42>"


def test_build_leave_event_captures_kick_metadata() -> None:
    event = build_leave_event(
        DummyRawPayload(),
        member=None,
        now=datetime(2026, 3, 13, 12, 0, tzinfo=UTC),
        event_type="member_kicked",
        kicked_by="mod-user",
        kick_reason="rule violation",
    )

    assert event.event_type == "member_kicked"
    assert event.kicked_by == "mod-user"
    assert event.kick_reason == "rule violation"


def test_build_leave_event_handles_payloads_without_user_id_attribute() -> None:
    class RawPayloadLikeEvent:
        guild_id = 999

        class user:
            id = 77
            name = "raw-user"
            bot = False
            created_at = datetime(2026, 3, 1, tzinfo=UTC)

    event = build_leave_event(
        RawPayloadLikeEvent(),
        member=None,
        now=datetime(2026, 3, 13, 12, 0, tzinfo=UTC),
    )

    assert event.user_id == 77
    assert event.username == "raw-user"
