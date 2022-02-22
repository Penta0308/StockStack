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


class Basic(dico_command.Addon):
    bot: Bot
    name = "Basic"

    @dico_interaction.slash(name="ping", description="Ping")
    async def _ping(self, ctx: dico_interaction.InteractionContext) -> None:
        await ctx.send(f"Pong #f({self.bot.get_shard_id(ctx.guild_id)} {self.bot.get_shard(ctx.guild_id).ping} us ")

    @dico_interaction.slash(name="help", description="HELP!!!!!")
    async def _help(self, ctx: dico_interaction.InteractionContext) -> None:
        await ctx.send("비었음 ㅋ")
