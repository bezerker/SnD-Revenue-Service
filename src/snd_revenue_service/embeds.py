import discord

from snd_revenue_service.events import JoinAuditEvent, LeaveAuditEvent


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
    embed = discord.Embed(title="Member Left")
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
    embed.add_field(name="Left At", value=discord.utils.format_dt(event.left_at, style="f"), inline=True)
    return embed
