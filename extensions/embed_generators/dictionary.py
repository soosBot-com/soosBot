import discord


async def generate_dictionary_embeds(client, ctx, word) -> list[discord.Embed]:
    word_information = await client.requests(f"https://api.dictionaryapi.dev/api/v2/entries/en_US/{word}", cache=True)
    if isinstance(word_information, dict):
        return []
    embeds = []
    sayings = ""
    for saying in word_information[0]["phonetics"]:
        link = saying.get('audio', None)
        if link:
            if not link.startswith("https://"):
                if link.startswith("//"):
                    link = "https://" + link[2:]
                else:
                    link = "https://" + link
        sayings += f"**[{saying['text']}]({link} \"Click to view audio\")**\n"

    sayings = sayings[:-1]
    for i in range(len(word_information[0]['meanings'])):
        embed = discord.Embed(
            title=f"{word.title()} [{word_information[0]['meanings'][i]['partOfSpeech'].title()}]",
            color=await client.get_users_theme_color(ctx.author.id)).set_author(name="Dictionary")
        description = sayings
        description += "\n** **\n"

        for definition in word_information[0]['meanings'][i]['definitions']:
            description += f"**`{word_information[0]['meanings'][i]['definitions'].index(definition) + 1}`**\n" \
                           f"**Definition**\n{definition['definition']}\n "
            try:
                if definition["synonyms"]:
                    description += "**Synonyms**\n"
                    for synonym in definition["synonyms"]:
                        description += f"{synonym.title()}, "
            except KeyError:
                pass
            description = description[:-2]
            try:
                if definition["example"]:
                    description += f"\n**Example**\n{definition['example'].capitalize()}."
            except KeyError:
                pass
            description += "\n** **\n"
        description = description[:-7]
        embed.description = description
        embeds.append(embed)
    return embeds
