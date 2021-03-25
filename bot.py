import os

import discord
from discord.ext import tasks, commands

# This library handles the .env files and how to read them
# The .env file is a layer of security that makes it so the API Token of the bot
# is not shown anywhere in the code
from dotenv import load_dotenv

# Here I'm loading all the environnement into variables to then use into the code
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD_NAME')

# Starting the bot object
bot = commands.Bot(command_prefix='!')
initial_extensions = ['cogs.curation']

if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)
     
@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(guild)
    print(f'{bot.user} has connected to Discord!')
    print(f'{bot.user} is connected to the following guild:\n'
              f'{guild.name}(id: {guild.id})')
    
bot.run(TOKEN)