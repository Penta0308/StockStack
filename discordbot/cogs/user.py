import dico_command
import dico_interaction

import stockstack.world.Company
from discordbot.bot import Bot
from stockstack.settings import Settings
from stockstack.world import Company


def load(bot: Bot):
    bot.load_addons(UserCog)
    Settings.logger.info(f"Loaded {__file__}")


def unload(bot: Bot):
    bot.unload_addons(UserCog)
    Settings.logger.info(f"Un-Loaded {__file__}")


class UserCog(dico_command.Addon, name="User"):
    bot: Bot

    @dico_interaction.slash("join", description="Join")
    async def _join(self, ctx: dico_interaction.InteractionContext) -> None:
        async with self.bot.dbconnpool.connection() as dbconn:
            async with dbconn.transaction():
                discorduid = int(ctx.author.id)
                cid = await Company.create(dbconn.cursor, f"TraderDiscord{discorduid}", None)
                await dbconn.execute("""INSERT INTO discorduser (discorduid, cid) VALUES (%s, %s)""", (discorduid, cid))
        await ctx.send(f"Joined, cid {cid}")

    @dico_interaction.slash("unjoin", description="Unjoin")
    async def _unjoin(self, ctx: dico_interaction.InteractionContext) -> None:
        async with self.bot.dbconnpool.connection() as dbconn:
            async with dbconn.transaction():
                discorduid = int(ctx.author.id)
                await dbconn.execute("""DELETE FROM discorduser WHERE discorduid = %s""", (discorduid,))
        await ctx.send(f"Unjoined")
