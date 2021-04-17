# NEW COG FOR STUDY CAFE WITH STAGE SUPPORT

import discord
from discord.ext import commands, tasks
from json import loads
import pyrebase
from decouple import config
from datetime import datetime as dt
from pytz import timezone as tz

# CHANNEL IDS
GUILD_ID = 785024897863647282
STUDY_CATEGORY_ID = 785024897863647284
STUDYING_ROLE_ID = 801096719982657556
NINJA_ROLE_ID = 785027080713797641
BOT_CHANNEL_ID = 801100961313194004  # BOT MESSAGES GO HERE
LOUNGE_VC_ID = 822865823285903380
VIDEO_VC_ID = 806098255875932170

# TIMER VARIABLES
DELETE_MESSAGES = False
DELETE_AFTER = 60  # 1 min
KICK_STALKERS_AFTER = 10  # 1.5 mins
TIMER_REFRESH_INTERVAL = 10  # study time gets updated every this mins

# FIREBASE DATABASE
firebase = pyrebase.initialize_app(loads(config("Firebase")))
db = firebase.database()


# CONVERTS MINUTES INTO HOURS,MINUTES
def mins_hours(mins: int):
    hours = int(mins / 60)
    minutes = mins % 60
    return hours, minutes


""" DATABASE TREE
MEMBER_TIME:
    <MEMBER ID>:
        TOTAL:<int>
        DAILY:<int>
        WEEKLY:<int>
        MONTHLY:<int>
        VIDEO:<int>
        STREAM:<int>
"""


def create_new_member(id_: int):
    db.child("MEMBER_TIME").child(id_).set(
        {"TOTAL": 0, "DAILY": 0, "WEEKLY": 0, "MONTHLY": 0, "STREAM": 0, "VIDEO": 0}
    )


def add_mins(id_: str, timers=("TOTAL", "DAILY", "WEEKLY", "MONTHLY")):
    member_time = db.child("MEMBER_TIME").child(id_).get().val()
    if member_time == None:
        create_new_member(id_)
        return
    for timer in timers:
        member_time[timer] = int(member_time[timer]) + TIMER_REFRESH_INTERVAL
    db.child("MEMBER_TIME").child(id_).set(member_time)


class Study(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not DELETE_MESSAGES:
            DELETE_AFTER = None
        self.GUILD = self.bot.get_guild(GUILD_ID)
        self.BOT_CHANNEL = self.GUILD.get_channel(BOT_CHANNEL_ID)
        self.NINJA_ROLE = self.GUILD.get_role(NINJA_ROLE_ID)
        self.STUDYING_ROLE = self.GUILD.get_role(STUDYING_ROLE_ID)
        self.STUDY_CATEGORY = [
            c for c in self.GUILD.categories if c.id == STUDY_CATEGORY_ID
        ][0]
        self.VIDEO_VC = self.GUILD.get_channel(VIDEO_VC_ID)
        self.LOUNGE_VC = self.GUILD.get_channel(LOUNGE_VC_ID)
        self.kick_stalkers.start()

    def get_studying(self):
        # RETURNS MEMBERS IN STUDY STAGE
        studying = []
        for vc in self.STUDY_CATEGORY.stage_channels:
            if vc.id == LOUNGE_VC_ID:
                continue
            for mem in vc.members:
                if not mem.bot:
                    studying.append((mem.id, "STAGE"))

        for vc in self.STUDY_CATEGORY.voice_channels:
            if vc.id == VIDEO_VC_ID:
                for mem in vc.members:
                    if not mem.bot:
                        studying.append((mem.id, "VIDEO"))
        return studying

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        studying = self.get_studying()

        #### WHEN SOMEONE PINGS A MEMBER IN STUDY VC ###
        for ping in message.mentions:
            if ping.id in studying:
                if message.channel == BOT_CHANNEL_ID:
                    continue
                await message.channel.send(
                    f"{message.author.mention}, **{ping}** is in **{ping.voice.channel.name}**, do not disturb them <a:AngryAwooGlitch:786456477589962772>",
                    delete_after=DELETE_AFTER,
                )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot or before.channel == after.channel:
            return
        if (
            before.channel == None
            and after.channel != None
            and after.channel.category_id == STUDY_CATEGORY_ID
            and after.channel.id != LOUNGE_VC_ID
        ):
            await member.remove_roles(self.NINJA_ROLE)
            await member.add_roles(self.STUDYING_ROLE)
            msg = f"{member.mention} joined <#{after.channel.id}> 🟢\n-> Access blocked from other channels\n"
            # CHECK IF SCREENSHARE or VIDEO IS NEEDED
            if after.channel.id == VIDEO_VC_ID:
                msg += f"-> **You have to turn on your video or share your screen**\n     or you will be moved to <#{LOUNGE_VC_ID}>"
            await self.BOT_CHANNEL.send(msg)
        elif (
            before.channel != None
            and after.channel == None
            and before.channel.category_id == STUDY_CATEGORY_ID
            and before.channel.id != LOUNGE_VC_ID
        ):
            await member.add_roles(self.NINJA_ROLE)
            await member.remove_roles(self.STUDYING_ROLE)
            await self.BOT_CHANNEL.send(
                f"{member.mention} left <#{before.channel.id}> 🔴\n-> Access granted to other channels"
            )

    @tasks.loop(seconds=KICK_STALKERS_AFTER)
    async def kick_stalkers(self):
        # MOVE MEMBERS WHO DONT HAVE VIDEO OR SCREENSHARE
        vc = self.VIDEO_VC
        for mem in vc.members:
            if not (mem.voice.self_stream or mem.voice.self_video):
                await mem.move_to(channel=self.LOUNGE_VC)
                await self.BOT_CHANNEL.send(
                    f"{mem.mention} was moved to <#{LOUNGE_VC_ID}>\n->They didnot turn on camera\n-> They didnot share their screen"
                )


def setup(bot):
    bot.add_cog(Study(bot))
    print("---> STUDY LOADED")