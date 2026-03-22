from datetime import UTC, datetime
from pathlib import Path
import sys
from types import SimpleNamespace

import discord
import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from snd_revenue_service.join_profile import build_join_profile_snapshot


def test_build_join_profile_snapshot_collects_expected_keys() -> None:
    now = datetime(2026, 3, 15, 12, 0, 0, tzinfo=UTC)
    guild = SimpleNamespace(id=10)
    member = SimpleNamespace(
        guild=guild,
        id=99,
        name="user_one",
        global_name="Global Name",
        display_name="Nick",
        mention="<@99>",
        bot=False,
        system=False,
        created_at=datetime(2026, 3, 10, tzinfo=UTC),
        joined_at=datetime(2026, 3, 15, 11, 0, 0, tzinfo=UTC),
        avatar=object(),
        default_avatar=False,
        banner=None,
        accent_color=0xAB12CD,
        public_flags=discord.PublicUserFlags(verified_bot=True),
    )

    snap = build_join_profile_snapshot(member, now=now)

    assert snap["guild_id"] == 10
    assert snap["user_id"] == 99
    assert snap["username"] == "user_one"
    assert snap["global_name"] == "Global Name"
    assert snap["display_name"] == "Nick"
    assert snap["mention"] == "<@99>"
    assert snap["is_bot"] is False
    assert snap["is_system"] is False
    assert snap["account_age_days"] == 5
    assert snap["default_avatar"] is False
    assert snap["has_banner"] is False
    assert snap["accent_color"] == "#ab12cd"
    assert snap["public_flags"] == ["verified_bot"]
    assert snap["joined_at"] == "2026-03-15T11:00:00+00:00"


def test_build_join_profile_snapshot_default_avatar_when_no_avatar() -> None:
    now = datetime(2026, 3, 15, tzinfo=UTC)
    member = SimpleNamespace(
        guild=SimpleNamespace(id=1),
        id=1,
        name="a",
        global_name=None,
        display_name=None,
        mention="<@1>",
        bot=False,
        system=False,
        created_at=datetime(2020, 1, 1, tzinfo=UTC),
        joined_at=None,
        avatar=None,
        default_avatar=None,
        banner=None,
        accent_color=None,
        public_flags=None,
    )

    snap = build_join_profile_snapshot(member, now=now)

    assert snap["default_avatar"] is True
    assert snap["joined_at"] is None
    assert snap["accent_color"] is None
    assert snap["public_flags"] == []


def test_build_join_profile_snapshot_requires_created_at() -> None:
    member = SimpleNamespace(guild=SimpleNamespace(id=1), created_at=None)
    with pytest.raises(ValueError, match="created_at"):
        build_join_profile_snapshot(member, now=datetime.now(UTC))
