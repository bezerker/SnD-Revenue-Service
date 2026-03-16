import asyncio
import inspect
import logging
from datetime import UTC, datetime, timedelta

import discord

from snd_revenue_service.embeds import render_join_embed, render_leave_embed
from snd_revenue_service.events import build_join_event, build_leave_event


async def _resolve(value):
    if inspect.isawaitable(value):
        return await value
    return value


async def _latest_kick_for_user(guild, user_id: int, *, now: datetime):
    if guild is None:
        return None
    me = getattr(guild, "me", None)
    if me is None:
        return None
    perms = getattr(guild, "permissions_for", lambda _member: None)(me)
    if not perms or not getattr(perms, "view_audit_log", False):
        return None

    try:
        async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.kick):
            target_id = getattr(getattr(entry, "target", None), "id", None)
            if target_id != user_id:
                continue
            created_at = getattr(entry, "created_at", None)
            if created_at is None:
                continue
            if now - created_at > timedelta(seconds=15):
                continue
            return entry
    except Exception:
        logging.getLogger(__name__).debug("failed to inspect kick audit logs", exc_info=True)
    return None

async def run_client(client: discord.Client, token: str) -> None:
    startup = client._snd_startup_future()
    async with client:
        start_task = asyncio.create_task(client.start(token))

        try:
            done, _ = await asyncio.wait(
                {startup, start_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            if startup in done:
                await startup
                await start_task
                return

            await start_task
            if not startup.done():
                raise RuntimeError("Discord client stopped before startup completed")
            await startup
        finally:
            if not startup.done():
                startup.cancel()
            if not start_task.done():
                await start_task


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
    startup_complete: asyncio.Future[None] | None = None

    def startup_future() -> asyncio.Future[None]:
        nonlocal startup_complete
        if startup_complete is None:
            startup_complete = asyncio.get_running_loop().create_future()
        return startup_complete

    async def on_ready() -> None:
        startup = startup_future()
        if startup.done():
            return
        try:
            await publisher.bind(client)
        except Exception as exc:
            logger.exception("failed to bind audit publisher")
            startup.set_exception(exc)
            await client.close()
            return
        startup.set_result(None)
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
        now = datetime.now(UTC)
        event_type = "member_left"
        try:
            guild = client.get_guild(payload.guild_id)
            payload_user = getattr(payload, "user", None)
            payload_user_id = getattr(payload_user, "id", getattr(payload, "user_id", None))
            cached_member = guild.get_member(payload_user_id) if guild and payload_user_id else None

            kicked_by = None
            kick_reason = None
            if payload_user_id is not None:
                entry = await _latest_kick_for_user(guild, payload_user_id, now=now)
                if entry is not None:
                    event_type = "member_kicked"
                    actor = getattr(entry, "user", None)
                    kicked_by = getattr(actor, "mention", None) or getattr(actor, "name", None)
                    kick_reason = getattr(entry, "reason", None)

            event = await _resolve(
                build_leave(
                    payload,
                    member=cached_member,
                    now=now,
                    event_type=event_type,
                    kicked_by=kicked_by,
                    kick_reason=kick_reason,
                )
            )
            await publish_event(event, render_leave)
        except Exception as exc:
            logger.exception(
                "audit event processing failed event_type=%s guild_id=%s user_id=%s reason=%s",
                event_type,
                payload.guild_id,
                getattr(payload, "user_id", "unknown"),
                exc,
            )

    client.event(on_ready)
    client.event(on_member_join)
    client.event(on_raw_member_remove)
    client._snd_on_ready = on_ready
    client._snd_on_member_join = on_member_join
    client._snd_on_raw_member_remove = on_raw_member_remove
    client._snd_startup_future = startup_future
    return client
