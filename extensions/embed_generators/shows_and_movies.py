from googlesearch import search
import discord
from datetime import datetime


async def generate_show_or_movie_embeds(client, ctx, query, query_type):
    url = f"https://api.themoviedb.org/3/search/{query_type}?api_key={client.tmdb_api_key}&query={query}"
    if query_type == "movie":
        url += "?include_adult=false"
    data = await client.requests(
        f"https://api.themoviedb.org/3/search/{query_type}?api_key={client.tmdb_api_key}&query={query}",
        cache=True
    )

    embeds = []
    title_or_name = "title" if query_type == "movie" else "name"
    movie_or_show = "Movie" if query_type == "movie" else "TV Show"
    for result in data["results"]:

        embed = discord.Embed(title=result[title_or_name],
                              color=await client.get_users_theme_color(ctx.author.id), description=result["overview"])
        embed.set_image(url=f"https://image.tmdb.org/t/p/original{result['poster_path']}")
        try:
            embed.add_field(name=f"First aired",
                            value=discord.utils.format_dt(datetime.strptime(result['first_air_date'],
                                                                            '%Y-%m-%d'),
                                                          style="R"),
                            inline=False)
        except:
            embed.add_field(name=f"First aired", value="?")
        embed.add_field(name=f"** **", value="** **", inline=False)
        embed.add_field(name=f"Votes", value=f"🔺 `{result['vote_count']}`", inline=True)
        embed.add_field(name="Rating", value=f":star: `{result['vote_average']}`", inline=True)
        embed.set_footer(text=f"ID : {result['id']}")

        embeds.append(embed.set_author(name=movie_or_show))
    return embeds
