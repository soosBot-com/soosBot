import discord
from discord.ext import commands
from jishaku.codeblocks import codeblock_converter


class ProgrammingCommands(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(aliases=["run"])
    async def run(self, ctx, *, code: codeblock_converter):
        if not code.language:
            return await ctx.send("No language provided")

        if not code.content:
            return await ctx.send("No code provided")

        embed = discord.Embed(color=0x2f3136).set_author(name="Loading",
                                                         icon_url="https://media.discordapp.net/attachments"
                                                                  "/762482391599022100/829461107752042566/loading.gif")
        loading_message = await ctx.message.reply(embed=embed)

        response = await self.client.aiohttp_session.post("https://emkc.org/api/v1/piston/execute", json={
            "language": code.language,
            "source": code.content
        })

        data = await response.json()

        if data["ran"]:
            if data["stdout"] != "":
                embed = discord.Embed(title=f"{data['language'].title()} `v{data['version']}`",
                                      description=f"```{code.language}\n{data['stdout']}```",
                                      color=0x2f3136)
                await loading_message.edit(embed=embed)
            else:
                embed = discord.Embed(title=f"{data['language'].title()} `v{data['version']}`",
                                      description=f"Your script ran without any output.",
                                      color=0x2f3136)
                await loading_message.edit(embed=embed)

        else:
            if data["stderr"] != "":
                description = ""
                if data["stdout"]:
                    description += f"**Output**\n```\n{data['stdout']}\n\n```"
                description += f"**Traceback**\n```\n{data['stderr']}```"
                embed = discord.Embed(title="Error", description=description, color=discord.Color.red())
                embed.set_footer(text=f"{data['language'].title()} v{data['version']}")
                await loading_message.edit(embed=embed)
            else:
                description = "The program ran for too long and was terminated."
                if data["stdout"] != "":
                    output = (await self.client.mystbin.post(data["stdout"], syntax="text")).url
                    description += f"\n\n [View output]({output})"
                embed = discord.Embed(title="Process terminated",
                                      description=description,
                                      color=discord.Color.red())
                embed.set_footer(text=f"{data['language'].title()} v{data['version']}")
                await loading_message.edit(embed=embed)

    @run.error
    async def run_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
            await ctx.send("No code provided")


def setup(client):
    client.add_cog(ProgrammingCommands(client))