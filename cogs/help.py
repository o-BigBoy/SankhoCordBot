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
                title="",
                description="Need Help?\n<> - optional arguments\n() - needed arguments\n [] - aliases",
                color=0x006900,
            )
            h.add_field(name="__ABOUT__", value=f"\nPrefix : `S.`")
            h.add_field(
                name="__STUDY VC__",
                value=f"`studytime <@user>` [st]\n`leaderboard <d/w/m>` [lb] | d-daily, w-weekly, m-monthly",
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
