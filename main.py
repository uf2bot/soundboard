import asyncio
import os
import sys
from typing import List

from loguru import logger
from uffbot.bot import UffBot
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
        token = os.environ['TOKEN']
        os.environ['TOKEN'] = ""
        return token
    except KeyError:
        logger.error("You need to set the 'TOKEN' environmental variable to a valid discord token!")
        sys.exit()


async def main():
    active_guilds = get_active_guild_ids()
    bot = UffBot(active_guilds)

    async with bot:
        try:
            await bot.start(get_token())
        except LoginFailure:
            logger.error("The token you provided is not valid!")
            sys.exit()


if __name__ == '__main__':
    asyncio.run(main())
