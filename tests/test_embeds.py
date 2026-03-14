from datetime import UTC, datetime
from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from snd_revenue_service.embeds import render_join_embed, render_leave_embed
from snd_revenue_service.events import JoinAuditEvent, LeaveAuditEvent


def test_render_join_embed_contains_creation_time_and_account_age() -> None:
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
    assert any(field.name == "Account Age" and field.value == "3 days" for field in embed.fields)
    assert any(
        field.name == "Account Created" and field.value == "<t:1773100800:f>"
        for field in embed.fields
    )


def test_render_leave_embed_marks_bot_label_when_available() -> None:
    event = LeaveAuditEvent(
        event_type="member_left",
        guild_id=1,
        user_id=99,
        username="helper-bot",
        display_name=None,
        mention=None,
        is_bot=True,
        account_created_at=None,
        left_at=datetime(2026, 3, 13, 13, 0, tzinfo=UTC),
    )

    embed = render_leave_embed(event)

    assert embed.title == "Member Left"
    assert any(field.name == "Account Type" and field.value == "Bot" for field in embed.fields)


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
        left_at=datetime(2026, 3, 13, 13, 0, tzinfo=UTC),
    )

    embed = render_leave_embed(event)

    assert any(field.name == "Username" and field.value == "Unavailable" for field in embed.fields)
    assert not any(field.name == "Account Type" for field in embed.fields)
    assert not any(field.name == "Account Created" for field in embed.fields)
