import discord
from discord.ext import commands
from decouple import config


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        try:

            h = discord.Embed(
                title="NEED HELP?",
                description="<> - optional arguments\n() - needed arguments\n [] - aliases",
                color=0xFFFFFF,
            )
            h.add_field(name="__ABOUT__", value=f"\nPrefix : `S.`", inline=False)
            h.add_field(
                name="__STUDY VC__",
                value=f"`stats <@user>` [st, studytime]\n`leaderboard` [lb]",
                inline=False,
            )
            h.add_field(
                name="__MISC__", value="`source` source code for the bot", inline=False
            )

            await ctx.send(embed=h)
        except Exception as e:
            print(e)

    @commands.command()
    async def source(self, ctx):
        await ctx.send("https://github.com/o-BigBoy/SankhoCordBot")


def setup(bot):
    bot.add_cog(Help(bot))
    print("---> HELP LOADED")
