import typing

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
    # "extensions.programming",
    "extensions.reddit",
    # "extensions.user",
    # "extensions.information",
    "extensions.search",
    "extensions.remind"
]


async def command_prefix(client, message):
    return "sbb "


class soosBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        self.database = None
        self.mystbin = None
        self.reddit = None
        self.aiohttp_session = None
        self.rapid_api_key = None
        self.tmdb_api_key = None
        self.random_cache = {}  # Random caching, can be used for anything.
        self.requests_cache = {}
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
            owner_ids=[632320319662587922, 618209006837825547, 793213521181147178],
            slash_command_guilds=[793213521181147178],
            slash_commands=True,
            help_command=None,
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
        self.rapid_api_key = configuration["rapid_api_key"]
        self.tmdb_api_key = configuration["tmdb_api_key"]

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

    async def get_users_theme_color(self, user_id):
        return discord.Colour.from_rgb(47, 49, 54)
        await self.wait_until_ready()
        cursor = await self.database.cursor()
        await cursor.execute("""SELECT theme FROM user_data WHERE user_id = ?""", (int(user_id),))
        theme = await cursor.fetchone()
        await cursor.close()
        if theme:
            if theme[0] == "dark":
                return discord.Colour.from_rgb(47, 49, 54)
            elif theme[0] == "light":
                return discord.Colour.from_rgb(242, 242, 245)
            else:
                return await commands.ColourConverter().convert(None, theme[0])
        else:
            return discord.Colour.from_rgb(47, 49, 54)

    async def requests(self, url, *,
                       method: str = "get",
                       cache: bool = None,
                       params: dict = None,
                       headers: dict = None,
                       user_agent: str = None):
        if user_agent:
            headers = {"User-Agent": user_agent}
        if cache and self.requests_cache.get(f"URL: {url} PARAMS: {params} HEADERS: {headers}"):
            print("RETURNING CACHE!")
            return self.requests_cache[f"URL: {url} PARAMS: {params} HEADERS: {headers}"]
        if method == "get":
            async with self.aiohttp_session.get(url, params=params, headers=headers) as response:
                data = await response.json()
                if cache:
                    self.requests_cache[f"URL: {url} PARAMS: {params} HEADERS: {headers}"] = data
                return data

    async def get_guilds_prefix(self, guild_id):
        return "sbb "
