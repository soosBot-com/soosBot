from discord.ext import commands
from discord import ui, PartialEmoji, Interaction
import discord
from .embed_generators.dictionary import generate_dictionary_embeds
from .embed_generators.urban_dictionary import generate_urban_dictionary_embeds
from .embed_generators.wikipedia import generate_wikipedia_embeds
from .embed_generators.google import generate_google_embeds
from .embed_generators.shows_and_movies import generate_show_or_movie_embeds


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
            description="Search Urban Dictionary for your query",
            emoji=PartialEmoji(name="urbandictionary", id=913062115336667226),
            default=True if default == "urban dictionary" else False
        ),
        discord.SelectOption(
            label="Wikipedia",
            description="Search Wikipedia for your query",
            emoji=PartialEmoji(name="wikipedia", id=913073692249047080),
            default=True if default == "wikipedia" else False
        ),
        discord.SelectOption(
            label="Google",
            description="Search Google for your query",
            emoji=PartialEmoji(name="google", id=913400557199323186),
            default=True if default == "google" else False
        ),
        discord.SelectOption(
            label="TV Show",
            description="Search for TV Shows related to your query",
            emoji=PartialEmoji(name="tv show", id=913421080348217384),
            default=True if default == "tv show" else False
        ),
        discord.SelectOption(
            label="Movie",
            description="Search for Movies related to your query",
            emoji=PartialEmoji(name="e0468", id=913442131392217098),
            default=True if default == "movie" else False
        )
    ]


class SettingsViewDropdown(ui.Select):
    def __init__(self, default: str):
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

        self.cache = {
            "urban dictionary": [],
            "dictionary": [],
            "wikipedia": [],
            "google": [],
            "tv show": [],
            "movie": []
        }
        super().__init__(timeout=70)

    async def on_timeout(self) -> None:
        self.clear_items()
        self.dropdown.placeholder = "Timed out"
        self.dropdown.disabled = True
        self.dropdown.options = generate_options("")  # So the dropdown placeholder is visible
        self.add_item(self.dropdown)
        await self.message.edit(view=self)
        self.stop()

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

        if query_type == "google":
            return await self.google_page()

        if query_type == "tv show":
            return await self.tv_show_page()

        if query_type == "movie":
            return await self.tv_show_page()

        # Here, query_type isn't provided, so we should select the best one possible to fit the query.

        # Hierarchy : Urban Dictionary > Dictionary > Google > Wikipedia > TV Show > Movie

        # TODO: Make hierarchy depend on something other than no results found,
        #  like looking at the volume of data/embeds.

        self.cache["urban dictionary"] = await generate_urban_dictionary_embeds(self.client, self.ctx, self.query)

        if len(self.cache["urban dictionary"]) != 0:
            self.dropdown.options = generate_options("urban dictionary")
            return await self.urban_dictionary_page()

        self.cache["dictionary"] = await generate_dictionary_embeds(self.client, self.ctx, self.query)

        if len(self.cache["dictionary"]) != 0:
            self.dropdown.options = generate_options("urban dictionary")
            return await self.dictionary_page()

        self.cache["google"] = await generate_google_embeds(self.client, self.ctx, self.query)

        if len(self.cache["google"]) != 0:
            self.dropdown.options = generate_options("google")
            return await self.google_page()

        self.cache["wikipedia"] = await generate_wikipedia_embeds(self.client, self.ctx, self.query)

        if len(self.cache["wikipedia"]) != 0:
            self.dropdown.options = generate_options("urban dictionary")
            return await self.wikipedia_page()

        self.cache["tv show"] = await generate_show_or_movie_embeds(self.client, self.ctx, self.query, "tv")

        if len(self.cache["tv show"]) != 0:
            self.dropdown.options = generate_options("tv show")
            return await self.tv_show_page()

        self.cache["movie"] = await generate_show_or_movie_embeds(self.client, self.ctx, self.query, "movie")

        if len(self.cache["movie"]) != 0:
            self.dropdown.options = generate_options("movie")
            return await self.movie_page()

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
        if self.cache["dictionary"]:
            self.paginator_embeds = self.cache["dictionary"]
        else:
            self.cache["dictionary"] = await generate_dictionary_embeds(self.client, self.ctx, self.query)
            if len(self.cache["dictionary"]) == 0:
                self.cache["dictionary"] = [
                    discord.Embed(
                        title="No results found",
                        color=await self.client.get_users_theme_color(self.ctx.author.id),
                    ).set_author(name="Dictionary")
                ]
            self.paginator_embeds = self.cache["dictionary"]
        await self.start_paginator()

    async def urban_dictionary_page(self):
        if self.cache["urban dictionary"]:
            self.paginator_embeds = self.cache["urban dictionary"]
        else:
            self.cache["urban dictionary"] = await generate_urban_dictionary_embeds(self.client, self.ctx, self.query)
            if len(self.cache["urban dictionary"]) == 0:
                self.cache["urban dictionary"] = [
                    discord.Embed(
                        title="No results found",
                        color=await self.client.get_users_theme_color(self.ctx.author.id),
                    ).set_author(name="Urban Dictionary")
                ]
            self.paginator_embeds = self.cache["urban dictionary"]
        await self.start_paginator()

    async def wikipedia_page(self):
        if self.cache["wikipedia"]:
            self.paginator_embeds = self.cache["wikipedia"]
        else:
            self.cache["wikipedia"] = await generate_wikipedia_embeds(self.client, self.ctx, self.query)
            if len(self.cache["wikipedia"]) == 0:
                self.cache["wikipedia"] = [
                    discord.Embed(
                        title="No results found",
                        color=await self.client.get_users_theme_color(self.ctx.author.id),
                    ).set_author(name="Wikipedia")
                ]
            self.paginator_embeds = self.cache["wikipedia"]
        await self.start_paginator()

    async def google_page(self):
        if self.cache["google"]:
            self.paginator_embeds = self.cache["google"]
        else:
            self.cache["google"] = await generate_google_embeds(self.client, self.ctx, self.query)
            if len(self.cache["google"]) == 0:
                self.cache["google"] = [
                    discord.Embed(
                        title="No results found",
                        color=await self.client.get_users_theme_color(self.ctx.author.id),
                    ).set_author(name="Wikipedia")
                ]
            self.paginator_embeds = self.cache["google"]
        await self.start_paginator()

    async def tv_show_page(self):
        if self.cache["tv show"]:
            self.paginator_embeds = self.cache["tv show"]
        else:
            self.cache["tv show"] = await generate_show_or_movie_embeds(self.client, self.ctx, self.query, "tv")
            if len(self.cache["tv show"]) == 0:
                self.cache["tv show"] = [
                    discord.Embed(
                        title="No results found",
                        color=await self.client.get_users_theme_color(self.ctx.author.id),
                    ).set_author(name="TV Show")
                ]
            self.paginator_embeds = self.cache["tv show"]
        await self.start_paginator()

    async def movie_page(self):
        if self.cache["movie"]:
            self.paginator_embeds = self.cache["movie"]
        else:
            self.cache["movie"] = await generate_show_or_movie_embeds(self.client, self.ctx, self.query, "movie")
            if len(self.cache["movie"]) == 0:
                self.cache["movie"] = [
                    discord.Embed(
                        title="No results found",
                        color=await self.client.get_users_theme_color(self.ctx.author.id),
                    ).set_author(name="Movie")
                ]
            self.paginator_embeds = self.cache["movie"]
        await self.start_paginator()


class SearchCommands(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(slash_command=True)
    async def search(self, ctx, *, query=commands.Option(description="Your search query!")):
        """
        Search for a query!
        """
        await SearchView().start(self.client, ctx, query)

    @commands.command(slash_command=True)
    async def google(self, *, ctx, query=commands.Option(description="Your search query!")):
        """
        Search for a query!
        """
        await SearchView().start(self.client, ctx, query)

    @commands.command(slash_command=True)
    async def tv(self, ctx, *, query=commands.Option(description="Your search query!")):
        """
        Search for a query!
        """
        await SearchView().start(self.client, ctx, query, query_type="tv show")

    @commands.command(slash_command=True)
    async def movie(self, ctx, *, query=commands.Option(description="Your search query!")):
        """
        Search for a query!
        """
        await SearchView().start(self.client, ctx, query, query_type="movie")

    @commands.command(slash_command=True)
    async def define(self, ctx, *, query=commands.Option(description="Your search query!")):
        """
        Search for a query!
        """
        await SearchView().start(self.client, ctx, query, query_type="dictionary")

    @commands.command(slash_command=True)
    async def urban(self, ctx, *, query=commands.Option(description="Your search query!")):
        """
        Search for a query!
        """
        await SearchView().start(self.client, ctx, query, query_type="urban dictionary")

    @commands.command(slash_command=True, aliases=["wikipedia"])
    async def wiki(self, ctx, *, query=commands.Option(description="Your search query!")):
        """
        Search for a query!
        """
        await SearchView().start(self.client, ctx, query, query_type="wikipedia")


def setup(client):
    client.add_cog(SearchCommands(client))
