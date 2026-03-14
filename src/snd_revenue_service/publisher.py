import discord


class PublishError(RuntimeError):
    pass


class AuditPublisher:
    def __init__(self, channel_id: int) -> None:
        self.channel_id = channel_id
        self.channel: discord.abc.Messageable | None = None

    async def bind(self, client: discord.Client) -> None:
        channel = client.get_channel(self.channel_id)
        if channel is None or (
            not isinstance(channel, discord.TextChannel)
            and not (hasattr(channel, "guild") and hasattr(channel, "permissions_for"))
        ):
            raise PublishError(f"Audit channel {self.channel_id} is not a text channel")

        permissions = channel.permissions_for(channel.guild.me)
        if not permissions.send_messages or not permissions.embed_links:
            raise PublishError(
                f"Missing send/embed permissions for audit channel {self.channel_id}"
            )
        self.channel = channel

    async def publish(self, embed: discord.Embed) -> None:
        if self.channel is None:
            raise PublishError("Publisher used before bind")
        await self.channel.send(embed=embed)
