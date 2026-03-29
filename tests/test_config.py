from pathlib import Path
import sys
from unittest import mock

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
    monkeypatch.delenv("SND_LLM_ENABLED", raising=False)
    monkeypatch.delenv("SND_LLM_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    settings = load_settings()

    assert settings.guild_id == 123
    assert settings.audit_channel_id == 456
    assert settings.discord_token == "token-value"
    assert settings.llm_enabled is False
    assert settings.llm_model == "5.4-mini"
    assert settings.llm_timeout_seconds == 30.0
    assert settings.llm_base_url is None


def test_load_settings_reads_llm_from_toml(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "[discord]\n"
        "guild_id = 123\n"
        "audit_channel_id = 456\n"
        "\n"
        "[llm]\n"
        "enabled = true\n"
        'model = "gpt-4o"\n'
        "timeout_seconds = 45\n"
        'base_url = "https://example.invalid/v1"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("SND_REVENUE_CONFIG", str(config_path))
    monkeypatch.setenv("DISCORD_TOKEN", "token-value")
    monkeypatch.delenv("SND_LLM_ENABLED", raising=False)
    monkeypatch.delenv("SND_LLM_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    settings = load_settings()

    assert settings.llm_enabled is True
    assert settings.llm_model == "gpt-4o"
    assert settings.llm_timeout_seconds == 45.0
    assert settings.llm_base_url == "https://example.invalid/v1"


def test_load_settings_env_overrides_llm_toml(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "[discord]\n"
        "guild_id = 123\n"
        "audit_channel_id = 456\n"
        "\n"
        "[llm]\n"
        "enabled = false\n"
        'model = "gpt-4o"\n'
        'base_url = "https://toml.example/v1"\n'
        "timeout_seconds = 60\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SND_REVENUE_CONFIG", str(config_path))
    monkeypatch.setenv("DISCORD_TOKEN", "token-value")
    monkeypatch.setenv("SND_LLM_ENABLED", "true")
    monkeypatch.setenv("OPENAI_MODEL", "custom-model-id")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://env.example/v1")
    monkeypatch.setenv("SND_LLM_TIMEOUT_SECONDS", "12")

    settings = load_settings()

    assert settings.llm_enabled is True
    assert settings.llm_model == "custom-model-id"
    assert settings.llm_timeout_seconds == 12.0
    assert settings.llm_base_url == "https://env.example/v1"


def test_load_settings_rejects_invalid_llm_timeout_in_toml(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "[discord]\n"
        "guild_id = 123\n"
        "audit_channel_id = 456\n"
        "\n"
        "[llm]\n"
        "enabled = true\n"
        "timeout_seconds = 0\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SND_REVENUE_CONFIG", str(config_path))
    monkeypatch.setenv("DISCORD_TOKEN", "token-value")
    monkeypatch.delenv("SND_LLM_TIMEOUT_SECONDS", raising=False)

    with pytest.raises(ConfigError, match="llm.timeout_seconds"):
        load_settings()


def test_load_settings_rejects_invalid_llm_timeout_in_env(
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
    monkeypatch.setenv("SND_LLM_TIMEOUT_SECONDS", "0")

    with pytest.raises(ConfigError, match="SND_LLM_TIMEOUT_SECONDS"):
        load_settings()


def test_load_settings_rejects_empty_openai_model(
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
    monkeypatch.setenv("OPENAI_MODEL", "   ")

    with pytest.raises(ConfigError, match="OPENAI_MODEL"):
        load_settings()


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


def test_load_settings_normalizes_config_read_failures(
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

    with mock.patch.object(Path, "open", side_effect=OSError("permission denied")):
        with pytest.raises(ConfigError, match="Could not read config file"):
            load_settings()


def test_load_settings_rejects_boolean_ids(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "[discord]\n"
        "guild_id = true\n"
        "audit_channel_id = 456\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SND_REVENUE_CONFIG", str(config_path))
    monkeypatch.setenv("DISCORD_TOKEN", "token-value")

    with pytest.raises(ConfigError, match="integer-like"):
        load_settings()


def test_load_settings_rejects_float_ids(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "[discord]\n"
        "guild_id = 123.9\n"
        "audit_channel_id = 456\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SND_REVENUE_CONFIG", str(config_path))
    monkeypatch.setenv("DISCORD_TOKEN", "token-value")

    with pytest.raises(ConfigError, match="integer-like"):
        load_settings()


def test_load_settings_rejects_zero_ids(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "[discord]\n"
        "guild_id = 0\n"
        "audit_channel_id = 456\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SND_REVENUE_CONFIG", str(config_path))
    monkeypatch.setenv("DISCORD_TOKEN", "token-value")

    with pytest.raises(ConfigError, match="positive"):
        load_settings()


def test_load_settings_rejects_negative_ids(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "[discord]\n"
        "guild_id = 123\n"
        "audit_channel_id = -456\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SND_REVENUE_CONFIG", str(config_path))
    monkeypatch.setenv("DISCORD_TOKEN", "token-value")

    with pytest.raises(ConfigError, match="positive"):
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


def test_main_exits_with_status_one_on_runtime_startup_failure(
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

    with mock.patch("snd_revenue_service.__main__.create_client", return_value=object()):
        with mock.patch(
            "snd_revenue_service.__main__.run_client",
            new=mock.AsyncMock(side_effect=RuntimeError("gateway failed")),
        ):
            with pytest.raises(SystemExit) as context:
                main()

    assert context.value.code == 1


def test_main_passes_join_risk_service_when_llm_enabled_and_api_key_set(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "[discord]\n"
        "guild_id = 123\n"
        "audit_channel_id = 456\n"
        "\n"
        "[llm]\n"
        "enabled = true\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SND_REVENUE_CONFIG", str(config_path))
    monkeypatch.setenv("DISCORD_TOKEN", "token-value")
    monkeypatch.delenv("SND_LLM_ENABLED", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    with mock.patch("snd_revenue_service.__main__.create_client") as create_client_mock:
        with mock.patch(
            "snd_revenue_service.__main__.run_client",
            new=mock.AsyncMock(),
        ):
            main()

    kwargs = create_client_mock.call_args.kwargs
    assert kwargs["join_risk_service"] is not None


def test_main_passes_no_join_risk_when_llm_enabled_but_api_key_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        "[discord]\n"
        "guild_id = 123\n"
        "audit_channel_id = 456\n"
        "\n"
        "[llm]\n"
        "enabled = true\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("SND_REVENUE_CONFIG", str(config_path))
    monkeypatch.setenv("DISCORD_TOKEN", "token-value")
    monkeypatch.delenv("SND_LLM_ENABLED", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with mock.patch("snd_revenue_service.__main__.create_client") as create_client_mock:
        with mock.patch(
            "snd_revenue_service.__main__.run_client",
            new=mock.AsyncMock(),
        ):
            with caplog.at_level("WARNING"):
                main()

    assert "OPENAI_API_KEY" in caplog.text
    kwargs = create_client_mock.call_args.kwargs
    assert kwargs["join_risk_service"] is None
