import inspect
import logging
from datetime import UTC, datetime

import discord

from snd_revenue_service.embeds import render_join_embed, render_leave_embed
from snd_revenue_service.events import build_join_event, build_leave_event


async def _resolve(value):
    if inspect.isawaitable(value):
        return await value
    return value


def create_client(
    settings,
    *,
    publisher,
    render_join=render_join_embed,
    render_leave=render_leave_embed,
    build_join=build_join_event,
    build_leave=build_leave_event,
) -> discord.Client:
    intents = discord.Intents.none()
    intents.guilds = True
    intents.members = True

    client = discord.Client(intents=intents)
    logger = logging.getLogger(__name__)

    async def on_ready() -> None:
        try:
            await publisher.bind(client)
        except Exception:
            logger.exception("failed to bind audit publisher")
            await client.close()
            raise
        logger.info("bot ready")

    async def publish_event(event, render) -> None:
        try:
            embed = await _resolve(render(event))
            await publisher.publish(embed)
        except Exception as exc:
            logger.exception(
                "audit publish failed event_type=%s guild_id=%s user_id=%s reason=%s",
                getattr(event, "event_type", "unknown"),
                getattr(event, "guild_id", "unknown"),
                getattr(event, "user_id", "unknown"),
                exc,
            )

    async def on_member_join(member) -> None:
        if member.guild.id != settings.guild_id:
            return
        try:
            event = await _resolve(build_join(member, now=datetime.now(UTC)))
            await publish_event(event, render_join)
        except Exception as exc:
            logger.exception(
                "audit event processing failed event_type=%s guild_id=%s user_id=%s reason=%s",
                "member_joined",
                member.guild.id,
                getattr(member, "id", "unknown"),
                exc,
            )

    async def on_raw_member_remove(payload) -> None:
        if payload.guild_id != settings.guild_id:
            return
        try:
            guild = client.get_guild(payload.guild_id)
            cached_member = guild.get_member(payload.user.id) if guild and payload.user else None
            event = await _resolve(
                build_leave(payload, member=cached_member, now=datetime.now(UTC))
            )
            await publish_event(event, render_leave)
        except Exception as exc:
            logger.exception(
                "audit event processing failed event_type=%s guild_id=%s user_id=%s reason=%s",
                "member_left",
                payload.guild_id,
                getattr(payload, "user_id", "unknown"),
                exc,
            )

    client.event(on_ready)
    client.event(on_member_join)
    client.event(on_raw_member_remove)
    client._snd_on_member_join = on_member_join
    client._snd_on_raw_member_remove = on_raw_member_remove
    return client
