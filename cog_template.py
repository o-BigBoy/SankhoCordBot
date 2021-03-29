import discord
from discord.ext import commands


class Template(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def template(self, ctx):
        # Stuff 2 send goes here
        await ctx.send("template")

    @commands.Cog.listener()
    async def on_message(self, message):
        pass


def setup(bot):
    bot.add_cog(Template(bot))
    print('---> TEMPLATE LOADED')
