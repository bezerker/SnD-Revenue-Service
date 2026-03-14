# SnD-Revenue-Service
The Stand and Deliver Revenue Service

## Runtime Configuration

- `SND_REVENUE_CONFIG`: path to the external TOML config file
- `DISCORD_TOKEN`: Discord bot token
- The Discord application must enable the privileged `SERVER MEMBERS INTENT`

Example TOML:

    [discord]
    guild_id = 123456789
    audit_channel_id = 987654321

## Running Locally

    export DISCORD_TOKEN=your-bot-token
    export SND_REVENUE_CONFIG=/path/to/config.toml
    uv run python -m snd_revenue_service

## Running With Docker

The image expects the same environment variables. Mount the external TOML file into the
container and point `SND_REVENUE_CONFIG` at the in-container path:

    docker build -t snd-revenue-service:local .
    docker run --rm \
      -e DISCORD_TOKEN=your-bot-token \
      -e SND_REVENUE_CONFIG=/config/config.toml \
      -v /path/to/config.toml:/config/config.toml:ro \
      snd-revenue-service:local
