import discord
from discord.ext import commands
from discord import ui, Interaction, ButtonStyle


class SettingsViewDropdown(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Theme",
                description="Edit your default color theme, light, dark, or a custom color."
            )
        ]
        super().__init__(placeholder='Select a setting to view or change', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: Interaction):
        selected_page = self.values[0]
        await self.view.select_page(selected_page)


class SettingsView(ui.View):

    def __init__(self):
        super().__init__(timeout=300)
        self.ctx = None
        self.client = None
        self.message = None
        self.selected_page = "Home Page"

        self.clear_items()
        self.dropdown = SettingsViewDropdown()
        self.add_item(self.dropdown)

    @ui.button(label="\u2001\u2001\u2001Edit Theme\u2001\u2001\u2001", style=ButtonStyle.gray)
    async def theme_page_edit_button(self, button: ui.Button, interaction: Interaction):
        await self.ctx.send("What do you want to change your theme to?")

    @ui.button(label="Return Home", row=4, style=ButtonStyle.gray)
    async def return_home_button(self, button: ui.Button, interaction: Interaction):
        self.clear_items()
        self.add_item(self.dropdown)
        embed = discord.Embed(
            color=0x2f3136,
            description="View or change your settings for soosBot."
        )
        embed.set_author(
            icon_url="https://cdn.discordapp.com/attachments/834509971315621899/911053616708735016/settings.png",
            name="soosBot Settings - Home"
        )
        await self.message.edit(embed=embed, view=self)

    async def start(self, client, ctx):
        self.ctx = ctx
        self.client = client

        embed = discord.Embed(
            color=0x2f3136,
            description="View or change your settings for soosBot."
        )
        embed.set_author(
            icon_url="https://cdn.discordapp.com/attachments/834509971315621899/911053616708735016/settings.png",
            name="soosBot Settings - Home"
        )
        self.message = await ctx.message.reply(embed=embed, view=self)

    async def select_page(self, page):
        self.add_item(self.return_home_button)
        self.remove_item(self.dropdown)

        if page == "Theme":
            theme_color = await self.client.get_users_theme_color(self.ctx.author.id)
            string_theme_color = str(theme_color)
            if string_theme_color == "#2f3136":
                string_theme_color = "Dark Mode"
            self.add_item(self.theme_page_edit_button)
            embed = discord.Embed(color=theme_color, description=f"Theme: **`{string_theme_color}`**")
            embed.set_author(
                name="Theme",
                icon_url="https://cdn.discordapp.com"
                         "/attachments/834509971315621899/911364492808564736/icons8-paint-brush-64.png"
            )

            if string_theme_color != "Dark Mode" and string_theme_color != "Light Mode":
                embed.set_image(url=f"https://singlecolorimage.com/get/{string_theme_color.replace('#', '')}/400x100")
            await self.message.edit(
                embed=embed,
                view=self
            )


class UserCommands(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def profile(self, ctx):
        await ctx.send("Hello, World!")

    @commands.command(aliases=["setting"])
    async def settings(self, ctx):
        await SettingsView().start(self.client, ctx)


def setup(client):
    client.add_cog(UserCommands(client))
