from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Settings:
    guild_id: int
    audit_channel_id: int
    discord_token: str
    config_path: Path
    # Join risk LLM: optional [llm] in TOML; OPENAI_API_KEY and optional env overrides.
    llm_enabled: bool = False
    llm_model: str = "5.4-mini"
    llm_timeout_seconds: float = 30.0
    llm_base_url: str | None = None


def _parse_intlike_value(value: object) -> int:
    if isinstance(value, bool):
        raise TypeError("boolean values are not valid IDs")
    if isinstance(value, float):
        raise TypeError("float values are not valid IDs")

    parsed = int(value)
    if parsed <= 0:
        raise ValueError("IDs must be positive integers")

    return parsed


def _env_flag_true(name: str) -> bool:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return False
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _parse_llm_from_toml(llm_section: Any) -> tuple[bool, str, float, str | None]:
    section = llm_section or {}
    if not isinstance(section, dict):
        raise ConfigError("llm must be a table")

    llm_enabled = bool(section.get("enabled", False))

    llm_model = section.get("model", "5.4-mini")
    if not isinstance(llm_model, str) or not llm_model.strip():
        raise ConfigError("llm.model must be a non-empty string when set")
    llm_model = llm_model.strip()

    raw_timeout = section.get("timeout_seconds", 30.0)
    try:
        llm_timeout_seconds = float(raw_timeout)
    except (TypeError, ValueError) as exc:
        raise ConfigError("llm.timeout_seconds must be a positive number") from exc
    if llm_timeout_seconds <= 0:
        raise ConfigError("llm.timeout_seconds must be a positive number")

    llm_base_url = section.get("base_url")
    if llm_base_url is not None and (not isinstance(llm_base_url, str) or not llm_base_url.strip()):
        raise ConfigError("llm.base_url must be a non-empty string when set")
    if isinstance(llm_base_url, str):
        llm_base_url = llm_base_url.strip() or None

    return llm_enabled, llm_model, llm_timeout_seconds, llm_base_url


def _apply_llm_env_overrides(
    llm_enabled: bool,
    llm_model: str,
    llm_timeout_seconds: float,
    llm_base_url: str | None,
) -> tuple[bool, str, float, str | None]:
    """When set, SND_LLM_ENABLED / OPENAI_* / SND_LLM_TIMEOUT_SECONDS override TOML."""
    if "SND_LLM_ENABLED" in os.environ:
        llm_enabled = _env_flag_true("SND_LLM_ENABLED")

    env_model = os.environ.get("OPENAI_MODEL")
    if isinstance(env_model, str) and env_model.strip():
        llm_model = env_model.strip()

    raw_timeout = os.environ.get("SND_LLM_TIMEOUT_SECONDS")
    if raw_timeout is not None and str(raw_timeout).strip():
        try:
            llm_timeout_seconds = float(str(raw_timeout).strip())
        except ValueError as exc:
            raise ConfigError("SND_LLM_TIMEOUT_SECONDS must be a positive number") from exc
        if llm_timeout_seconds <= 0:
            raise ConfigError("SND_LLM_TIMEOUT_SECONDS must be a positive number")

    env_base_url = os.environ.get("OPENAI_BASE_URL")
    if isinstance(env_base_url, str) and env_base_url.strip():
        llm_base_url = env_base_url.strip()

    return llm_enabled, llm_model, llm_timeout_seconds, llm_base_url


def load_settings() -> Settings:
    raw_path = os.environ.get("SND_REVENUE_CONFIG")
    if not raw_path:
        raise ConfigError("SND_REVENUE_CONFIG must point to the runtime TOML file")

    config_path = Path(raw_path)
    if not config_path.is_file():
        raise ConfigError(f"Config file does not exist: {config_path}")

    try:
        with config_path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Invalid TOML in config file: {config_path}") from exc
    except OSError as exc:
        raise ConfigError(f"Could not read config file: {config_path}") from exc

    discord_section = data.get("discord") or {}
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        raise ConfigError("DISCORD_TOKEN must be set")

    try:
        guild_id = _parse_intlike_value(discord_section["guild_id"])
        audit_channel_id = _parse_intlike_value(discord_section["audit_channel_id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ConfigError(
            "discord.guild_id and discord.audit_channel_id must be positive integer-like values"
        ) from exc

    llm_enabled, llm_model, llm_timeout_seconds, llm_base_url = _parse_llm_from_toml(
        data.get("llm")
    )
    llm_enabled, llm_model, llm_timeout_seconds, llm_base_url = _apply_llm_env_overrides(
        llm_enabled,
        llm_model,
        llm_timeout_seconds,
        llm_base_url,
    )

    env_model_check = os.environ.get("OPENAI_MODEL")
    if env_model_check is not None and (
        not isinstance(env_model_check, str) or not env_model_check.strip()
    ):
        raise ConfigError("OPENAI_MODEL must be a non-empty string when set")

    return Settings(
        guild_id=guild_id,
        audit_channel_id=audit_channel_id,
        discord_token=token,
        config_path=config_path,
        llm_enabled=llm_enabled,
        llm_model=llm_model,
        llm_timeout_seconds=llm_timeout_seconds,
        llm_base_url=llm_base_url,
    )
