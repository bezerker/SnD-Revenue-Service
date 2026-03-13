from dataclasses import dataclass
import os
from pathlib import Path

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


def _parse_intlike_value(value: object) -> int:
    if isinstance(value, bool):
        raise TypeError("boolean values are not valid IDs")

    return int(value)


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
            "discord.guild_id and discord.audit_channel_id must be integer-like"
        ) from exc

    return Settings(
        guild_id=guild_id,
        audit_channel_id=audit_channel_id,
        discord_token=token,
        config_path=config_path,
    )
