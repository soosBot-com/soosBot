import discord


async def generate_wikipedia_embeds(client, ctx, query) -> list[discord.Embed]:
    response = await client.aiohttp_session.get(
        "http://en.wikipedia.org/w/api.php",
        params={
            'list': 'search',
            'srprop': '',
            'srlimit': 1,
            'srsearch': query,
            'format': 'json',
            'action': 'query'
        },
        headers={
            "User-Agent": "soosBot"
        }
    )

    data = await response.json()
    try:
        query = data["query"]["search"][0]["title"]
    except (KeyError, IndexError):
        return []
    page = data["query"]["search"][0]["pageid"]

    # Getting page data.
    response = await client.aiohttp_session.get(
        "http://en.wikipedia.org/w/api.php",
        params={
            'prop': 'extracts',
            'explaintext': '',
            'titles': query,
            'format': 'json',
            'action': 'query'
        },
        headers={
            "User-Agent": "soosBot"
        }
    )

    data = await response.json()
    extract = data["query"]["pages"][str(page)]["extract"]
    if len(extract) > 1000:
        extract = extract[:997] + "..."

    return [
        discord.Embed(
            title=query,
            description=extract,
            color=await client.get_users_theme_color(ctx.author.id),
            url=f"https://en.wikipedia.org/wiki/{query}"
        )
    ]