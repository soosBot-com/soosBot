from discord.ext import commands
from discord import ui, PartialEmoji, Interaction
import discord
from .embed_generators.dictionary import generate_dictionary_embeds
from .embed_generators.urban_dictionary import generate_urban_dictionary_embeds
from .embed_generators.wikipedia import generate_wikipedia_embeds


def generate_options(default: str) -> list[discord.SelectOption]:
    return [
        discord.SelectOption(
            label="Dictionary",
            description="Search a dictionary for your query",
            emoji=PartialEmoji(name="dictionary", id=913037246737842216),
            default=True if default == "dictionary" else False
        ),
        discord.SelectOption(
            label="Urban Dictionary",
            description="Search a urban dictionary for your query",
            emoji=PartialEmoji(name="urbandictionary", id=913062115336667226),
            default=True if default == "urban dictionary" else False
        ),
        discord.SelectOption(
            label="Wikipedia",
            description="Search Wikipedia for your query",
            emoji=PartialEmoji(name="wikipedia", id=913073692249047080),
            default=True if default == "wikipedia" else False
        )
    ]


class SettingsViewDropdown(ui.Select):
    def __init__(self, default: dict):
        self.default = default
        super().__init__(
            placeholder='Select another place to search...',
            min_values=1,
            max_values=1,
            options=generate_options(default)
        )

    async def callback(self, interaction: Interaction):
        if interaction.user != self.view.ctx.author:
            embed = discord.Embed(description="You cannot control this command because you did not execute it.",
                                  color=discord.Colour.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        selected_page = self.values[0]

        self.view.paginator_current_page = None
        self.view.paginator_embeds = None
        self.options = generate_options(selected_page.lower())
        await getattr(self.view, selected_page.lower().replace(" ", "_") + "_page")()


class SearchView(ui.View):
    def __init__(self):
        self.client = None
        self.ctx = None
        self.query = None
        self.query_type = None
        self.paginator_embeds = None
        self.paginator_current_page = None
        self.PageCounterButton = None
        self.message = None
        self.dropdown = None

        # TODO COMBINE THESE INTO DICT
        self.cached_urban_embeds = []
        self.cached_dictionary_embeds = []
        self.cached_wikipedia_embeds = []
        super().__init__(timeout=70)

    async def on_timeout(self) -> None:
        self.clear_items()
        self.dropdown.placeholder = "Timed out"
        self.dropdown.disabled = True
        self.dropdown.options = generate_options("")  # So the dropdown placeholder is visible
        self.add_item(self.dropdown)
        await self.message.edit(view=self)

    async def start(self, client, ctx, query, *, query_type=None):
        self.client = client
        self.ctx = ctx
        self.query_type = query_type
        self.query = query

        self.dropdown = SettingsViewDropdown(query_type)

        self.add_item(self.dropdown)

        if query_type == "dictionary":
            return await self.dictionary_page()

        if query_type == "urban dictionary":
            return await self.urban_dictionary_page()

        if query_type == "wikipedia":
            return await self.wikipedia_page()

        # Here, query_type isn't provided, so we should select the best one possible to fit the query.

        # Hierarchy : Urban Dictionary > Dictionary > Wikipedia

        # TODO: Make hierarchy depend on something other than no results found,
        #  like looking at the volume of data/embeds.

        self.cached_urban_embeds = await generate_urban_dictionary_embeds(self.client, self.ctx, self.query)

        if len(self.cached_urban_embeds) != 0:
            self.dropdown.options = generate_options("urban dictionary")
            return await self.urban_dictionary_page()

        self.cached_dictionary_embeds = await generate_dictionary_embeds(self.client, self.ctx, self.query)

        if len(self.cached_dictionary_embeds) != 0:
            self.dropdown.options = generate_options("urban dictionary")
            return await self.dictionary_page()

        self.cached_wikipedia_embeds = await generate_wikipedia_embeds(self.client, self.ctx, self.query)

        if len(self.cached_wikipedia_embeds) != 0:
            self.dropdown.options = generate_options("urban dictionary")
            return await self.wikipedia_page()

        # Here, there are no results.

        await ctx.message.reply(embed=discord.Embed(
            title="No results found.",
            color=await self.client.get_users_theme_color(self.ctx.author.id)
        ))

    @ui.button(emoji=discord.PartialEmoji(name="soosBot_back", id=795306327425155082))
    async def previous(self, button: ui.Button, interaction: Interaction):
        if interaction.user != self.ctx.author:
            embed = discord.Embed(description="You cannot control this command because you did not execute it.",
                                  color=discord.Colour.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        if self.paginator_current_page == 0:
            embed = self.paginator_embeds[-1]
            self.paginator_current_page = len(self.paginator_embeds) - 1
        else:
            embed = self.paginator_embeds[self.paginator_current_page - 1]
            self.paginator_current_page -= 1

        self.page_counter.label = f"{self.paginator_current_page + 1}/{len(self.paginator_embeds)}"
        await self.message.edit(embed=embed, view=self)

    @ui.button(label=f"...", disabled=True)
    async def page_counter(self, button: ui.Button, interaction: Interaction):
        await Interaction.response.defer()
        pass

    @ui.button(emoji=discord.PartialEmoji(name="soosBot_forward", id=795309161054470144))
    async def forward(self, button: ui.Button, interaction: Interaction):
        if interaction.user != self.ctx.author:
            embed = discord.Embed(description="You cannot control this command because you did not execute it.",
                                  color=discord.Colour.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        if self.paginator_current_page == len(self.paginator_embeds) - 1:
            self.paginator_current_page = 0
            embed = self.paginator_embeds[self.paginator_current_page]
        else:
            self.paginator_current_page += 1
            embed = self.paginator_embeds[self.paginator_current_page]

        self.page_counter.label = f"{self.paginator_current_page + 1}/{len(self.paginator_embeds)}"
        await self.message.edit(embed=embed, view=self)

    async def start_paginator(self):
        if len(self.paginator_embeds) > 1:
            self.clear_items()
            self.add_item(self.dropdown)
            self.add_item(self.previous)
            self.add_item(self.page_counter)
            self.add_item(self.forward)
            self.paginator_current_page = 0
            self.page_counter.label = f"{self.paginator_current_page + 1}/{len(self.paginator_embeds)}"
            if self.message:
                await self.message.edit(embed=self.paginator_embeds[self.paginator_current_page], view=self)
            else:
                self.message = await self.ctx.send(embed=self.paginator_embeds[self.paginator_current_page], view=self)
        else:
            self.clear_items()
            self.add_item(self.dropdown)
            if self.message:
                await self.message.edit(embed=self.paginator_embeds[0], view=self)
            else:
                self.message = await self.ctx.send(embed=self.paginator_embeds[0], view=self)

    async def dictionary_page(self):
        if self.cached_dictionary_embeds:
            self.paginator_embeds = self.cached_dictionary_embeds
        else:
            self.cached_dictionary_embeds = await generate_dictionary_embeds(self.client, self.ctx, self.query)
            if len(self.cached_dictionary_embeds) == 0:
                self.cached_dictionary_embeds = [
                    discord.Embed(
                        title="No results found",
                        color=await self.client.get_users_theme_color(self.ctx.author.id),
                    ).set_author(name="Dictionary")
                ]
            self.paginator_embeds = self.cached_dictionary_embeds
        await self.start_paginator()

    async def urban_dictionary_page(self):
        if self.cached_urban_embeds:
            self.paginator_embeds = self.cached_urban_embeds
        else:
            self.cached_urban_embeds = await generate_urban_dictionary_embeds(self.client, self.ctx, self.query)
            if len(self.cached_urban_embeds) == 0:
                self.cached_urban_embeds = [
                    discord.Embed(
                        title="No results found",
                        color=await self.client.get_users_theme_color(self.ctx.author.id),
                    ).set_author(name="Urban Dictionary")
                ]
            self.paginator_embeds = self.cached_urban_embeds
        await self.start_paginator()

    async def wikipedia_page(self):
        if self.cached_wikipedia_embeds:
            self.paginator_embeds = self.cached_wikipedia_embeds
        else:
            self.cached_wikipedia_embeds = await generate_wikipedia_embeds(self.client, self.ctx, self.query)
            if len(self.cached_wikipedia_embeds) == 0:
                self.cached_wikipedia_embeds = [
                    discord.Embed(
                        title="No results found",
                        color=await self.client.get_users_theme_color(self.ctx.author.id),
                    ).set_author(name="Wikipedia")
                ]
            self.paginator_embeds = self.cached_wikipedia_embeds
        await self.start_paginator()


class SearchCommands(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def search(self, ctx, query=None):
        if not query:
            return await ctx.message.reply("give a query???")
        await SearchView().start(self.client, ctx, query)


def setup(client):
    client.add_cog(SearchCommands(client))
