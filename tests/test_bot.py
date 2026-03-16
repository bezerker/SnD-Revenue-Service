import asyncio
from datetime import UTC, datetime
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock

import discord
import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from snd_revenue_service.bot import create_client, run_client
from snd_revenue_service.config import Settings
from snd_revenue_service.publisher import AuditPublisher, PublishError


@pytest.mark.asyncio
async def test_on_member_join_publishes_rendered_embed() -> None:
    publisher = SimpleNamespace(bind=AsyncMock(), publish=AsyncMock())
    renderer = AsyncMock(return_value=discord.Embed(title="Member Joined"))
    builder = AsyncMock(
        return_value=SimpleNamespace(
            event_type="member_joined",
            guild_id=123,
            user_id=42,
        )
    )
    settings = Settings(123, 456, "token", Path("/tmp/config.toml"))

    client = create_client(
        settings,
        publisher=publisher,
        render_join=renderer,
        build_join=builder,
    )
    member = SimpleNamespace(guild=SimpleNamespace(id=123))

    await client._snd_on_member_join(member)

    publisher.publish.assert_awaited_once()


@pytest.mark.asyncio
async def test_on_raw_member_remove_publishes_leave_embed() -> None:
    publisher = SimpleNamespace(bind=AsyncMock(), publish=AsyncMock())
    renderer = AsyncMock(return_value=discord.Embed(title="Member Left"))
    builder = AsyncMock(
        return_value=SimpleNamespace(
            event_type="member_left",
            guild_id=123,
            user_id=77,
        )
    )
    settings = Settings(123, 456, "token", Path("/tmp/config.toml"))

    client = create_client(
        settings,
        publisher=publisher,
        render_leave=renderer,
        build_leave=builder,
    )
    client.get_guild = lambda guild_id: SimpleNamespace(get_member=lambda user_id: None)

    payload = SimpleNamespace(guild_id=123, user=SimpleNamespace(id=77), user_id=77)
    await client._snd_on_raw_member_remove(payload)

    publisher.publish.assert_awaited_once()


@pytest.mark.asyncio
async def test_handlers_ignore_other_guilds() -> None:
    publisher = SimpleNamespace(bind=AsyncMock(), publish=AsyncMock())
    settings = Settings(123, 456, "token", Path("/tmp/config.toml"))

    client = create_client(settings, publisher=publisher)
    member = SimpleNamespace(guild=SimpleNamespace(id=999))

    await client._snd_on_member_join(member)

    publisher.publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_publish_failures_are_logged_without_raising(
    caplog: pytest.LogCaptureFixture,
) -> None:
    publisher = SimpleNamespace(bind=AsyncMock(), publish=AsyncMock(side_effect=RuntimeError("boom")))
    renderer = AsyncMock(return_value=discord.Embed(title="Member Joined"))
    builder = AsyncMock(
        return_value=SimpleNamespace(
            event_type="member_joined",
            guild_id=123,
            user_id=42,
        )
    )
    settings = Settings(123, 456, "token", Path("/tmp/config.toml"))

    client = create_client(
        settings,
        publisher=publisher,
        render_join=renderer,
        build_join=builder,
    )
    member = SimpleNamespace(guild=SimpleNamespace(id=123))

    with caplog.at_level("ERROR"):
        await client._snd_on_member_join(member)

    assert "audit publish failed" in caplog.text
    assert "event_type=member_joined" in caplog.text
    assert "guild_id=123" in caplog.text
    assert "user_id=42" in caplog.text
    assert "reason=boom" in caplog.text


@pytest.mark.asyncio
async def test_event_processing_failures_are_logged_without_raising(
    caplog: pytest.LogCaptureFixture,
) -> None:
    publisher = SimpleNamespace(bind=AsyncMock(), publish=AsyncMock())
    renderer = AsyncMock(return_value=discord.Embed(title="Member Joined"))
    builder = AsyncMock(side_effect=ValueError("bad payload"))
    settings = Settings(123, 456, "token", Path("/tmp/config.toml"))

    client = create_client(
        settings,
        publisher=publisher,
        render_join=renderer,
        build_join=builder,
    )
    member = SimpleNamespace(guild=SimpleNamespace(id=123), id=42)

    with caplog.at_level("ERROR"):
        await client._snd_on_member_join(member)

    assert "audit event processing failed" in caplog.text
    assert "event_type=member_joined" in caplog.text
    assert "guild_id=123" in caplog.text
    assert "user_id=42" in caplog.text
    assert "reason=bad payload" in caplog.text


@pytest.mark.asyncio
async def test_run_client_closes_client_context_on_normal_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    publisher = SimpleNamespace(bind=AsyncMock(), publish=AsyncMock())
    settings = Settings(123, 456, "token", Path("/tmp/config.toml"))
    client = create_client(settings, publisher=publisher)

    enter = AsyncMock(return_value=client)
    exit_ = AsyncMock(return_value=False)
    monkeypatch.setattr(discord.Client, "__aenter__", enter)
    monkeypatch.setattr(discord.Client, "__aexit__", exit_)

    async def fake_start(token: str) -> None:
        await client._snd_on_ready()

    client.start = fake_start

    await run_client(client, settings.discord_token)

    enter.assert_awaited_once()
    exit_.assert_awaited_once()
    assert exit_.await_args.args == (None, None, None)


@pytest.mark.asyncio
async def test_run_client_surfaces_bind_failures_and_closes_client_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    publisher = SimpleNamespace(
        bind=AsyncMock(side_effect=PublishError("Missing send/embed permissions")),
        publish=AsyncMock(),
    )
    settings = Settings(123, 456, "token", Path("/tmp/config.toml"))
    client = create_client(settings, publisher=publisher)
    client.close = AsyncMock()

    enter = AsyncMock(return_value=client)
    exit_ = AsyncMock(return_value=False)
    monkeypatch.setattr(discord.Client, "__aenter__", enter)
    monkeypatch.setattr(discord.Client, "__aexit__", exit_)

    async def fake_start(token: str) -> None:
        await client._snd_on_ready()
        await asyncio.sleep(0)

    client.start = fake_start

    with pytest.raises(PublishError, match="Missing send/embed permissions"):
        await run_client(client, settings.discord_token)

    enter.assert_awaited_once()
    exit_.assert_awaited_once()
    assert exit_.await_args.args[0] is PublishError
    client.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_audit_publisher_rejects_non_text_channel_objects() -> None:
    permissions = SimpleNamespace(send_messages=True, embed_links=False)
    me = object()
    channel = SimpleNamespace(
        guild=SimpleNamespace(me=me),
        permissions_for=lambda member: permissions,
    )
    client = SimpleNamespace(get_channel=lambda channel_id: channel)
    publisher = AuditPublisher(channel_id=456)

    with pytest.raises(PublishError, match="not a text channel"):
        await publisher.bind(client)


@pytest.mark.asyncio
async def test_audit_publisher_rejects_missing_embed_permission_on_text_channel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    permissions = SimpleNamespace(send_messages=True, embed_links=False)
    me = object()
    channel = object.__new__(discord.TextChannel)
    channel.guild = SimpleNamespace(me=me)
    monkeypatch.setattr(
        discord.TextChannel,
        "permissions_for",
        lambda self, member: permissions,
    )

    client = SimpleNamespace(get_channel=lambda channel_id: channel)
    publisher = AuditPublisher(channel_id=456)

    with pytest.raises(PublishError, match="Missing send/embed permissions"):
        await publisher.bind(client)


@pytest.mark.asyncio
async def test_on_raw_member_remove_marks_recent_audit_kick() -> None:
    publisher = SimpleNamespace(bind=AsyncMock(), publish=AsyncMock())
    renderer = AsyncMock(return_value=discord.Embed(title="Member Left"))
    builder = AsyncMock(
        return_value=SimpleNamespace(
            event_type="member_kicked",
            guild_id=123,
            user_id=77,
        )
    )
    settings = Settings(123, 456, "token", Path("/tmp/config.toml"))

    client = create_client(
        settings,
        publisher=publisher,
        render_leave=renderer,
        build_leave=builder,
    )

    class AuditLogs:
        def __init__(self, entries):
            self.entries = entries

        def __aiter__(self):
            async def _gen():
                for entry in self.entries:
                    yield entry

            return _gen()

    def _audit_logs(*, action, **kwargs):
        if action == discord.AuditLogAction.kick:
            return AuditLogs(
                [
                    SimpleNamespace(
                        target=SimpleNamespace(id=77),
                        created_at=datetime.now(UTC),
                        user=SimpleNamespace(mention="<@9001>", name="mod"),
                        reason="rule violation",
                    )
                ]
            )
        return AuditLogs([])

    guild = SimpleNamespace(
        me=object(),
        permissions_for=lambda _member: SimpleNamespace(view_audit_log=True),
        get_member=lambda user_id: None,
        audit_logs=_audit_logs,
    )
    client.get_guild = lambda guild_id: guild

    payload = SimpleNamespace(guild_id=123, user=SimpleNamespace(id=77), user_id=77)
    await client._snd_on_raw_member_remove(payload)

    _, kwargs = builder.await_args
    assert kwargs["event_type"] == "member_kicked"
    assert kwargs["kicked_by"] == "<@9001>"
    assert kwargs["kick_reason"] == "rule violation"
    publisher.publish.assert_awaited_once()


@pytest.mark.asyncio
async def test_on_raw_member_remove_marks_recent_audit_ban() -> None:
    publisher = SimpleNamespace(bind=AsyncMock(), publish=AsyncMock())
    renderer = AsyncMock(return_value=discord.Embed(title="Member Left"))
    builder = AsyncMock(
        return_value=SimpleNamespace(
            event_type="member_banned",
            guild_id=123,
            user_id=77,
        )
    )
    settings = Settings(123, 456, "token", Path("/tmp/config.toml"))

    client = create_client(
        settings,
        publisher=publisher,
        render_leave=renderer,
        build_leave=builder,
    )

    class AuditLogs:
        def __init__(self, entries):
            self.entries = entries

        def __aiter__(self):
            async def _gen():
                for entry in self.entries:
                    yield entry

            return _gen()

    def _audit_logs(*, action, **kwargs):
        if action == discord.AuditLogAction.ban:
            return AuditLogs(
                [
                    SimpleNamespace(
                        target=SimpleNamespace(id=77),
                        created_at=datetime.now(UTC),
                        user=SimpleNamespace(mention="<@4444>", name="admin"),
                        reason="repeat abuse",
                    )
                ]
            )
        return AuditLogs([])

    guild = SimpleNamespace(
        me=object(),
        permissions_for=lambda _member: SimpleNamespace(view_audit_log=True),
        get_member=lambda user_id: None,
        audit_logs=_audit_logs,
    )
    client.get_guild = lambda guild_id: guild

    payload = SimpleNamespace(guild_id=123, user=SimpleNamespace(id=77), user_id=77)
    await client._snd_on_raw_member_remove(payload)

    _, kwargs = builder.await_args
    assert kwargs["event_type"] == "member_banned"
    assert kwargs["kicked_by"] == "<@4444>"
    assert kwargs["kick_reason"] == "repeat abuse"
    publisher.publish.assert_awaited_once()
