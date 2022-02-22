import dico_command
import dico_interaction

from discordbot.bot import Bot
from stockstack.settings import Settings


def load(bot: Bot):
    bot.load_addons(Basic)
    Settings.logger.info(f"Loaded {__file__}")


def unload(bot: Bot):
    bot.unload_addons(Basic)
    Settings.logger.info(f"Un-Loaded {__file__}")


class Basic(dico_command.Addon, name="Basic"):
    bot: Bot

    @dico_interaction.slash("ping", description="Ping")
    async def _ping(self, ctx: dico_interaction.InteractionContext) -> None:
        await ctx.send(f"Pong #{self.bot.get_shard_id(ctx.guild_id)} {self.bot.get_shard(ctx.guild_id).ping} sec ")

    @dico_interaction.slash("help", description="HELP!!!!!")
    async def _help(self, ctx: dico_interaction.InteractionContext) -> None:
        await ctx.send("비었음 ㅋ")
