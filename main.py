import discord
from discord.ext import commands
import os
from decouple import config

print("---> BOT is waking up\n")

intents = discord.Intents.default()
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix=["S.", "s."], case_insensitive=True, intents=intents)
bot.remove_command("help")


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
    print("\n---> BOT is awake\n")


token = config("Token")
bot.run(token)
