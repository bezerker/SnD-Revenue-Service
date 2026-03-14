# SnD-Revenue-Service
The Stand and Deliver Revenue Service

SnD Revenue Service is a Discord audit bot for a single server. The current release posts
embed-based audit messages when members join or leave, and includes Discord account age
information on joins.

## Current Scope

- One Discord guild per bot instance
- One configured audit channel
- Reports both human and bot accounts
- Labels bot accounts explicitly
- Join events include account creation time and relative account age

## Discord Setup

1. Create a Discord application and bot in the Discord Developer Portal.
2. Enable the privileged `SERVER MEMBERS INTENT` for the bot.
3. Invite the bot to the target server.
4. Ensure the bot can access the configured audit channel with:
   - `View Channel`
   - `Send Messages`
   - `Embed Links`

This bot only audits the guild configured in `config.toml`. If it is present in other guilds,
their join and leave events are ignored.

## Runtime Configuration

The bot reads non-secret settings from an external `TOML` file and reads the bot token from an
environment variable. Do not commit the config file or token.

- `SND_REVENUE_CONFIG`: absolute or container-local path to the external TOML config file
- `DISCORD_TOKEN`: Discord bot token from the Discord Developer Portal

Config file:

```toml
[discord]
guild_id = 123456789012345678
audit_channel_id = 987654321098765432
```

Settings:

- `guild_id`: the single Discord server this bot should monitor
- `audit_channel_id`: the channel where join and leave embeds should be posted

## What The Bot Posts

Join embed:

- member mention
- username and Discord user ID
- bot or human label
- account creation timestamp
- human-readable account age such as `2 years, 3 months`
- join timestamp

Leave embed:

- member mention or fallback name
- username and Discord user ID when available
- bot or human label
- leave timestamp

## Running With uv

Prerequisites:

- Python 3.13
- `uv`

Start the bot:

```bash
export DISCORD_TOKEN=your-bot-token
export SND_REVENUE_CONFIG=/absolute/path/to/config.toml
uv sync --frozen --all-groups
uv run python -m snd_revenue_service
```

## Running With Docker

The image expects the same environment variables. Mount the external TOML file into the
container and point `SND_REVENUE_CONFIG` at the in-container path:

```bash
docker build -t snd-revenue-service:local .
docker run --rm \
  -e DISCORD_TOKEN=your-bot-token \
  -e SND_REVENUE_CONFIG=/config/config.toml \
  -v /path/to/config.toml:/config/config.toml:ro \
  snd-revenue-service:local
```

## Running In Kubernetes

This bot should run as a long-lived deployment, not as a CronJob.

Example pattern:

- store `DISCORD_TOKEN` in a `Secret`
- provide `config.toml` via a mounted `Secret` or `ConfigMap`
- run one replica unless you intentionally want multiple bots connected at once

Example container settings:

```yaml
env:
  - name: DISCORD_TOKEN
    valueFrom:
      secretKeyRef:
        name: snd-revenue-service
        key: discord-token
  - name: SND_REVENUE_CONFIG
    value: /config/config.toml
volumeMounts:
  - name: config
    mountPath: /config
    readOnly: true
volumes:
  - name: config
    secret:
      secretName: snd-revenue-service-config
```

## CI And Image Build

GitHub Actions runs:

- locked dependency sync with `uv`
- the full test suite
- Docker image build validation

The repository includes:

- `Dockerfile`
- `.github/workflows/ci.yml`
- `uv.lock`

## Operational Notes

- Startup fails fast if the config file is missing, malformed, or the token is unset.
- Startup also fails if the configured channel is not a text channel or the bot lacks embed
  permissions.
- Runtime publish failures are logged and do not crash the process.
- Future anti-abuse checks can be added without changing the external configuration format.
