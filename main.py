import asyncio
import os
import sys
from typing import List

from loguru import logger
import discord
from uffbot.uffclient import UffClient
from discord.errors import LoginFailure


def get_active_guild_ids() -> List[int]:
    try:
        active_guilds = []
        for guild_id in os.environ['ACTIVE_GUILDS'].split(','):
            try:
                active_guilds.append(int(guild_id.strip()))
            except ValueError:
                logger.warning(f"Invalid id provided: {guild_id}, ignoring")
        return active_guilds

    except KeyError:
        return []


def get_token() -> str:
    try:
        return os.environ['TOKEN']
    except KeyError:
        logger.error("You need to set the 'TOKEN' environmental variable to a valid discord token!")
        sys.exit()


async def main():
    active_guilds = get_active_guild_ids()
    uff_client = UffClient(active_guilds)

    async with uff_client:
        try:
            await uff_client.start(get_token())
        except LoginFailure:
            logger.error("The token you provided is not valid!")
            sys.exit()


if __name__ == '__main__':
    asyncio.run(main())
