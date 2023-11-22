import discord
from discord.ext import commands
import random
import asyncio
YOUR_BOT_TOKEN = 'MTE3NjE4NjM5Nzg4ODA5NDI5MA.GOvs18.VozWtToNw7bPxY-wH3N19NQ7jd4ZwqqkwB2L6Q'
intents = discord.Intents.all()
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='secretsanta')
async def secretsanta(ctx):
    # Get the role named "Secret Santa"
    role = discord.utils.get(ctx.guild.roles, name='Mustiga Modsen')
    if not role:
        await ctx.send("Role 'Secret Santa' not found.")
        return

    # Get all members with the "Secret Santa" role
    members = [member.name for member in role.members]
    # Shuffle the list to randomize the order
    random.shuffle(members)
    # Create a dictionary with members as keys and empty strings as values
    secret_santa_list = [member for member in members]
    random.shuffle(secret_santa_list)
    finishedList = dict()
    for item in range(len(members)):
        
        while members[item] == secret_santa_list[0]:
            random.shuffle(secret_santa_list)
        finishedList[members[item]] = secret_santa_list[0]
        secret_santa_list.remove(secret_santa_list[0])
    # Send a message with the shuffled list of members and the Secret Santa assignments 
    for user in role.members:
        if user.dm_channel is None:
            await user.create_dm()
        for anvandare in role.members:
            if finishedList.get(user.name) == anvandare.name:
                await user.dm_channel.send("God jul {}, jag har något att säga till dig kom ihåg att hålla det hemligt, du har fått äran att ge en julklapp till {}".format(user.name,anvandare.nick))
        await asyncio.sleep(1)
bot.run(YOUR_BOT_TOKEN)

