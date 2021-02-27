<<<<<<< HEAD
import discord
import os
=======
# bot.py
import os

import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
>>>>>>> iloveeric

client = discord.Client()

@client.event
async def on_ready():
<<<<<<< HEAD
    print('We have logged in as {0.user}'.format(client))
=======
    print(f'{client.user} has connected to Discord!')
>>>>>>> iloveeric

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

<<<<<<< HEAD
client.run(os.getenv('TOKEN'))
=======
client.run(TOKEN)
>>>>>>> iloveeric
