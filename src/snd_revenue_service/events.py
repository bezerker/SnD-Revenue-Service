from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class JoinAuditEvent:
    event_type: str
    guild_id: int
    user_id: int
    username: str
    display_name: str | None
    mention: str
    is_bot: bool
    account_created_at: datetime
    account_age: str
    joined_at: datetime


@dataclass(frozen=True)
class LeaveAuditEvent:
    event_type: str
    guild_id: int
    user_id: int
    username: str | None
    display_name: str | None
    mention: str | None
    is_bot: bool | None
    account_created_at: datetime | None
    left_at: datetime


def format_account_age(created_at: datetime, now: datetime) -> str:
    delta = now - created_at.astimezone(UTC)
    days = max(delta.days, 0)
    return "1 day" if days == 1 else f"{days} days"


def build_join_event(member, now: datetime) -> JoinAuditEvent:
    return JoinAuditEvent(
        event_type="member_joined",
        guild_id=member.guild.id,
        user_id=member.id,
        username=member.name,
        display_name=getattr(member, "display_name", None),
        mention=member.mention,
        is_bot=member.bot,
        account_created_at=member.created_at,
        account_age=format_account_age(member.created_at, now),
        joined_at=member.joined_at or now,
    )


def build_leave_event(payload, *, member, now: datetime) -> LeaveAuditEvent:
    user = getattr(payload, "user", None) or member
    user_id = getattr(user, "id", payload.user_id)
    return LeaveAuditEvent(
        event_type="member_left",
        guild_id=payload.guild_id,
        user_id=user_id,
        username=getattr(user, "name", None),
        display_name=getattr(member, "display_name", None),
        mention=getattr(member, "mention", None),
        is_bot=getattr(user, "bot", None),
        account_created_at=getattr(user, "created_at", None),
        left_at=now,
    )
