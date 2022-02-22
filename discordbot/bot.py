import contextlib
import os
import traceback

import dico
import dico.utils
import dico_command
import dico_interaction
from dico_interaction.exception import CheckFailed

from stockstack.settings import Settings


class Bot(dico_command.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dico_interaction.InteractionClient(client=self, auto_register_commands=True)

        self.on_("ready", self._ready_handler)
        self.on_("shards_ready", self._shards_ready_handler)
        self.on_("interaction_error", self._interaction_error_handler)

    def load_modules(self):
        for filename in os.listdir("discordbot/cogs"):
            if filename.endswith(".py"):
                try:
                    self.load_module(f"discordbot.cogs.{filename[:-3]}")
                except dico_command.ModuleAlreadyLoaded:
                    self.reload_module(f"discordbot.cogs.{filename[:-3]}")
                except dico_command.InvalidModule:
                    Settings.logger.warning(
                        f"Skipping Invalid: discordbot.cogs.{filename}")
                    continue

    async def _shards_ready_handler(self):
        user = await self.request_user()
        Settings.logger.info(f"User {user}, {self.guild_count} Guilds {self.shard_count} Shards")
        self.load_modules()

    async def _ready_handler(self, ready: dico.Ready):
        Settings.logger.info(f"Online Shard #{ready.shard_id}")
        await self.shards[ready.shard_id].update_presence(activities=[
            dico.Activity(activity_type=dico.ActivityTypes.LISTENING, name=f"/help, #{ready.shard_id}").to_dict()],
                                                          since=None, status="online", afk=False)

    async def _interaction_error_handler(self, ctx: dico_interaction.InteractionContext, error):
        if isinstance(error, CheckFailed): return

        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))

        tb = ("..." + tb[-1997:]) if len(tb) > 2000 else tb
        with contextlib.suppress(Exception):
            await ctx.send(embed=dico.Embed(description="Error.\n```py\n" + tb + "\n```"))
        Settings.logger.error(
            f"Error on {ctx.data.name}",
            exc_info=(type(error), error, error.__traceback__))
