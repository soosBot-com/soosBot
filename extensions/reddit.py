import aiosqlite
from discord.ext import commands, tasks
from discord import ButtonStyle, Interaction, ui, PartialEmoji
import random
import discord
import json
import asyncio
import io


def calculate_storage(number_one, number_two):
    percent = number_one / number_two * 100
    percent = round(percent, -1)
    percent = int(percent)
    if percent > 100:
        percent = 100
    elif percent < 0:
        percent = 0
    return f"https://cdn.soosbot.com/images/percentage/{percent}.png"


class ButtonSaved(ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.user = None
        self.back.disabled = True
        self.delete.disabled = True
        self.page = -1
        self.started = True
        self.client = None
        self.cursor = None
        self.message = None

    async def start(self, client, ctx):
        self.user = ctx.author
        self.client = client

        if ctx.interaction:
            await ctx.interaction.response.defer()
        else:
            loading_message = await ctx.send(
                embed=discord.Embed(color=await self.client.get_users_theme_color(ctx.author.id)).set_footer(
                    text="Loading",
                    icon_url='https://media.discordapp.net/attachments/762482391599022100/829461107752042566/loading.gif'))
        try:
            cursor = await self.client.database.cursor()
        except:
            if not ctx.interaction:
                await loading_message.delete()
            await ctx.send(
                "Well this is awkward, looks like you used this command JUST as I restarted.. please give me a moment "
                "to connect to my database, (5-10 seconds), and try again.")
            return
        await cursor.execute("""SELECT * FROM saved_memes WHERE user_id = ?""", (ctx.author.id,))
        memes = await cursor.fetchall()
        if len(memes) == 0:
            if not ctx.interaction:
                await loading_message.delete()
            await ctx.send(embed=discord.Embed(title="You haven't saved any memes.",
                                               color=await self.client.get_users_theme_color(ctx.author.id)).set_image(
                url="https://cdn.soosbot.com/images/commands/empty.png"))
            return
        else:
            if not ctx.interaction:
                await loading_message.delete()
            embed = discord.Embed(title="This is where you can browse your saved posts!",
                                  color=await self.client.get_users_theme_color(ctx.author.id))
            embed.add_field(name="** **", value="Press the <:soosBot_forward:795309161054470144> to continue.",
                            inline=False)

            embed.add_field(name="** **\nPost Storage", value=f"{len(memes)}/25 ({round((len(memes) / 25) * 100)}%)",
                            inline=False)
            embed.set_author(icon_url=ctx.author.avatar.url, name=ctx.author)
            embed.set_image(url=calculate_storage(len(memes), 25))
            self.message = await ctx.send(embed=embed, view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        embed = discord.Embed(title="Timed out", color=discord.Colour.red())
        await self.message.edit(embed=embed, view=self)

    @ui.button(emoji=PartialEmoji(name="soosBot_back", id=795306327425155082, animated=False),
               style=ButtonStyle.secondary)
    async def back(self, button: ui.Button, interaction: Interaction):
        if interaction.user != self.user:
            embed = discord.Embed(description="You cannot control this command because you did not execute it.",
                                  color=discord.Colour.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.cursor.execute("""SELECT * FROM saved_memes WHERE user_id = ?""", (self.user.id,))
        memes = await self.cursor.fetchall()
        self.page -= 1
        if self.page < 0:
            self.page = len(memes) - 1
        em = discord.Embed(title=memes[self.page][2],
                           color=await self.client.get_users_theme_color(self.user.id))
        em.set_author(
            name=f"r/{memes[self.page][1]}")
        em.set_footer(text=f"Page {self.page + 1}/{len(memes)}")

        em.url = memes[self.page][3]
        content = memes[self.page][4]
        await self.cursor.execute("SELECT * FROM subreddits WHERE subreddit = ?", (memes[self.page][1],))
        data = await self.cursor.fetchone()
        if not data:
            content = "https://cdn.soosbot.com/images/commands/notApproved.png"
        if ".gifv" in content or ".mp4" in content or ".webm" in content or "youtube" in content or "v.redd.it" in content or "youtu.be" in content or 'comments' in content or 'gfycat.com' in content or "kapwing" in content or "kapwi" in content:
            em.description = content
            await interaction.response.edit_message(
                embed=em, view=self)
        else:
            em.set_image(url=content)
            await interaction.response.edit_message(
                embed=em, view=self)

    @ui.button(emoji=PartialEmoji(name="soosBot_forward", id=795309161054470144, animated=False),
               style=ButtonStyle.secondary)
    async def forward(self, button: ui.Button, interaction: Interaction):
        if interaction.user != self.user:
            embed = discord.Embed(description="You cannot control this command because you did not execute it.",
                                  color=discord.Colour.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        if not self.cursor:
            self.cursor = await self.client.database.cursor()

        await self.cursor.execute("""SELECT * FROM saved_memes WHERE user_id = ?""", (self.user.id,))
        memes = await self.cursor.fetchall()
        self.delete.disabled = False
        self.back.disabled = False
        self.page += 1
        if self.page > len(memes) - 1:
            self.page = 0

        em = discord.Embed(title=memes[self.page][2],
                           color=await self.client.get_users_theme_color(self.user.id))
        em.set_author(
            name=f"r/{memes[self.page][1]}")
        em.set_footer(text=f"Page {self.page + 1}/{len(memes)}")
        em.url = memes[self.page][3]
        content = memes[self.page][4]
        await self.cursor.execute("SELECT * FROM subreddits WHERE subreddit = ?", (memes[self.page][1],))
        data = await self.cursor.fetchone()
        if not data:
            content = "https://cdn.soosbot.com/images/commands/notApproved.png"
        if self.page == 0 and self.started:
            if ".gifv" in content or ".mp4" in content or ".webm" in content or "youtube" in content or "v.redd.it" in content or "youtu.be" in content or 'comments' in content or 'gfycat.com' in content or "kapwing" in content or "kapwi" in content:
                em.description = content
                await interaction.response.edit_message(
                    embed=em, view=self)
            else:
                em.set_image(url=content)
                await interaction.response.edit_message(
                    embed=em, view=self)
        else:
            if ".gifv" in content or ".mp4" in content or ".webm" in content or "youtube" in content or "v.redd.it" in content or "youtu.be" in content or 'comments' in content or 'gfycat.com' in content or "kapwing" in content or "kapwi" in content:
                em.description = content
                await interaction.response.edit_message(
                    embed=em, view=self)
            else:
                em.set_image(url=content)
                await interaction.response.edit_message(
                    embed=em, view=self)

    @ui.button(label="Delete", emoji=PartialEmoji(name="soosBot_trash", id=795313016908152833, animated=False),
               style=ButtonStyle.danger)
    async def delete(self, button: ui.Button, interaction: Interaction):
        await self.cursor.execute("""SELECT * FROM saved_memes WHERE user_id = ?""", (self.user.id,))
        memes = await self.cursor.fetchall()
        if interaction.user != self.user:
            embed = discord.Embed(description="You cannot control this command because you did not execute it.",
                                  color=discord.Colour.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.cursor.execute(
            """DELETE FROM saved_memes WHERE user_id = ? AND subreddit = ? AND title = ? AND url = ? AND 
            content = ?""",
            (memes[self.page][0], memes[self.page][1], memes[self.page][2], memes[self.page][3], memes[self.page][4]))
        await self.client.database.commit()
        await self.cursor.execute("""SELECT * FROM saved_memes WHERE user_id = ?""", (self.user.id,))
        memes = await self.cursor.fetchall()
        self.page -= 1
        if self.page < 0:
            self.page = len(memes) - 1
        try:
            em = discord.Embed(title=memes[self.page][2],
                               color=await self.client.get_users_theme_color(self.user.id))
            em.set_author(
                name=f"r/{memes[self.page][1]}")
            em.set_footer(text=f"Page {self.page + 1}/{len(memes)}")
            em.url = memes[self.page][3]
            content = memes[self.page][4]
            await self.cursor.execute("SELECT * FROM subreddits WHERE subreddit = ?", (memes[self.page][1],))
            data = await self.cursor.fetchone()
            if not data:
                content = "https://cdn.soosbot.com/images/commands/notApproved.png"
            if ".gifv" in content or ".mp4" in content or ".webm" in content or "youtube" in content or "v.redd.it" in content or "youtu.be" in content or 'comments' in content or 'gfycat.com' in content or "kapwing" in content or "kapwi" in content:
                em.description = content
                await interaction.response.edit_message(
                    embed=em, view=self)
            else:
                em.set_image(url=content)
                await interaction.response.edit_message(
                    embed=em, view=self)
        except IndexError:
            for button in self.children:
                button.disabled = True
            embed = discord.Embed(title="You haven't saved any memes.",
                                  color=await self.client.get_users_theme_color(self.user.id)).set_image(
                url="https://cdn.soosbot.com/images/commands/empty.png")
            await interaction.response.edit_message(
                embed=embed, view=self)
            self.stop()


class RedditCommands(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.cached_memes = {}
        self.refresh_cached_memes.start()
        self.active_memes_delete.start()
        self.seen_memes = {}

    @tasks.loop(seconds=300)
    async def refresh_cached_memes(self):
        posts = []
        sub = await self.client.reddit.subreddit("dankmemes")
        await sub.load()
        async for submission in sub.hot(limit=50):
            posts.append(submission)
        self.cached_memes = posts
        self.seen_memes = {}

    @tasks.loop(hours=24)
    async def active_memes_delete(self):
        await self.client.wait_until_ready()
        cursor = await self.client.database.cursor()
        await cursor.execute("""DELETE FROM active_memes""")
        await self.client.database.commit()

    @active_memes_delete.before_loop
    async def before_active_memes_delete(self):
        await asyncio.sleep(86400)

    async def send_reddit_post(self, ctx, subreddit, title, author, url, content, score, comments, *, savable, nsfw):
        cursor = await self.client.database.cursor()
        embed = discord.Embed(title=title,
                              color=await self.client.get_users_theme_color(ctx.author.id))
        embed.set_author(name=f"r/{subreddit}")
        embed.url = url
        if nsfw:
            embed.set_thumbnail(url="https://cdn.soosbot.com/images/commands/NSFW.png")
        embed.set_footer(text=f"🔺 {score} • 💬 {comments} • u/{author}")
        valid_file_formats = ("webp", "png", "gif", "jpg")
        if content.split('.')[-1] in valid_file_formats:
            embed.set_image(url=content)
            post = await ctx.send(embed=embed)
        else:
            await ctx.send(embed=embed)
            post = await ctx.channel.send(content=url)
        if savable:
            try:
                await cursor.execute("""INSERT INTO active_memes VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                     (ctx.guild.id, ctx.channel.id, post.id, subreddit, title, url, content))
            except aiosqlite.OperationalError:
                await cursor.execute("""CREATE TABLE active_memes (server_id integer, channel_id integer, message_id 
                integer, subreddit text, title text, url text, content text)""")
                await cursor.execute("""
                INSERT INTO active_memes VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                     (ctx.guild.id, ctx.channel.id, post.id, subreddit, title, url, content))
            await self.client.database.commit()
            await post.add_reaction("<:soosBot_save:795131937592311848>")
            await cursor.close()
            print("meme added t")

    @commands.command(slash_command=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def meme(self, ctx):
        """Retrieve a post from r/dankmemes!"""
        if not self.cached_memes:
            return await ctx.send(embed=discord.Embed(title="Please wait a few moments until meme caching is done.",
                                                      colour=await self.client.get_users_theme_color(ctx.author.id)))
        while True:
            post = random.choice(self.cached_memes)
            url = "https://www.reddit.com" + post.permalink
            try:
                if url in self.seen_memes[ctx.guild.id]:
                    continue
                elif post.over_18:
                    continue
                else:
                    break
            except KeyError:
                self.seen_memes[ctx.guild.id] = []
        title = post.title
        content = post.url
        score = post.score
        comments = post.num_comments
        author = post.author.name
        await self.send_reddit_post(ctx, "dankmemes", title, author, url, content, score, comments, savable=True,
                                    nsfw=False)
        self.seen_memes[ctx.guild.id].append(url)

    # @cog_ext.cog_slash(name="meme", guild_ids=[793213521181147178, 536983354936000537], description="Retrieve top posts from r/dankmemes")
    # async def slash_meme(self, ctx):
    #     if not self.cached_memes:
    #         return await ctx.send(embed=discord.Embed(title="Please wait a few moments until meme caching is done.",
    #                                                   colour=await self.client.get_users_theme_color(ctx.author.id)))
    #     while True:
    #         post = random.choice(self.cached_memes['data']['children'])
    #         url = ('https://reddit.com' + post['data']['permalink'])
    #         try:
    #             if url in self.seen_memes[ctx.guild.id]:
    #                 continue
    #             elif post["data"]["over_18"]:
    #                 continue
    #             else:
    #                 break
    #         except KeyError:
    #             self.seen_memes[ctx.guild.id] = []
    #     content = post['data']['url']
    #     score = post['data']['score']
    #     comments = post['data']['num_comments']
    #     title = post['data']['title']
    #     author = post['data']['author']
    #
    #     cursor = await self.client.database.cursor()
    #     embed = discord.Embed(title=title,
    #                           color=await self.client.get_users_theme_color(ctx.author.id))
    #     embed.set_author(name=f"r/darkmemes")
    #     embed.url = url
    #     embed.set_footer(text=f"🔺 {score} • 💬 {comments} • u/{author}")
    #     valid_file_formats = ("webp", "png", "gif", "jpg")
    #     if content.split('.')[-1] in valid_file_formats:
    #         embed.set_image(url=content)
    #         post = await ctx.send(embed=embed)
    #     else:
    #         await ctx.send(embed=embed)
    #         post = await ctx.channel.send(content=url)
    #     try:
    #         await cursor.execute("""INSERT INTO active_memes VALUES (?, ?, ?, ?, ?, ?, ?)""",
    #                              (ctx.guild.id, ctx.channel.id, post.id, "dankmemes", title, url, content))
    #     except aiosqlite.OperationalError:
    #         await cursor.execute("""CREATE TABLE active_memes (server_id integer, channel_id integer, message_id
    #         integer, subreddit text, title text, url text, content text)""")
    #         await cursor.execute("""
    #         INSERT INTO active_memes VALUES (?, ?, ?, ?, ?, ?, ?)""",
    #                              (ctx.guild.id, ctx.channel.id, post.id, "dankmemes", title, url, content))
    #     await self.client.database.commit()
    #     await post.add_reaction("<:soosBot_save:795131937592311848>")
    #     await cursor.close()
    #     self.seen_memes[ctx.guild.id].append(url)

    @meme.error
    async def meme_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
            embed = discord.Embed(title="Cooldown",
                                  description=f"Please try again in {round(error.retry_after)} seconds.",
                                  color=discord.Colour.from_rgb(47, 49, 54))
            await ctx.send(embed=embed)
        else:
            raise error

    @commands.command(aliases=["r"], slash_command=True)
    @commands.cooldown(1, 4, commands.BucketType.user)
    async def posts(self, ctx, *, subreddit=commands.Option(description="A valid reddit subreddit.")):
        """Retrieve a post from the provided subreddit!"""
        sub = await self.client.reddit.subreddit(subreddit)
        await sub.load()
        if sub.over18:
            if ctx.channel.is_nsfw():
                if ctx.interaction:
                    await ctx.interaction.response.defer()
                else:
                    em = discord.Embed(color=await self.client.get_users_theme_color(ctx.author.id))
                    em.set_author(name="Loading",
                                  icon_url="https://media.discordapp.net/attachments/762482391599022100"
                                           "/829461107752042566/loading.gif")
                    loading_message = await ctx.send(embed=em)
                posts = []
                async for submission in sub.hot(limit=50):
                    posts.append(submission)
                random_post = random.choice(posts)
                title = random_post.title
                content = random_post.url
                score = random_post.score
                comments = random_post.num_comments
                author = random_post.author.name
                url = "https://www.reddit.com" + random_post.permalink
                await self.send_reddit_post(ctx, subreddit, title, author, url, content, score, comments, savable=False,
                                            nsfw=True)
                if not ctx.interaction:
                    await loading_message.delete()
            else:
                await ctx.send(embed=discord.Embed(title="BONK",
                                                   colour=discord.Colour.red()).
                               set_image(url="http://cdn.soosbot.com/images/commands/nsfwMessage.gif"))
        else:
            cursor = await self.client.database.cursor()
            try:
                await cursor.execute("SELECT * FROM subreddits WHERE subreddit = ?", (subreddit,))
            except aiosqlite.OperationalError:
                await cursor.execute("""CREATE TABLE subreddits (subreddit text)""")
                await cursor.execute("SELECT * FROM subreddits WHERE subreddit = ?", (subreddit,))
            data = await cursor.fetchone()
            if data or ctx.channel.is_nsfw():
                if ctx.interaction:
                    await ctx.interaction.response.defer()
                else:
                    em = discord.Embed(color=await self.client.get_users_theme_color(ctx.author.id))
                    em.set_author(name="Loading",
                                  icon_url="https://media.discordapp.net/attachments/762482391599022100"
                                           "/829461107752042566/loading.gif")
                    loading_message = await ctx.send(embed=em)
                posts = []
                async for submission in sub.hot(limit=50):
                    posts.append(submission)
                random_post = random.choice(posts)
                if random_post.over_18:
                    if not ctx.interaction:
                        await loading_message.delete()
                    await ctx.send("Post was NSFW and could not be shown")
                    return
                title = random_post.title
                content = random_post.url
                score = random_post.score
                comments = random_post.num_comments
                author = random_post.author.name
                url = "https://www.reddit.com" + random_post.permalink
                if data:
                    saveable = True
                else:
                    saveable = False
                await self.send_reddit_post(ctx, subreddit, title, author, url, content, score, comments,
                                            savable=saveable,
                                            nsfw=False)
                if not ctx.interaction:
                    await loading_message.delete()
            else:
                embed = discord.Embed(title="Unapproved Subreddit",
                                      description="This subreddit is not flagged as NSFW on Reddit, but is not "
                                                  "approved by soosBot. This system is in place to filter out "
                                                  "subreddits which can be made to bypass Reddit's NSFW "
                                                  "guidelines.\n** **\nIf you would like to suggest a subreddit to be "
                                                  f"approved, please run this command:\n**`"
                                                  f"{await self.client.get_guilds_prefix(ctx.guild.id)}subreddit "
                                                  f"suggest "
                                                  f"{{subreddit}}`**",
                                      color=await self.client.get_users_theme_color(ctx.author.id))
                await ctx.send(embed=embed)
            await cursor.close()

    @posts.error
    async def posts_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
            embed = discord.Embed(title="Cooldown",
                                  description=f"Please try again in {round(error.retry_after)} seconds.",
                                  color=discord.Colour.from_rgb(47, 49, 54))
            await ctx.send(embed=embed)
        elif isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
            em = discord.Embed(title="Please specify a subreddit.\n EX : ``sb posts ksi``", color=discord.Colour.red())
            await ctx.send(embed=em)
        elif isinstance(error, discord.ext.commands.errors.CommandInvokeError):
            em = discord.Embed(title="Subreddit not found",
                               color=discord.Colour.red())
            await ctx.send(embed=em)
            raise error
        else:
            await self.client.log_error(error, ctx.command)

    @commands.group(invoke_without_command=True, aliases=["sub"])
    async def subreddit(self, ctx):
        await ctx.send("Subreddit commands. \n`sb subreddit suggest {subreddit}\n`sb subreddit report {subreddit}")

    @subreddit.command(name="suggest")
    @commands.cooldown(3, 3600, commands.BucketType.user)
    async def subreddit_suggest_command(self, ctx, subreddit, *, reason=None):
        sub = await self.client.reddit.subreddit(subreddit)
        await sub.load()
        if sub.over18:
            embed = discord.Embed(description=f"That subreddit is flagged as NSFW on reddit and cannot be suggested.",
                                  color=discord.Colour.red())
            await ctx.send(embed=embed)
            return
        subreddit = subreddit.replace(r"r/", "")
        cursor = await self.client.database.cursor()
        await cursor.execute("""SELECT * FROM subreddits WHERE subreddit = ?""", (subreddit,))
        data = await cursor.fetchone()
        if data:
            embed = discord.Embed(description=f"r/{subreddit} is already approved",
                                  color=discord.Colour.red())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(color=await self.client.get_users_theme_color(ctx.author.id),
                                  description=f"[r/{subreddit}](https://reddit.com/r/{subreddit})\n")
            embed.set_author(name=f"{str(ctx.author)}  ({ctx.author.id})", icon_url=ctx.author.avatar.url)
            if reason:
                embed.description = embed.description + "\n" + reason
            channel = self.client.get_guild(762429730695675905).get_channel(845033287579729990)
            await channel.send(embed=embed)
            embed = discord.Embed(description=f"Summited your request to get r/{subreddit} approved",
                                  color=await self.client.get_users_theme_color(ctx.author.id))
            await ctx.send(embed=embed)
        await cursor.close()

    @subreddit.command(name="report")
    @commands.cooldown(3, 3600, commands.BucketType.user)
    async def subreddit_report_command(self, ctx, subreddit, *, reason=None):
        subreddit = subreddit.replace(r"r/", "")
        cursor = await self.client.database.cursor()
        await cursor.execute("""SELECT * FROM subreddits WHERE subreddit = ?""", (subreddit,))
        data = await cursor.fetchone()
        if not data:
            embed = discord.Embed(description=f"r/{subreddit} is not approved, you cannot report it.",
                                  color=discord.Colour.red())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(color=await self.client.get_users_theme_color(ctx.author.id),
                                  description=f"[r/{subreddit}](https://reddit.com/r/{subreddit})\n")
            embed.set_author(name=f"{str(ctx.author)}  ({ctx.author.id})", icon_url=ctx.author.avatar.url)
            if reason:
                embed.description = embed.description + "\n" + reason
            channel = self.client.get_guild(762429730695675905).get_channel(845033215906545744)
            await channel.send(embed=embed)
            embed = discord.Embed(description=f"Summited your request to get r/{subreddit} removed.",
                                  color=await self.client.get_users_theme_color(ctx.author.id))
            await ctx.send(embed=embed)
        await cursor.close()

    @subreddit.command(name="add", aliases=["approve"])
    async def subreddit_add_command(self, ctx, subreddit):
        sub = await self.client.reddit.subreddit(subreddit)
        await sub.load()
        if ctx.author.id == 632320319662587922 or ctx.author.id == 618209006837825547 or ctx.author.id == 168422909482762240:
            cursor = await self.client.database.cursor()
            await cursor.execute("""SELECT * FROM subreddits WHERE subreddit = ?""", (subreddit,))
            data = await cursor.fetchone()
            if data:
                await ctx.send(
                    embed=discord.Embed(description=f"r/{subreddit} is already approved", color=discord.Colour.red()))
            else:
                await cursor.execute("""INSERT INTO subreddits VALUES (?)""", (subreddit,))
                embed = discord.Embed(description=f"r/{subreddit} was approved",
                                      color=await self.client.get_users_theme_color(ctx.author.id))
                await ctx.send(embed=embed)
                embed = discord.Embed(description=f"r/{subreddit} was approved",
                                      color=discord.Colour.from_rgb(47, 49, 54))
                channel = self.client.get_guild(762429730695675905).get_channel(845046061575176193)
                await channel.send(embed=embed)
            await cursor.close()
            await self.client.database.commit()

    @subreddit_add_command.error
    async def subreddit_add_command_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.CommandInvokeError):
            await ctx.send(embed=discord.Embed(description=f"Subreddit not found",
                                               color=discord.Colour.red()))

        else:
            self.client.log_error(error, ctx.command)

    @subreddit_add_command.error
    async def subreddit_add_command_error(self, ctx, error):
        await ctx.send(error)
        await self.client.log_error(error, ctx.command)

    @subreddit.command(name="remove", aliases=["deny"])
    async def subreddit_remove_command(self, ctx, subreddit, user_id=None):
        if ctx.author.id == 632320319662587922 or ctx.author.id == 618209006837825547 or ctx.author.id == 168422909482762240:
            cursor = await self.client.database.cursor()
            await cursor.execute("""SELECT * FROM subreddits WHERE subreddit = ?""", (subreddit,))
            data = await cursor.fetchone()
            if not data:
                await ctx.send(
                    embed=discord.Embed(description=f"r/{subreddit} is not approved", color=discord.Colour.red()))
            else:
                await cursor.execute("""DELETE FROM subreddits WHERE subreddit = ? ;""", (subreddit,))
                embed = discord.Embed(description=f"r/{subreddit} was removed",
                                      color=await self.client.get_users_theme_color(ctx.author.id))
                await ctx.send(embed=embed)
                channel = self.client.get_guild(762429730695675905).get_channel(845046061575176193)
                embed = discord.Embed(description=f"r/{subreddit} was removed",
                                      color=discord.Colour.from_rgb(47, 49, 54))
                await channel.send(embed=embed)
            await cursor.close()
            await self.client.database.commit()

    @subreddit_suggest_command.error
    @subreddit_report_command.error
    async def subreddit_suggestion_and_report_commands_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
            await ctx.send("You are missing and argument")
        elif isinstance(error, discord.ext.commands.errors.CommandOnCooldown):
            em = discord.Embed(
                title="You can only suggest/report 3 subreddits per hour.",
                colour=discord.Colour.red()
            )
            cooldowntime = '{:.2f}'.format(error.retry_after)
            cooldowntime = float(cooldowntime)
            cooldowntime = cooldowntime / 60
            cooldowntime = round(cooldowntime)
            msg = 'Please try again in ``{:.2f}`` seconds'.format(error.retry_after)
            em.add_field(name="Cooldown : ``One hour``", value=f"{msg} or around ``{cooldowntime} minutes``")
            await ctx.send(embed=em)
        elif isinstance(error, discord.ext.commands.errors.CommandInvokeError):
            await ctx.send(embed=discord.Embed(description=f"Subreddit not found",
                                               color=discord.Colour.red()))
            await ctx.command.reset_cooldown(ctx)
        else:
            await self.client.log_error(error, ctx.command)

    @commands.command(slash_command=True)
    async def saved(self, ctx):
        """Browse your saved memes!"""
        await ButtonSaved().start(self.client, ctx)

    @commands.Cog.listener("on_raw_reaction_add")
    async def post_save_function(self, payload):
        user = await self.client.fetch_user(payload.user_id)
        if payload.user_id == self.client.user.id or user.bot:
            return
        if str(payload.emoji) == "<:soosBot_save:795131937592311848>":
            cursor = await self.client.database.cursor()
            await cursor.execute(
                """SELECT * FROM active_memes WHERE server_id = ? AND  channel_id = ? AND message_id = ?""",
                (payload.guild_id, payload.channel_id, payload.message_id))
            meme_ = await cursor.fetchone()
            if meme_:
                channel = self.client.get_guild(meme_[0]).get_channel(meme_[1])
                message = await channel.fetch_message(payload.message_id)
                try:
                    await cursor.execute("""SELECT * FROM saved_memes WHERE user_id = ?""", (payload.user_id,))
                    test = await cursor.fetchall()
                    saved_memes = len(test)
                except:
                    await cursor.execute(
                        """CREATE TABLE saved_memes (user_id integer, subreddit text, title text, url text, 
                        content text)""")
                    saved_memes = 0
                if saved_memes >= 25:
                    embed = discord.Embed(title="Storage exceed",
                                          description="You have exceeded your storage of 25 posts.\nPlease delete some "
                                                      "of them to store more.",
                                          colour=discord.Colour.red())
                    embed.set_author(name=user, icon_url=user.avatar.url)
                    await message.reply(embed=embed)
                    return
                await cursor.execute("""INSERT INTO saved_memes VALUES (?, ?, ?, ?, ?)""",
                                     (payload.user_id, meme_[3], meme_[4], meme_[5], meme_[6]))
                await self.client.database.commit()
                embed = discord.Embed(title="Post saved",
                                      color=await self.client.get_users_theme_color(payload.member.id))
                embed.set_author(name=user, icon_url=user.avatar.url)
                embed.add_field(name="Storage",
                                value=f"{saved_memes + 1}/25 ({round(((saved_memes + 1) / 25) * 100)}%)")
                url = calculate_storage(saved_memes, 25)
                embed.set_image(url=url)
                await message.reply(embed=embed, delete_after=7)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        user = await self.client.fetch_user(payload.user_id)
        if payload.user_id == self.client.user.id or user.bot == True:
            return
        if str(payload.emoji) == "<:soosBot_save:795131937592311848>":
            cursor = await self.client.database.cursor()
            await cursor.execute(
                """SELECT * FROM active_memes WHERE server_id = ? AND  channel_id = ? AND message_id = ?""",
                (payload.guild_id, payload.channel_id, payload.message_id))
            meme_ = await cursor.fetchone()
            channel = self.client.get_guild(payload.guild_id).get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            if meme_:
                await cursor.execute(
                    """SELECT * FROM saved_memes WHERE user_id = ? AND subreddit = ? AND title = ? AND url = ? AND 
                    content = ?""",
                    (user.id, meme_[3], meme_[4], meme_[5], meme_[6]))
                _ = await cursor.fetchall()
                if len(_) > 0:
                    await cursor.execute(
                        """DELETE FROM saved_memes WHERE user_id = ? AND subreddit = ? AND title = ? AND url = ? AND 
                        content = ?""",
                        (user.id, meme_[3], meme_[4], meme_[5], meme_[6]))
                    await self.client.database.commit()
                else:
                    embed = discord.Embed(title="Error", description="Post couldn't be unsaved due to it not being in "
                                                                     "your gallery.",
                                          color=await self.client.get_users_theme_color(user.id))
                    embed.set_author(name=user, icon_url=user.avatar.url)
                    await message.reply(embed=embed)
                    return
                embed = discord.Embed(title="Post unsaved", color=await self.client.get_users_theme_color(user.id))
                embed.set_author(name=user, icon_url=user.avatar.url)
                await message.reply(embed=embed, delete_after=7)


def setup(client):
    client.add_cog(RedditCommands(client))
