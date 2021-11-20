import discord
from discord.ext import commands
from jishaku.codeblocks import codeblock_converter


class ProgrammingCommands(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def format_output(self, output: str) -> str:
        if len(output) > 40:
            return f"\n ```\n{output[0:40]}...({len(output) - 40} characters more)\n```\n" \
                   f"[View Entire Output<:image12:909262805264371782>]" \
                   f"({(await self.client.mystbin.post(output, syntax='text')).url})"
        else:
            return f"```\n{output}\n```"

    @commands.command(aliases=["compile"])
    async def run(self, ctx, *, code: codeblock_converter):
        if not code.language:
            embed = discord.Embed(title="Please provide a language to compile/execute to.", color=discord.Color.red())
            embed.set_image(url="https://media.discordapp.net/attachments/793214658194178088/909431878690422856"
                                "/Language_to_run_in.png")
            return await ctx.message.reply(embed=embed)

        if not code.content:
            embed = discord.Embed(title="Please provide a codebook to compile/execute.", color=discord.Color.red())
            embed.set_image(url="https://media.discordapp.net/attachments/793214658194178088/909431878690422856"
                                "/Language_to_run_in.png")
            return await ctx.message.reply(embed=embed)

        embed = discord.Embed(color=0x2f3136).set_author(name="Loading",
                                                         icon_url="https://media.discordapp.net/attachments"
                                                                  "/762482391599022100/829461107752042566/loading.gif")
        loading_message = await ctx.message.reply(embed=embed)

        response = await self.client.aiohttp_session.post("https://emkc.org/api/v2/piston/execute", json={
            "language": code.language,
            "files": [
                {
                    "name": "code.txt",
                    "content": code.content
                }
            ],
            "version": "*"
        })

        data = await response.json()
        data["run"]["output"] = data["run"]["output"].replace("/piston/jobs/", "/soosBot/compiler/execute/")
        data["run"]["stderr"] = data["run"]["stderr"].replace("/piston/jobs/", "/soosBot/compiler/execute/")
        data["run"]["output"] = data["run"]["output"].replace("code.txt", f"code.{code.language}")
        data["run"]["stderr"] = data["run"]["stderr"].replace("code.txt", f"code.{code.language}")
        print(await self.format_output(str(data)))

        if data["run"]["stderr"] == "" and data["run"]['signal'] != "SIGKILL":
            if data["run"]["output"] != "":
                embed = discord.Embed(title=f"{data['language'].title()} `v{data['version']}`",
                                      description=await self.format_output(data["run"]["output"]),
                                      color=0x2f3136)
                await loading_message.edit(embed=embed)
            else:
                embed = discord.Embed(title=f"{data['language'].title()} `v{data['version']}`",
                                      description=f"Your script ran without any output.",
                                      color=0x2f3136)
                await loading_message.edit(embed=embed)

        else:
            if data["run"]["stderr"] != "":
                description = f"\n```{code.language}\n{data['run']['output']}\n\n```"
                embed = discord.Embed(title="Error", description=description, color=discord.Color.red())
                embed.set_footer(text=f"{data['language'].title()} v{data['version']}")
                await loading_message.edit(embed=embed)
            else:
                description = "The program ran for too long and was terminated."
                if data["run"]["output"] != "":
                    description += await self.format_output(data["run"]["output"])
                embed = discord.Embed(title="Process terminated",
                                      description=description,
                                      color=discord.Color.red())
                embed.set_footer(text=f"{data['language'].title()} v{data['version']}")
                await loading_message.edit(embed=embed)

    @run.error
    async def run_error(self, ctx, error):
        if isinstance(error, discord.ext.commands.errors.MissingRequiredArgument):
            embed = discord.Embed(title="Please provide a codebook to compile/execute.", color=discord.Color.red())
            embed.set_image(url="https://media.discordapp.net/attachments/793214658194178088/909431878690422856"
                                "/Language_to_run_in.png")
            return await ctx.message.reply(embed=embed)
        else:
            raise error

    @commands.command(aliases=["langs"])
    async def languages(self, ctx):
        response = await self.client.aiohttp_session.get("https://emkc.org/api/v2/piston/runtimes")
        data = await response.json()
        text = ""
        try:
            # Sending empty message to author to see if we can dm them
            await ctx.author.send()
        except discord.Forbidden:
            # If theres a forbidden error we cant dm them, so we send in channel
            for languages in data:
                try:
                    text += f"**{languages['language']} v{languages['version']}**\n"
                except KeyError:
                    text += f"**{languages['language']} **\n"
            embed = discord.Embed(title="Supported programming languages", description=text,
                                  color=discord.Colour.from_rgb(32, 146, 247))
            embed.set_thumbnail(
                url="https://cdn.iconscout.com/icon/free/png-512/web-programming-2190088-1840536.png")
            await ctx.send(embed=embed)
        except discord.errors.HTTPException:
            # Otherwise, there will be a 400 error, meaning we can dm them, but we cant send empty messages.
            for languages in data:
                try:
                    lang = f"**{languages['language']} v{languages['version']}**\n aliases : "
                except KeyError:
                    lang = f"**{languages['language']} **\n aliases : "

                for aliases in languages['aliases']:
                    lang = lang + f"{aliases}, "
                lang = lang[0:-2]
                text = text + lang + "\n"
            embed = discord.Embed(title="Supported programming languages", description=text,
                                  color=discord.Colour.from_rgb(32, 146, 247))
            embed.set_thumbnail(
                url="https://cdn.iconscout.com/icon/free/png-512/web-programming-2190088-1840536.png")
            await ctx.author.send(embed=embed)
            await ctx.send(
                embed=discord.Embed(title="A list of programming languages was sent to your DMs.",
                                    color=discord.Colour.green()))


def setup(client):
    client.add_cog(ProgrammingCommands(client))
