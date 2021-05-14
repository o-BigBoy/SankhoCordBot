import discord
from discord.ext import commands
import os
from decouple import config
from datetime import datetime
from pytz import timezone

print("---> BOT is waking up\n")

intents = discord.Intents.default()
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix=["S.", "s."], case_insensitive=True, intents=intents)
bot.remove_command("help")

BOT_CHANNEL_ID = 842629324846923786


def load_cogs():
    for file in os.listdir("./cogs"):
        if file.endswith(".py") and not file.startswith("_"):
            bot.load_extension(f"cogs.{file[:-3]}")


@bot.event
async def on_ready():
    print(f"---> Logged in as : {bot.user.name} , ID : {bot.user.id}")
    print(f"---> Total Servers : {len(bot.guilds)}\n")
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name="Ankoosh <3")
    )
    load_cogs()
    channel = bot.get_channel(BOT_CHANNEL_ID)
    await channel.send(f"> BOT ONLINE AT `{datetime.now(timezone('Asia/Kolkata'))}`")
    print("\n---> BOT is awake\n")


token = config("Token")
bot.run(token)
