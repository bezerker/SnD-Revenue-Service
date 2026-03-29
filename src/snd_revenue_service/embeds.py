import discord

from snd_revenue_service.events import JoinAuditEvent, LeaveAuditEvent
from snd_revenue_service.join_risk import JoinRiskResult, RISK_DISCLAIMER

_CATEGORY_LABELS = {
    "likely_human": "Likely human",
    "uncertain": "Uncertain",
    "likely_automation_or_compromise": "Likely automation or compromise",
}


def _truncate_field_value(text: str, max_len: int = 1000) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


def render_join_risk_embed(
    *,
    user_id: int,
    mention: str | None,
    username: str | None,
    result: JoinRiskResult,
) -> discord.Embed:
    embed = discord.Embed(title="Join risk assessment")
    member_value = mention or username or str(user_id)
    embed.add_field(name="Member", value=member_value, inline=False)
    embed.add_field(name="User ID", value=str(user_id), inline=True)
    embed.add_field(name="Risk score", value=str(result.risk_score), inline=True)
    category_label = _CATEGORY_LABELS.get(result.category, result.category)
    embed.add_field(name="Category", value=category_label, inline=True)
    embed.add_field(
        name="Rationale",
        value=_truncate_field_value(result.rationale),
        inline=False,
    )
    signals_text = "\n".join(f"• {s}" for s in result.signals) if result.signals else "—"
    embed.add_field(
        name="Signals",
        value=_truncate_field_value(signals_text),
        inline=False,
    )
    embed.set_footer(text=RISK_DISCLAIMER)
    return embed


def render_join_embed(event: JoinAuditEvent) -> discord.Embed:
    embed = discord.Embed(title="Member Joined")
    embed.add_field(name="Member", value=event.mention, inline=False)
    embed.add_field(name="Username", value=event.username, inline=True)
    embed.add_field(name="User ID", value=str(event.user_id), inline=True)
    embed.add_field(name="Account Type", value="Bot" if event.is_bot else "Human", inline=True)
    embed.add_field(
        name="Account Created",
        value=discord.utils.format_dt(event.account_created_at, style="f"),
        inline=False,
    )
    embed.add_field(name="Account Age", value=event.account_age, inline=True)
    embed.add_field(
        name="Joined At",
        value=discord.utils.format_dt(event.joined_at, style="f"),
        inline=True,
    )
    return embed


def render_leave_embed(event: LeaveAuditEvent) -> discord.Embed:
    title_map = {
        "member_left": "Member Left",
        "member_kicked": "Member Kicked",
        "member_banned": "Member Banned",
    }
    title = title_map.get(event.event_type, "Member Left")
    embed = discord.Embed(title=title)
    embed.add_field(name="User ID", value=str(event.user_id), inline=True)
    embed.add_field(name="Username", value=event.username or "Unavailable", inline=True)
    if event.is_bot is not None:
        embed.add_field(name="Account Type", value="Bot" if event.is_bot else "Human", inline=True)
    if event.account_created_at is not None:
        embed.add_field(
            name="Account Created",
            value=discord.utils.format_dt(event.account_created_at, style="f"),
            inline=False,
        )
    if event.event_type in {"member_kicked", "member_banned"}:
        actor_label = "Kicked By" if event.event_type == "member_kicked" else "Banned By"
        reason_label = "Kick Reason" if event.event_type == "member_kicked" else "Ban Reason"
        embed.add_field(name=actor_label, value=event.moderated_by or "Unavailable", inline=True)
        if event.moderation_reason:
            embed.add_field(name=reason_label, value=event.moderation_reason, inline=False)
    embed.add_field(name="Left At", value=discord.utils.format_dt(event.left_at, style="f"), inline=True)
    return embed
