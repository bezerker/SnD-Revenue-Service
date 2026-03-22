"""Build a JSON-serializable snapshot of a joining member for LLM risk assessment."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import discord


def _account_age_days(created_at: datetime, now: datetime) -> int:
    delta = now - created_at.astimezone(UTC)
    return max(delta.days, 0)


def _normalize_public_flags(value: Any) -> discord.PublicUserFlags:
    if value is None:
        return discord.PublicUserFlags._from_value(0)
    if isinstance(value, discord.PublicUserFlags):
        return value
    try:
        return discord.PublicUserFlags._from_value(int(value))
    except (TypeError, ValueError):
        return discord.PublicUserFlags.none()


def _public_flag_names(flags: discord.PublicUserFlags) -> list[str]:
    return sorted(str(f.name) for f in flags.all())


def build_join_profile_snapshot(member: Any, *, now: datetime) -> dict[str, Any]:
    """Collect Discord-visible fields only (no image bytes or external lookups)."""
    created_at = getattr(member, "created_at", None)
    if created_at is None:
        raise ValueError("member has no created_at")

    public_flags = _normalize_public_flags(getattr(member, "public_flags", None))

    avatar = getattr(member, "avatar", None)
    default_avatar = getattr(member, "default_avatar", None)
    if callable(default_avatar):
        default_avatar = default_avatar()
    if default_avatar is None:
        default_avatar = avatar is None

    banner = getattr(member, "banner", None)
    accent = getattr(member, "accent_color", None)
    accent_hex = f"#{accent:06x}" if accent is not None else None

    joined_at = getattr(member, "joined_at", None)

    return {
        "guild_id": getattr(getattr(member, "guild", None), "id", None),
        "user_id": getattr(member, "id", None),
        "username": getattr(member, "name", None),
        "global_name": getattr(member, "global_name", None),
        "display_name": getattr(member, "display_name", None),
        "mention": getattr(member, "mention", None),
        "is_bot": bool(getattr(member, "bot", False)),
        "is_system": bool(getattr(member, "system", False)),
        "account_created_at": created_at.astimezone(UTC).isoformat(),
        "account_age_days": _account_age_days(created_at, now),
        "joined_at": joined_at.astimezone(UTC).isoformat() if joined_at else None,
        "default_avatar": bool(default_avatar),
        "has_banner": banner is not None,
        "accent_color": accent_hex,
        "public_flags": _public_flag_names(public_flags),
    }
