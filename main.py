import asyncio
import os
import sys
from typing import List
import argparse

from loguru import logger
from discord.errors import LoginFailure

from uffbot import UffBot


async def main(token: str, active_guilds: List[str]):
    bot = UffBot(active_guilds)

    async with bot:
        try:
            await bot.start(token)
        except LoginFailure:
            logger.error("The token you provided is not valid!")
            sys.exit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--token', type=str, help='Bot token to authenticate with the discord API.')
    parser.add_argument('-g', '--guilds', type=str, help='Discord IDs of active guilds')
    
    args = parser.parse_args()

    if args.token:
        token = args.token
    else:
        try:
            token = os.environ['BOT_TOKEN']
            # os.environ['TOKEN'] = ""
        except KeyError:
            logger.error("You need to set the 'BOT_TOKEN' environmental variable to a valid discord token!")
            sys.exit()

    if args.guilds:
        active_guilds_raw = args.guilds
    else:
        try:
            active_guilds_raw = os.environ['ACTIVE_GUILDS']
        except KeyError:
            active_guilds_raw = ""

    active_guilds = []
    for guild_id in active_guilds_raw.split(','):
        try:
            active_guilds.append(int(guild_id.strip()))
        except ValueError:
            logger.warning(f"Invalid guild id provided: {guild_id}, ignoring")

    asyncio.run(main(token, active_guilds))
