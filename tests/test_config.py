from pathlib import Path
import sys

import pytest

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from snd_revenue_service.__main__ import main
from snd_revenue_service.config import ConfigError, load_settings


def test_load_settings_reads_toml_and_env(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "[discord]\n"
        "guild_id = 123\n"
        "audit_channel_id = 456\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SND_REVENUE_CONFIG", str(config_path))
    monkeypatch.setenv("DISCORD_TOKEN", "token-value")

    settings = load_settings()

    assert settings.guild_id == 123
    assert settings.audit_channel_id == 456
    assert settings.discord_token == "token-value"


def test_load_settings_requires_discord_token(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "[discord]\n"
        "guild_id = 123\n"
        "audit_channel_id = 456\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SND_REVENUE_CONFIG", str(config_path))
    monkeypatch.delenv("DISCORD_TOKEN", raising=False)

    with pytest.raises(ConfigError, match="DISCORD_TOKEN"):
        load_settings()


def test_load_settings_requires_existing_config_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("SND_REVENUE_CONFIG", str(tmp_path / "missing.toml"))
    monkeypatch.setenv("DISCORD_TOKEN", "token-value")

    with pytest.raises(ConfigError, match="does not exist"):
        load_settings()


def test_load_settings_rejects_malformed_ids(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "[discord]\n"
        "guild_id = 'abc'\n"
        "audit_channel_id = 456\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SND_REVENUE_CONFIG", str(config_path))
    monkeypatch.setenv("DISCORD_TOKEN", "token-value")

    with pytest.raises(ConfigError, match="integer-like"):
        load_settings()


def test_load_settings_rejects_malformed_toml(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "[discord\n"
        "guild_id = 123\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SND_REVENUE_CONFIG", str(config_path))
    monkeypatch.setenv("DISCORD_TOKEN", "token-value")

    with pytest.raises(ConfigError, match="Invalid TOML"):
        load_settings()


def test_load_settings_requires_all_required_keys(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "[discord]\n"
        "guild_id = 123\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SND_REVENUE_CONFIG", str(config_path))
    monkeypatch.setenv("DISCORD_TOKEN", "token-value")

    with pytest.raises(ConfigError, match="integer-like"):
        load_settings()


def test_main_exits_cleanly_on_config_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SND_REVENUE_CONFIG", raising=False)

    with pytest.raises(SystemExit, match="SND_REVENUE_CONFIG"):
        main()
