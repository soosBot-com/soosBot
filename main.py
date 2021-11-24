from utilities import loader
from soosbot import soosBot

# This import is for development purposes only.
from cogwatch import Watcher

client = soosBot()
client.loaded = False


@client.event
async def on_ready():
    reloaded = "re" if client.loaded else ""
    print(f"{client.user} {reloaded}loaded,"
          f" with {len(client.commands)} command(s),"
          f" {len(client.guilds)} guild(s),"
          f" and {sum([x.member_count for x in client.guilds])} user(s).")
    client.loaded = True

    # This code is for development purposes.
    # It is used for hot reloading cogs while edits occur.

    watcher = Watcher(client, path="extensions", preload=False)
    await watcher.start()


def main():
    config = loader.load_json("configuration.json")
    client.run(config["tokens"]["soosBot-BETA"])


if __name__ == "__main__":
    main()
