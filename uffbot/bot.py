from typing import List, Union

from loguru import logger

import discord
from discord.ext import commands

from uffbot.soundboard import SoundBoard


class UffBot(commands.Bot):
    def __init__(self, active_guild_ids: Union[List[int]], **kwargs):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__('!', intents=intents, **kwargs)

        self.active_guild_ids = active_guild_ids

    async def command_init(self):
        # clear all commands that may already be registered
        self.tree.clear_commands(guild=None)
        await self.tree.sync()

        for guild_id in self.active_guild_ids:
            guild = discord.Object(id=guild_id)
            self.tree.add_command(SoundBoard(self), guild=guild)
            try:
                await self.tree.sync(guild=guild)
                logger.info(f"successfully added commands to guild with id '{guild_id}'")
            except discord.Forbidden:
                logger.warning(f"The bot does not have access to a guild with the id '{guild_id}', ignoring.")

    async def on_ready(self):
        app_info = await self.application_info()

        logger.info(f'logged in as {self.user}')
        servers = "\n".join(str(g) for g in self.guilds)
        logger.info(f'i am a member of the following servers:\n{servers}')
        logger.info(f'Use the following URL to add the bot to a server:\n'
                    f'https://discordapp.com/oauth2/authorize?client_id={app_info.id}&scope=bot')

        await self.command_init()

    async def on_message(self, message):
        logger.debug(f'message from {message.author}: {message.content}')
