import asyncio
import discord
from discord.ext import commands, tasks
import aiosqlite
from datetime import datetime
import datetime as dt
from .utilities.time_formats import UserFriendlyTime
import humanize


class RemindCommands(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.current_timer = None
        client.loop.create_task(self.load_reminders())

    @tasks.loop(count=1)
    async def sleeper(self, seconds):
        timer = self.current_timer
        await asyncio.sleep(seconds)
        await self.send_reminder(timer[0], timer[1], timer[2], timer[3], timer[4], timer[5])
        cursor = await self.client.database.cursor()
        await cursor.execute(
            "DELETE FROM REMINDERS WHERE user_id = ? "
            "AND channel_id = ? AND message_id = ? AND date = ? and reminder = ? and users_current_time =?",
            (
                timer[0],
                timer[1],
                timer[2],
                timer[3],
                timer[4],
                timer[5]
            )
        )
        self.current_timer = None
        await self.client.database.commit()
        await self.load_reminders()

    async def load_reminders(self):
        cursor = await self.client.database.cursor()

        try:
            await cursor.execute("SELECT * FROM REMINDERS")
            reminders = await cursor.fetchall()
            shortest_timer = None
            for reminder in reminders:
                # Last bug
                if (datetime.fromisoformat(reminder[3]) - datetime.utcnow().replace(tzinfo=None)).total_seconds() <= 0:
                    await cursor.execute(
                        "DELETE FROM REMINDERS WHERE user_id = ? "
                        "AND channel_id = ? AND message_id = ? AND "
                        "date = ? and reminder = ? and users_current_time = ?",
                        (
                            reminder[0],
                            reminder[1],
                            reminder[2],
                            reminder[3],
                            reminder[4],
                            reminder[5]
                        )
                    )
                    await self.client.database.commit()
                    await self.send_reminder(reminder[0], reminder[1], reminder[2],
                                             reminder[3], reminder[4], reminder[5],
                                             passed=True)
                elif not shortest_timer:
                    shortest_timer = reminder
                else:
                    if datetime.fromisoformat(reminder[3]) - datetime.utcnow() < \
                            datetime.fromisoformat(shortest_timer[3]) - datetime.utcnow():  # Multiline conditional
                        shortest_timer = reminder
            if shortest_timer:
                if self.sleeper.is_running():
                    self.sleeper.restart(
                        seconds=(datetime.fromisoformat(shortest_timer[3]) - datetime.utcnow()).total_seconds())
                else:
                    self.sleeper.start(
                        seconds=(datetime.fromisoformat(shortest_timer[3]) - datetime.utcnow()).total_seconds())
                self.current_timer = shortest_timer
        except aiosqlite.OperationalError:
            await cursor.execute("CREATE TABLE REMINDERS "
                                 "(user_id integer, channel_id integer, message_id integer, "
                                 "date text, reminder text, users_current_time text)")
            await self.client.database.commit()

    async def add_reminder(self, user_id, channel_id, message_id, date, reminder, users_current_time):
        cursor = await self.client.database.cursor()
        await cursor.execute(
            "INSERT INTO REMINDERS VALUES (?, ?, ?, ?, ?, ?)",
            (
                user_id,
                channel_id,
                message_id,
                str(date),
                reminder,
                str(users_current_time)
            )
        )
        await self.client.database.commit()

        # Check if the reminder is shorter than the current one.
        if self.current_timer and datetime.fromisoformat(self.current_timer[3]) > date:
            self.current_timer = None
            await self.load_reminders()
        else:
            if not self.current_timer:
                await self.load_reminders()

    async def send_reminder(self, user_id, channel_id, message_id, date, reason, users_current_time, *, passed=False):
        channel = await self.client.fetch_channel(channel_id)
        user = await self.client.fetch_user(user_id)
        date = datetime.fromisoformat(date)
        try:
            message = await channel.fetch_message(message_id)
        except discord.errors.NotFound:
            message = None
        users_current_time = datetime.fromisoformat(users_current_time)
        seconds = (datetime.utcnow() - date).total_seconds()
        time = discord.utils.format_dt(users_current_time + dt.timedelta(0, seconds), style="R")
        if not passed:
            if reason == "None":
                embed = discord.Embed(title="Reminder",
                                      description=f"You asked me to remind you {time}",
                                      color=await self.client.get_users_theme_color(user.id))
            else:
                embed = discord.Embed(title="Reminder",
                                      description=f"`{reason.title()}`",
                                      color=await self.client.get_users_theme_color(user.id))

        else:
            if reason == "None":
                embed = discord.Embed(title="Reminder",
                                      description=f"You asked me to remind you {time}\n\n"
                                                  f"*This reminder was sent late because soosBot was offline. "
                                                  f"[Learn more.](https://soosbot.com)*",
                                      color=discord.Color.red())
            else:
                embed = discord.Embed(title="Reminder",
                                      description=f"`{reason.title()}`\n\n"
                                                  f"*This reminder was sent late because soosBot was offline. "
                                                  f"[Learn more.](https://soosbot.com)*",
                                      color=discord.Color.red())

        if message:
            await message.reply(embed=embed)
        else:
            await channel.send(user.mention, embed=embed)

    @commands.command()
    async def remind(self, ctx, *, reminder: UserFriendlyTime(commands.clean_content, default="None")):
        await self.add_reminder(
            ctx.author.id,
            ctx.channel.id,
            ctx.message.id,
            reminder.dt,
            reminder.arg,
            ctx.message.created_at
        )
        seconds = (reminder.dt - datetime.utcnow()).total_seconds()
        time = discord.utils.format_dt(ctx.message.created_at + dt.timedelta(0, seconds), style="R")
        if reminder.arg == "None":
            embed = discord.Embed(title="Reminder",
                                  description=f"Alright! I'll remind you {time}",
                                  color=await self.client.get_users_theme_color(ctx.author.id))
        else:
            embed = discord.Embed(title="Reminder",
                                  description=f"\n``{reminder.arg.title()}``  {time}",
                                  color=await self.client.get_users_theme_color(ctx.author.id))
        await ctx.message.reply(embed=embed)

    @remind.error
    async def remind_error(self, ctx, error):
        await ctx.message.reply(embed=discord.Embed(
            title=error,
            color=discord.Color.red()
        ))


def setup(client):
    client.add_cog(RemindCommands(client))
