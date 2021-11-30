from googlesearch import search
import discord


async def generate_google_embeds(client, ctx, query):
    print(client.random_cache)
    if client.random_cache.get("google") and client.random_cache["google"].get(query):
        description = client.random_cache["google"][query]

    else:
        results = search(query)
        description = ""
        for result in results:
            if result.startswith("https://"):
                description += result + "\n"
        client.random_cache["google"] = {}
        client.random_cache["google"][query] = description
    return [
        discord.Embed(
            description=description,
            color=await client.get_users_theme_color(ctx.author.id)
        ).set_author(name="Google")
    ]
