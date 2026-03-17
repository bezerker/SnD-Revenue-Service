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
    moderated_by: str | None
    moderation_reason: str | None
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


def build_leave_event(
    payload,
    *,
    member,
    now: datetime,
    event_type: str = "member_left",
    moderated_by: str | None = None,
    moderation_reason: str | None = None,
) -> LeaveAuditEvent:
    user = getattr(payload, "user", None) or member
    user_id = getattr(user, "id", None)
    if user_id is None:
        user_id = getattr(payload, "user_id", None)
    if user_id is None:
        user_id = getattr(member, "id", None)
    if user_id is None:
        raise ValueError("could not resolve user_id from payload or cached member")
    return LeaveAuditEvent(
        event_type=event_type,
        guild_id=payload.guild_id,
        user_id=user_id,
        username=getattr(user, "name", None),
        display_name=getattr(member, "display_name", None),
        mention=getattr(member, "mention", None),
        is_bot=getattr(user, "bot", None),
        account_created_at=getattr(user, "created_at", None),
        moderated_by=moderated_by,
        moderation_reason=moderation_reason,
        left_at=now,
    )
