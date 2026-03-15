from datetime import UTC, datetime
from pathlib import Path
import sys

import discord

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from snd_revenue_service.embeds import render_join_embed, render_leave_embed
from snd_revenue_service.events import JoinAuditEvent, LeaveAuditEvent


def _field_snapshot(embed) -> list[tuple[str, str, bool]]:
    return [(field.name, field.value, field.inline) for field in embed.fields]


def _formatted_timestamp(value: datetime) -> str:
    return discord.utils.format_dt(value, style="f")


def test_render_join_embed_renders_full_field_contract() -> None:
    event = JoinAuditEvent(
        event_type="member_joined",
        guild_id=1,
        user_id=42,
        username="new-user",
        display_name="New User",
        mention="<@42>",
        is_bot=False,
        account_created_at=datetime(2026, 3, 10, tzinfo=UTC),
        account_age="3 days",
        joined_at=datetime(2026, 3, 13, 12, 0, tzinfo=UTC),
    )

    embed = render_join_embed(event)

    assert embed.title == "Member Joined"
    assert _field_snapshot(embed) == [
        ("Member", "<@42>", False),
        ("Username", "new-user", True),
        ("User ID", "42", True),
        ("Account Type", "Human", True),
        ("Account Created", "<t:1773100800:f>", False),
        ("Account Age", "3 days", True),
        ("Joined At", _formatted_timestamp(event.joined_at), True),
    ]


def test_render_leave_embed_renders_optional_account_fields_when_available() -> None:
    event = LeaveAuditEvent(
        event_type="member_left",
        guild_id=1,
        user_id=99,
        username="helper-bot",
        display_name=None,
        mention=None,
        is_bot=True,
        account_created_at=datetime(2026, 3, 10, tzinfo=UTC),
        kicked_by=None,
        kick_reason=None,
        left_at=datetime(2026, 3, 13, 13, 0, tzinfo=UTC),
    )

    embed = render_leave_embed(event)

    assert embed.title == "Member Left"
    assert _field_snapshot(embed) == [
        ("User ID", "99", True),
        ("Username", "helper-bot", True),
        ("Account Type", "Bot", True),
        ("Account Created", "<t:1773100800:f>", False),
        ("Left At", _formatted_timestamp(event.left_at), True),
    ]


def test_render_leave_embed_uses_explicit_fallbacks_for_missing_fields() -> None:
    event = LeaveAuditEvent(
        event_type="member_left",
        guild_id=1,
        user_id=55,
        username=None,
        display_name=None,
        mention=None,
        is_bot=None,
        account_created_at=None,
        kicked_by=None,
        kick_reason=None,
        left_at=datetime(2026, 3, 13, 13, 0, tzinfo=UTC),
    )

    embed = render_leave_embed(event)

    assert embed.title == "Member Left"
    assert _field_snapshot(embed) == [
        ("User ID", "55", True),
        ("Username", "Unavailable", True),
        ("Left At", _formatted_timestamp(event.left_at), True),
    ]


def test_render_leave_embed_renders_kick_specific_fields() -> None:
    event = LeaveAuditEvent(
        event_type="member_kicked",
        guild_id=1,
        user_id=77,
        username="kicked-user",
        display_name=None,
        mention=None,
        is_bot=False,
        account_created_at=None,
        kicked_by="<@123>",
        kick_reason="spamming",
        left_at=datetime(2026, 3, 13, 13, 0, tzinfo=UTC),
    )

    embed = render_leave_embed(event)

    assert embed.title == "Member Kicked"
    assert _field_snapshot(embed) == [
        ("User ID", "77", True),
        ("Username", "kicked-user", True),
        ("Account Type", "Human", True),
        ("Kicked By", "<@123>", True),
        ("Kick Reason", "spamming", False),
        ("Left At", _formatted_timestamp(event.left_at), True),
    ]
