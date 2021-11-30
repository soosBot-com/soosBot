import random
import aiosqlite
import discord
from discord.ext import commands
from datetime import datetime


class RedditCommands(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.cache = {}  # Cache of subreddits.
        self.seen_memes = {}  # Cache of the posts seen by each guild. This is so dupes arnt sent to users.

    async def get_subreddit_post(self, subreddit):
        # If the cache is there, and the cache is younger than 5
        # minutes, return the cache instead of fetching new data.
        if self.cache.get(subreddit) and (datetime.now() - self.cache[subreddit]["cached"]).total_seconds() < 300:
            return random.choice(self.cache[subreddit]["posts"])
        else:
            posts = []
            sub = await self.client.reddit.subreddit(subreddit, fetch=True)
            async for submission in sub.hot(limit=50):
                posts.append(submission)
            self.cache[subreddit] = {
                "posts": posts,
                "cached": datetime.now(),
                "icon": sub.icon_img if sub.icon_img else "",
                "nsfw": sub.over_18
            }
            self.seen_memes[subreddit] = {}

            return random.choice(self.cache[subreddit]["posts"])

    async def send_post(
            self,
            ctx,
            subreddit,
            title,
            author,
            url,
            content,
            score,
            comments,
            *, savable=True, nsfw=False
    ):
        if nsfw and savable:
            savable = False

        embed = discord.Embed(title=title, color=await self.client.get_users_theme_color(ctx.author.id))
        embed.set_author(name=f"r/{subreddit}", icon_url=self.cache[subreddit]["icon"])
        embed.set_footer(text=f"🔺 {score} • 💬 {comments} • u/{author}")
        embed.url = url

        valid_file_formats = ("webp", "png", "gif", "jpg")

        if content.split('.')[-1] in valid_file_formats:
            embed.set_image(url=content)
            message = await ctx.send(embed=embed)
        else:
            await ctx.send(embed=embed)
            message = await ctx.channel.send(content=url)

        if savable:
            cursor = await self.client.database.cursor()
            try:
                await cursor.execute("""INSERT INTO active_memes VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                     (ctx.guild.id, ctx.channel.id, message.id, subreddit, title, url, content))
            except aiosqlite.OperationalError:
                await cursor.execute("""CREATE TABLE active_memes (server_id integer, channel_id integer, message_id 
                integer, subreddit text, title text, url text, content text)""")
                await cursor.execute("""
                INSERT INTO active_memes VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                     (ctx.guild.id, ctx.channel.id, message.id, subreddit, title, url, content))
            await self.client.database.commit()
            await message.add_reaction("<:soosBot_save:795131937592311848>")
            await cursor.close()

    @commands.command(alaises=["r"])
    async def posts(self, ctx, subreddit):
        can_be_nsfw = ctx.channel.is_nsfw()


        post = await self.get_subreddit_post(subreddit)
        post.over_18 = True
        can_be_nsfw = False
        # Expected result: Can send
        if not can_be_nsfw and not post.over_18:
            "Cant send"
        else:
            "Can send!"

        if self.cache[subreddit]["nsfw"] and not can_be_nsfw:
            return await ctx.send("nsfw!")

        if post.permalink in self.seen_memes[subreddit].get(ctx.guild.id, []) \
                or True:  # Weird logic, if post_over 18 AND can be nsfw, dont go into the if statment.
            cached_posts = self.cache[subreddit]["posts"].copy()
            while len(cached_posts) != 0:
                post = random.choice(cached_posts)
                if post.permalink in self.seen_memes[subreddit].get(ctx.guild.id, []) or post.over_18:
                    cached_posts.remove(post)
                else:
                    break
            else:
                if post.over_18:
                    return await ctx.send("You can out of cached posts, AND the last post was nsfw!")
                else:
                    await ctx.send("You can out of cached posts. Try again later.")
        title = post.title
        content = post.url
        score = post.score
        comments = post.num_comments
        author = post.author.name
        url = "https://www.reddit.com" + post.permalink
        await self.send_post(ctx, subreddit, title, author, url, content, score, comments)
        if self.seen_memes[subreddit].get(ctx.guild.id):
            self.seen_memes[subreddit][ctx.guild.id].append(post.permalink)
        else:
            self.seen_memes[subreddit][ctx.guild.id] = [post.permalink]


def setup(client):
    client.add_cog(RedditCommands(client))
