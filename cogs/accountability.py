import discord
from discord.ext import commands

nums = [
    "0️⃣",
    "1️⃣",
    "2️⃣",
    "3️⃣",
    "4️⃣",
    "5️⃣",
    "6️⃣",
    "7️⃣",
    "8️⃣",
    "9️⃣",
    "🔟",
    "🇦",
    "🇧",
    "🇨",
    "🇩",
    "🇪",
    "🇫",
    "🇬",
    "🇭",
    "🇮",
]  # max 20 reactions supported

""" every task message
:one:. task 1
:two:. task 2
...
> **PS ...**
> By <@id>
"""


class Accountability(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == 785725709288603688 and not message.author.bot:
            if "::" in message.content:
                PS = message.content.split("::")[1].replace("\n", ". ")
                PS = f"**PS - {PS}**"
                tasks = message.content.split("\n")[:-1]
            else:
                PS = ""
                tasks = message.content.split("\n")

            for i in range(len(tasks)):
                tasks[i] = nums[i] + f". {tasks[i]}"  # add number emoji to task
            n = len(tasks)
            tasks = "\n".join(tasks)

            goal = f"{tasks}\n> {PS}\n> By <@{message.author.id}>"
            await message.delete()
            msg = await message.channel.send(goal)
            for i in range(n):
                await msg.add_reaction(nums[i])

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction):
        """
        cross - delete message
        number - crossout the task
        """
        if reaction.channel_id == 785725709288603688 and not reaction.member.bot:
            guild_ = discord.utils.get(self.bot.guilds, id=785024897863647282)
            channel_ = discord.utils.get(guild_.channels, id=785725709288603688)
            msg = await channel_.fetch_message(reaction.message_id)
            msg_cnt = msg.content
            uid = msg.content.split("\n")[-1]
            if str(reaction.member.id) in uid:
                tasks = msg_cnt.split("\n")[:-2]
                if reaction.emoji.name in nums:
                    i = nums.index(reaction.emoji.name)
                    if not "✅" in tasks[i]:
                        tasks[i] = tasks[i][:5] + "~~" + tasks[i][5:] + "~~ ✅"
                        t = 0
                        for _ in tasks:
                            if "~" in tasks:
                                t += 1
                        print(t)
                await msg.edit(
                    content="\n".join(tasks)
                    + "\n"
                    + "\n".join(msg.content.split("\n")[-2:])
                )


def setup(bot):
    bot.add_cog(Accountability(bot))
    print("---> ACCOUNTABILITY LOADED")
