# NEW COG FOR STUDY CAFE WITH STAGE SUPPORT

import discord
from discord.ext import commands, tasks
from json import loads
import pyrebase
from decouple import config
from datetime import datetime
from pytz import timezone
from collections import OrderedDict

# CHANNEL IDS
GUILD_ID = 785024897863647282
STUDY_CATEGORY_ID = 785024897863647284
STUDYING_ROLE_ID = 801096719982657556
NINJA_ROLE_ID = 785027080713797641
BOT_CHANNEL_ID = 842629324846923786  # BOT MESSAGES GO HERE
CAFE_LOUNGE_ID = 801100961313194004  # PPL TALK HERE, WHY?
LOUNGE_VC_ID = 822865823285903380
VIDEO_VC_ID = 806098255875932170  # VIDEO/STREAM BOTH GO INTO VIDEO TIMER
STREAM_VC_ID = 837889538855927819  # STREAM GOES INTO STREAM
STUDY_VC_ID = 831055532759449610  # STAGE VC
STUDY_VC_NORMAL_ID = 840974183201636373  # NON STAGE VC
PRIVATE_VC_ID = 837898127222636544  # PRIVATE VC FOR STAFF AND AKATSUKI

# TIMER VARIABLES
# DELETE_MESSAGES = True
DELETE_AFTER = 75  # 1 min
KICK_STALKERS_AFTER = 90  # 1.5 min
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


### reset functions
def resetDaily():
    times = dict(db.child("MEMBER_TIME").get().val())
    for id_ in times:
        times[id_]["DAILY"] = 0
    db.child("MEMBER_TIME").set(times)
    print("reset daily")


def resetWeekly():
    times = dict(db.child("MEMBER_TIME").get().val())
    for id_ in times:
        times[id_]["WEEKLY"] = 0
    db.child("MEMBER_TIME").set(times)
    print("reset weekly")


def resetMonthly():
    times = dict(db.child("MEMBER_TIME").get().val())
    for id_ in times:
        times[id_]["MONTHLY"] = 0
    db.child("MEMBER_TIME").set(times)
    print("reset monthly")


class Study(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.GUILD = self.bot.get_guild(GUILD_ID)
        self.BOT_CHANNEL = self.GUILD.get_channel(BOT_CHANNEL_ID)
        self.NINJA_ROLE = self.GUILD.get_role(NINJA_ROLE_ID)
        self.STUDYING_ROLE = self.GUILD.get_role(STUDYING_ROLE_ID)
        self.STUDY_CATEGORY = [
            c for c in self.GUILD.categories if c.id == STUDY_CATEGORY_ID
        ][0]
        self.VIDEO_VC = self.GUILD.get_channel(VIDEO_VC_ID)
        self.STREAM_VC = self.GUILD.get_channel(STREAM_VC_ID)
        self.STUDY_VC = self.GUILD.get_channel(STUDY_VC_ID)
        self.STUDY_VC_NORMAL = self.GUILD.get_channel(STUDY_VC_NORMAL_ID)
        self.PRIVATE_VC = self.GUILD.get_channel(PRIVATE_VC_ID)
        self.LOUNGE_VC = self.GUILD.get_channel(LOUNGE_VC_ID)
        self.kick_stalkers.start()
        self.timer_refresh.start()
        self.reset.start()
        self.students_count = len(self.get_studying())
        self.message_count = {}
        self.update_count.start()

    def get_studying(self):
        # RETURNS MEMBERS IN STUDY STAGE
        studying = []

        for mem in self.STUDY_VC.members:  # NORMAL STODYING VC
            if not mem.bot:
                studying.append((mem.id, "NONE"))

        for mem in self.STUDY_VC_NORMAL.members:  # NORMAL STODYING VC
            if not mem.bot:
                studying.append((mem.id, "NONE"))

        for mem in self.PRIVATE_VC.members:
            if not mem.bot:
                if mem.voice.self_video:
                    studying.append((mem.id, "VIDEO"))
                elif mem.voice.self_stream:
                    studying.append((mem.id, "STREAM"))
                else:
                    studying.append((mem.id, "NONE"))

        for mem in self.VIDEO_VC.members:  # VC ONLY FOR VIDEO
            if mem.voice.self_video and not mem.bot:
                studying.append((mem.id, "VIDEO"))
        for mem in self.STREAM_VC.members:  # VC ONLY FOR STREAMING
            if mem.voice.self_stream and not mem.bot:
                studying.append((mem.id, "STREAM"))

        self.students_count = len(studying)
        return studying

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        studying = self.get_studying()
        studying_ids = [mem[0] for mem in studying]
        #### WHEN SOMEONE PINGS A MEMBER IN STUDY VC ###
        for ping in message.mentions:
            if str(ping.id) in str(studying):
                if str(message.channel.id) == str(CAFE_LOUNGE_ID):
                    continue
                await message.channel.send(
                    f"{message.author.mention}, **{ping}** is in **{ping.voice.channel.name}**, do not disturb them <a:AngryAwooGlitch:786456477589962772>",
                    delete_after=DELETE_AFTER,
                )

        if (
            message.author.id in self.message_count
            and message.author.id in studying_ids
        ):
            self.message_count[message.author.id] = (
                int(self.message_count[message.author.id]) + 1
            )
            if int(self.message_count[message.author.id]) >= 15:
                await message.channel.send(
                    f"{message.author.mention} You are talking too much while in study VC\nGo study baka!<a:AngryAwooGlitch:786456477589962772>",
                    delete_after=DELETE_AFTER,
                )
                self.message_count[message.author.id] = 0
        else:
            self.message_count[message.author.id] = 1

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot or (before.channel == after.channel):
            return
        if (
            before.channel == None
            and after.channel != None
            and after.channel.category_id == STUDY_CATEGORY_ID
            and after.channel.id != LOUNGE_VC_ID
        ):
            await member.remove_roles(self.NINJA_ROLE)
            await member.add_roles(self.STUDYING_ROLE)
            msg = f"{member.name} joined <#{after.channel.id}> 🟢\n-> Access blocked from other channels\n"
            # CHECK IF SCREENSHARE or VIDEO IS NEEDED
            if after.channel.id == VIDEO_VC_ID:
                msg += f"-> **You have to turn on your video**\n     or you will be moved to <#{LOUNGE_VC_ID}>"
            elif after.channel.id == STREAM_VC_ID:
                msg += f"-> **You have to share your screen**\n     or your time will not be counted"
            await self.BOT_CHANNEL.send(msg)
        elif (
            before.channel != None
            and after.channel == None
            and before.channel.category_id == STUDY_CATEGORY_ID
        ):
            await member.add_roles(self.NINJA_ROLE)
            await member.remove_roles(self.STUDYING_ROLE)
            await self.BOT_CHANNEL.send(
                f"{member.name} left <#{before.channel.id}> 🔴\n-> Access granted to other channels"
            )

    ###########################################################

    @tasks.loop(seconds=15)
    async def update_count(self):
        await self.BOT_CHANNEL.edit(name=f"studying with {self.students_count} others")

    @tasks.loop(seconds=KICK_STALKERS_AFTER)
    async def kick_stalkers(self):
        # MOVE MEMBERS WHO DONT HAVE VIDEO OR SCREENSHARE
        vc = self.VIDEO_VC
        for mem in vc.members:
            if not mem.voice.self_video:
                await mem.move_to(channel=self.LOUNGE_VC)
                print(f"moved {mem}")
                await self.BOT_CHANNEL.send(
                    f"{mem.mention} was moved to <#{LOUNGE_VC_ID}>\n->They didnot turn on video",
                    delete_after=DELETE_AFTER,
                )

    @tasks.loop(minutes=TIMER_REFRESH_INTERVAL)
    async def timer_refresh(self):
        studying = self.get_studying()
        for mem in studying:
            if mem[1] == "VIDEO":
                T = ("TOTAL", "DAILY", "WEEKLY", "MONTHLY", "VIDEO")
            elif mem[1] == "STREAM":
                T = ("TOTAL", "DAILY", "WEEKLY", "MONTHLY", "STREAM")
            else:
                T = ("TOTAL", "DAILY", "WEEKLY", "MONTHLY")
            ID = mem[0]
            add_mins(ID, T)

    # Resets leaderboards everyday.
    @tasks.loop(minutes=50)
    async def reset(self):
        now = datetime.now(timezone("Asia/Kolkata"))
        if now.hour == 0:
            resetDaily()
            await self.BOT_CHANNEL.send(
                f"> RESET DAILY LEADERBOARD AT `{datetime.now(timezone('Asia/Kolkata'))}`"
            )
            if now.weekday() == 0:
                resetWeekly()
                await self.BOT_CHANNEL.send(
                    f"> RESET WEEKLY LEADERBOARD AT `{datetime.now(timezone('Asia/Kolkata'))}`"
                )
            if now.day == 1:
                resetMonthly()
                await self.BOT_CHANNEL.send(
                    f"> RESET MONTHLY LEADERBOARD AT `{datetime.now(timezone('Asia/Kolkata'))}`"
                )

    ###########################################################

    @commands.command(aliases=["lb"])
    async def leaderboard(self, ctx, timer="TOTAL"):
        timer = timer.upper()
        lb = db.child("MEMBER_TIME").order_by_child(timer).get().val()
        lb = OrderedDict(reversed(list(lb.items())))  # REVERSE THE SORTED DICT
        desc = f""
        for mem_id in lb:
            try:
                member = await self.GUILD.fetch_member(mem_id)
            except Exception:
                member = "UNKNOWN MEMBER"
            hrs, mins = mins_hours(lb[mem_id][timer])
            position = list(lb.keys()).index(mem_id) + 1
            if position > 10:
                break
            if mem_id == str(ctx.author.id):
                desc += f"-> | {member} | {hrs} Hrs {mins} Mins <-\n"
            else:
                if position == 10:  # ONE SPACE LESSER
                    desc += f"#{position}| {member} | {hrs} Hrs {mins} Mins\n"
                else:
                    desc += f"#{position} | {member} | {hrs} Hrs {mins} Mins\n"

        mem_id = str(ctx.author.id)
        try:
            member = await self.GUILD.fetch_member(mem_id)
        except Exception:
            member = "UNKNOWN MEMBER"
        hrs, mins = mins_hours(lb[mem_id][timer])
        position = list(lb.keys()).index(mem_id) + 1

        emb = discord.Embed(
            title=f"**STUDY CAFE LEADERBOARD [{timer}]**",
            description=f"```\n{desc}\n```",
            color=0xFFFFFF,
        )
        emb.set_author(
            name="available options : TOTAL, DAILY, WEEKLY, MONTHLY, VIDEO, STREAM"
        )
        emb.set_footer(text=f"#{position} | {member} | {hrs} Hrs {mins} Mins")
        await ctx.send(embed=emb)

    @commands.command(aliases=["studytime", "st"])
    async def stats(self, ctx, user: discord.User = None):
        if user == None:
            user = ctx.author
        lb = db.child("MEMBER_TIME").child(user.id).get().val()
        times = []
        if lb != None:
            for mins in (
                lb["TOTAL"],
                lb["DAILY"],
                lb["WEEKLY"],
                lb["MONTHLY"],
                lb["VIDEO"],
                lb["STREAM"],
            ):
                times.append(mins_hours(mins))  # REMEMBER ORDER
        else:
            for _ in range(6):
                times.append((0, 0))
        total = str(times[0][0]) + " Hrs " + str(times[0][1]) + " Mins"
        daily = str(times[1][0]) + " Hrs " + str(times[1][1]) + " Mins"
        weekly = str(times[2][0]) + " Hrs " + str(times[2][1]) + " Mins"
        monthly = str(times[3][0]) + " Hrs " + str(times[3][1]) + " Mins"
        video = str(times[4][0]) + " Hrs " + str(times[4][1]) + " Mins"
        stream = str(times[5][0]) + " Hrs " + str(times[5][1]) + " Mins"

        desc = f"Total Time : {total}\nTime for today : {daily}\nTime for this Week : {weekly}\nTime for this month : {monthly}\nTotal Video Time : {video}\nTotal Stream Time : {stream}"

        emb = discord.Embed(
            title=f"STATS FOR {user}",
            description=f"```\n{desc}\n```",
            color=0xFFFFFF,
        )
        await ctx.send(embed=emb)

    @commands.command()
    async def manual_reset(self, ctx, timer=""):
        timer = timer.upper()
        if timer == "" or not timer in ("DAILY", "WEEKLY", "MONTHLY"):
            await ctx.send("DAILY | WEEKLEY | MONTHLY")
            return
        if timer == "DAILY":
            resetDaily()
        elif timer == "WEEKLY":
            resetWeekly()
        elif timer == "MONTHLY":
            resetMonthly()


def setup(bot):
    bot.add_cog(Study(bot))
    print("---> STUDY LOADED")
