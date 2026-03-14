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
