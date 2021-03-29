import discord
from discord.ext import commands, tasks
from json import loads
import pyrebase
from decouple import config
from datetime import datetime as dt
from pytz import timezone as tz

# CODE FOR TRACKING TIME SPENT IN STUDY VC
# AND AWARD ROLES ACCORDING TO AMOUNT OF TIME STUDIED

guild_id = 785024897863647282
study_category_id = 785024897863647284
study_role_id = 801096719982657556
ninja_role_id = 785027080713797641
study_channel_id = 801100961313194004
stream_vc = 806098255875932170  # for vcs where screenshare is mandatory
video_vc = 806098255875932170
study_lounge = 822865823285903380

# variables
message_delete_after = 60  # 1 min
stalker_kick_refresh = 90  # 1.5 mins
refresh_interval_mins = 10  # study time gets updated every this mins

Times = {
    "": "MEMBER_TIME",
    "D": "DAILY_TIME",
    "W": "WEEKLY_TIME",
    "M": "MONTHLY_TIME",
    "V": "VIDEO",
    "S": "STREAM",
}

firebase = pyrebase.initialize_app(loads(config("Firebase")))
db = firebase.database()


def mins_hours(mins: int):
    hours = int(mins / 60)
    minutes = mins % 60
    return hours, minutes


def add_mins(id_: int, vc: str):
    # print(id_)
    for TIME in ("MEMBER_TIME", "DAILY_TIME", "WEEKLY_TIME", "MONTHLY_TIME"):
        data = db.child(TIME).child(id_).get().val()
        if data == None:
            db.child(TIME).child(id_).child("MINUTES").set(refresh_interval_mins)
        else:
            db.child(TIME).child(id_).child("MINUTES").set(
                data["MINUTES"] + refresh_interval_mins
            )

    if vc == "VIDEO":
        data = db.child("VIDEO").child(id_).get().val()
        if data == None:
            db.child("VIDEO").child(id_).child("MINUTES").set(refresh_interval_mins)
        else:
            db.child("VIDEO").child(id_).child("MINUTES").set(
                data["MINUTES"] + refresh_interval_mins
            )

    elif vc == "STREAM":
        data = db.child("STREAM").child(id_).get().val()
        if data == None:
            db.child("STREAM").child(id_).child("MINUTES").set(refresh_interval_mins)
        else:
            db.child("STREAM").child(id_).child("MINUTES").set(
                data["MINUTES"] + refresh_interval_mins
            )


class Study(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hmm.start()
        self.lb_reset.start()
        self.kick_stalkers.start()
        self.message_count = {}
        self.stalker_ids = set({})

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            return

        guild = self.bot.get_guild(guild_id)
        study_category = [c for c in guild.categories if c.id == study_category_id][0]

        #### FOR GETTING MEMBERS(ID) IN STUDY VCs #####
        members_studying = []
        for vc in study_category.voice_channels:
            if vc.id == study_lounge:
                continue
            for mem in vc.members:
                if not mem.bot:
                    members_studying.append(mem.id)

        #### UPDATING MESSAGES SENT BY MEMBERS IN STUUDY VC ####
        if message.author.id in members_studying:
            if message.author.id in self.message_count:
                self.message_count[message.author.id] += 1
                if self.message_count[message.author.id] >= 10:
                    self.message_count[message.author.id] = 0
                    await message.channel.send(
                        f"{message.author.mention} you are chatting too much while being connected to **{message.author.voice.channel.name}** 😠",
                        delete_after=message_delete_after,
                    )
            else:
                self.message_count[message.author.id] = 1

        #### WHEN SOMEONE PINGS A MEMBER IN STUDY VC ###
        for ping in message.mentions:
            if ping.id in members_studying:
                await message.channel.send(
                    f"{message.author.mention}, **{ping}** is in **{ping.voice.channel.name}**, do not disturb them 😠",
                    delete_after=message_delete_after,
                )

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        guild = self.bot.get_guild(guild_id)
        channel = guild.get_channel(study_channel_id)
        ninja = guild.get_role(ninja_role_id)
        studying = guild.get_role(study_role_id)

        if before.channel == None and after.channel != None:
            if (
                after.channel.category_id == study_category_id
            ):  # when someone joins a study vc
                await member.add_roles(studying)
                await member.remove_roles(ninja)
                await channel.send(
                    f"{member.mention} I restricted your access to distracting channels because you joined **{after.channel}**\nHappy Studying 😄",
                    delete_after=message_delete_after,
                )

        elif before.channel != None and after.channel == None:
            if (
                before.channel.category_id == study_category_id
            ):  # when someone leaves a study vc
                await member.add_roles(ninja)
                await member.remove_roles(studying)
                await channel.send(
                    f"**{member}** has left **{before.channel}**",
                    delete_after=message_delete_after,
                )

        # CHECK IF SCREENSHARE or VIDEO IS NEEDED
        if after.channel != None:
            if after.channel.id == stream_vc or after.channel.id == video_vc:
                if not after.self_stream or after.self_video:
                    await channel.send(
                        f"{member.mention} You have joined **{after.channel}** where video or screensharing is mandatory, if you dont turn on video or screenshare you will be removed from the VC!",
                        delete_after=message_delete_after,
                    )
                    self.stalker_ids.add((member.id, after.channel.id))
                elif after.self_stream or after.self_video:
                    self.stalker_ids.remove((member.id, after.channel.id))

    @tasks.loop(seconds=stalker_kick_refresh)
    async def kick_stalkers(self):
        # return  # phuck kicking let ppl see stream coz no one joins anyways ;-;
        if not len(self.stalker_ids) > 0:
            return

        guild = self.bot.get_guild(guild_id)
        ninja = guild.get_role(ninja_role_id)
        studying = guild.get_role(study_role_id)
        channel = guild.get_channel(study_channel_id)

        stalkers = self.stalker_ids.copy()
        for stalker_id in stalkers:
            user = discord.utils.get(guild.members, id=stalker_id[0])
            channel_id = stalker_id[1]
            vchannel = guild.get_channel(channel_id)
            lounge = guild.get_channel(study_lounge)
            await user.add_roles(ninja)
            await user.remove_roles(studying)
            await user.move_to(channel=lounge)
            await channel.send(
                f"{user.mention} you have been removed from **{vchannel}** for not **turning on video or not screensharing**",
                delete_after=message_delete_after,
            )
            if stalker_id in self.stalker_ids:
                self.stalker_ids.remove(stalker_id)

    @tasks.loop(hours=1)  # TESTING IN PROGRESS
    async def lb_reset(self):
        ist = dt.now().astimezone(tz("Asia/Kolkata"))
        hour = ist.now().hour
        date = ist.now().date
        weekday = ist.now().weekday()
        guild = self.bot.get_guild(guild_id)
        channel = guild.get_channel(study_channel_id)
        if hour == 0:  # hour 0 == 12AM? idk gotta test
            db.child("DAILY_TIME").remove()
            await channel.send(f"DAILY LEADERBOARD reset at {ist}")
        if weekday == 0 and hour == 0:  # day 0 == monday
            db.child("WEEKLY_TIME").remove()
            await channel.send(f"WEEKLY LEADERBOARD reset at {ist}")
        if date == 1 and hour == 0:  # date 1 == first day of month
            await channel.send(f"MONTHLY LEADERBOARD reset at {ist}")
            db.child("MONTHLY_TIME").remove()

    @tasks.loop(minutes=refresh_interval_mins)
    async def hmm(self):
        guild = self.bot.get_guild(guild_id)
        study_category = [c for c in guild.categories if c.id == study_category_id][0]

        members_studying = []
        for vc in study_category.voice_channels:
            if vc.id == study_lounge:
                continue

            for mem in vc.members:
                # CHECK IF MEMBER HAS VIDEO OR SCREENSHARE TURNED ON
                # AND ADD TIME IN SEPERATE VARIABLES
                if mem.voice.self_stream:
                    VC = "STREAM"
                elif mem.voice.self_video:
                    VC = "VIDEO"
                else:
                    VC = "NONE"
                if not mem.bot:
                    if mem.voice.self_stream and mem.voice.self_video:
                        members_studying.append((mem, "STREAM"))
                        members_studying.append((mem, "VIDEO"))
                    else:
                        members_studying.append((mem, VC))

        for mem in members_studying:
            add_mins(mem[0].id, mem[1])

    @commands.command(aliases=["st"])
    async def studytime(self, ctx, user: discord.User = None):
        if user == None:
            user = ctx.author
        emb = discord.Embed(title=f"Study VC stats for {user}", color=0x006900)

        for TIME in ("MEMBER_TIME", "DAILY_TIME", "WEEKLY_TIME", "MONTHLY_TIME"):
            data = db.child(TIME).child(user.id).get().val()
            if data == None:
                H, M = 0, 0
            else:
                H, M = mins_hours(data["MINUTES"])
            emb.add_field(
                name=TIME.replace("_", " "),
                value=f"**{H}** Hours **{M}** Minutes",
                inline=False,
            )

        data = db.child("VIDEO").child(user.id).get().val()
        if data == None:
            H, M = 0, 0
        else:
            H, M = mins_hours(data["MINUTES"])
        emb.add_field(
            name="VIDEO TIME", value=f"**{H}** Hours **{M}** Minutes", inline=False
        )

        data = db.child("STREAM").child(user.id).get().val()
        if data == None:
            H, M = 0, 0
        else:
            H, M = mins_hours(data["MINUTES"])
        emb.add_field(
            name="SCREENSHARE TIME",
            value=f"**{H}** Hours **{M}** Minutes",
            inline=False,
        )

        await ctx.send(embed=emb)

    # DWN = Daily || Weekly || Monthly + Video + Screenshare
    @commands.command(aliases=["lb"])
    async def leaderboard(self, ctx, DWM=""):
        TIME = Times[DWM.upper()]
        data = db.child(TIME).order_by_child("MINUTES").limit_to_last(10).get().val()
        dsc = ""
        rank = len(data)

        for id_ in data:
            try:
                user = await ctx.guild.fetch_member(id_)
            except Exception as e:
                user = "unknown member"
            H, M = mins_hours(data[id_]["MINUTES"])
            dsc = f"#{rank} | **{user}** | **{H}** Hours **{M}** Minutes\n" + dsc
            rank -= 1
        TIME = TIME.replace("_", " ")
        emb = discord.Embed(
            title=f"Study VC Leaderboard ({TIME})", description=dsc, color=0x006900
        )
        emb.set_footer(
            text=f"{ctx.author}\nvalid options : d,w,m,v,s",
            icon_url=ctx.author.avatar_url,
        )
        await ctx.send(embed=emb)
        
    @commands.command()
    async def source(self, ctx):
        await ctx.send("Here's the repository link:\nhttps://github.com/o-BigBoy/SankhoCordBot")


def setup(bot):
    bot.add_cog(Study(bot))
    print("---> STUDY LOADED")
