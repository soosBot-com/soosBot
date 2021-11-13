from utilities import loader
from soosbot import soosBot

client = soosBot()


@client.event
async def on_ready():
    await client.wait_until_ready()

    print(f"{client.user} loaded,"
          f" with {len(client.commands)} command(s),"
          f" {len(client.guilds)} guild(s),"
          f" and {sum([x.member_count for x in client.guilds])} user(s).")


def main():
    config = loader.load_json("configuration.json")
    client.run(config["tokens"]["soosBot-BETA"])


if __name__ == "__main__":
    main()
