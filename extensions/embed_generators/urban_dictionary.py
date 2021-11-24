import re
import discord


def cleanup_definition(definition):
    bracketed = re.compile(r"(\[(.+?)])")

    def hyperlink(m):
        word = m.group(2)
        return f'[{word}](http://{word.replace(" ", "-")}.urbanup.com)'

    ret = bracketed.sub(hyperlink, definition)
    return ret


async def generate_urban_dictionary_embeds(client, ctx, word):
    url = "https://mashape-community-urban-dictionary.p.rapidapi.com/define"
    querystring = {"term": word}
    headers = {
        'x-rapidapi-key': client.rapid_api_key,
        'x-rapidapi-host': "mashape-community-urban-dictionary.p.rapidapi.com"
    }
    response = await client.aiohttp_session.get(url, headers=headers, params=querystring)
    word_information = await response.json()
    embeds = []
    for i in range(len(word_information["list"])):
        definition = word_information['list'][i]['definition']
        likes = word_information['list'][i]['thumbs_up']
        dislikes = word_information['list'][i]['thumbs_down']
        author = word_information['list'][i]['author']
        definition = cleanup_definition(definition)
        if len(definition) > 1000:
            definition = definition[:997] + "..."
        em = discord.Embed(title="Urban Dictionary", color=await client.get_users_theme_color(ctx.author.id))
        if ctx.guild.id == 681882711945641997:
            pass
            # em.description = f"**Definition of {await client.censor_text(word)}**\n" \
            #                  f"{await client.censor_text(definition)}"
            # em.add_field(name="** **", value=f":thumbsup: {likes} :thumbsdown: {dislikes} • {author}")
            # em.set_footer(text=f"Page {i + 1}/{len(word_information['list'])}")
        else:
            em.description = f"**Definition of {word}**\n{definition}"
            em.add_field(name=f"** **", value=f":thumbsup: {likes} :thumbsdown: {dislikes} • {author}")
        embeds.append(em)
    return embeds
