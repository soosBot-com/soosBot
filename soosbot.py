import discord
from discord.ext import commands
import aiohttp
import aiosqlite
import asyncpraw
import mystbin
from utilities import loader
import jishaku

extensions = [
    'jishaku',
    "extensions.programming"
]


async def command_prefix(client, message):
    return "sbb "


class soosBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        self.database = None
        self.mystbin = None
        self.reddit = None
        self.aiohttp_session = None
        self.user_agent = f"soosBot - Multi-Purpose Discord Bot. [soosBot.com] | enhanced-discord.py version : " \
                          f"{discord.__version__} | aiohttp version : {aiohttp.__version__} "
        super().__init__(
            command_prefix=command_prefix,
            case_insensitive=True,
            intents=discord.Intents(guilds=True, messages=True, members=False, reactions=True),
            activity=discord.Activity(
                type=discord.ActivityType.playing, name="soosBot.com | @soosBot"
            ),
            status=discord.Status.online,
            owner_ids=[632320319662587922, 618209006837825547],
            slash_commands=True,
            # help_command=None,
        )

    async def start(self, *args, **kwargs):
        self.database = await aiosqlite.connect("database.db")
        self.aiohttp_session = aiohttp.ClientSession()
        self.mystbin = mystbin.Client(session=self.aiohttp_session)
        configuration = loader.load_json("configuration.json")
        self.reddit = asyncpraw.Reddit(client_id=configuration["praw"]["client_id"],
                                       client_secret=configuration["praw"]["client_secret"],
                                       user_agent=configuration["praw"]["user_agent"],
                                       username=configuration["praw"]["username"],
                                       password=configuration["praw"]["password"],
                                       requestor_kwargs={"session": self.aiohttp_session})

        # Load all cogs in the list "cogs" to client.
        for extension in extensions:
            self.load_extension(extension)

        await super().start(*args, **kwargs)

    async def close(self):
        await self.aiohttp_session.close()
        await self.database.close()
        await self.mystbin.close()
        await self.reddit.close()
        await super().close()
        print(f"{self.user} stopped.")


