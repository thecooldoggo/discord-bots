# Rufus Discord Bot
# Created by: @TheCoolDoggo
import discord
import os
import json
from dotenv import load_dotenv
from discord import app_commands
import aiohttp
import asyncio
import requests
from datetime import datetime, timedelta
from openai import OpenAI
import requests
import json

url = 'https://jamsapi.hackclub.dev/openai/chat/completions'
AIheaders = {
    'Content-Type': 'application/json',
    'Authorization': 'token'
}
data = {
    'model': 'gpt-3.5-turbo',
    'messages': [
        {
            'role': 'user',
            'content': 'DEBUG MESSAGE'
        }
    ],
}

response = requests.post(url, headers=AIheaders, data=json.dumps(data))

if response.status_code == 200:
    print(response.json()['choices'][0]['message']['content'])
else:
    print(f"Request failed with status code {response.status_code}")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
intents.messages = True
intents.message_content = True 
intents.members = True
streamer_live = False

headers = {
    'Authorization': 'token',
    'Client-ID': 'token',
}

async def is_live():
    url = "https://api.twitch.tv/helix/streams?user_login=asquirreloncoffee"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            return bool(data.get('data', []))

async def notify_when_live():
    global streamer_live
    await client.wait_until_ready()
    channel = client.get_channel(1229954064494891098)
    while not client.is_closed():
        if await is_live():
            if not streamer_live:
                data = {
                    'model': 'gpt-3.5-turbo',
                    'messages': [
                        {
                            'role': 'system',
                            'content': 'You are a helpful assistant that generates unique and nice messages about a streamer going live.'
                        },
                        {
                            'role': 'user',
                            'content': 'Generate a message for aSquirrelOnCoffee going live.'
                        }
                    ],
                }
                response = requests.post(url, headers=AIheaders, data=json.dumps(data))
                if response.status_code == 200:
                    live_message = response.json()['choices'][0]['message']['content'] + "<@&1229954247118950523>. https://www.twitch.tv/asquirreloncoffee"
                else:
                    live_message = "aSquirrelOnCoffee is now live! Join up <@&1229954247118950523>. https://www.twitch.tv/asquirreloncoffee"
                await channel.send(live_message)
                streamer_live = True
            await asyncio.sleep(30 * 30)  # wait for 30 mins before checking again
        else:
            if streamer_live:  # if the streamer was live but is no longer live
                top_clips = await get_top_clips('asquirreloncoffee')
                if top_clips:
                    await channel.send(f"Top clips from **aSquirrelOnCoffee's** last stream: \n- **#1** [twitch.tv/JubilantJokerDoggo88]({top_clips[0]['url']}) \n- **#2** [twitch.tv/DilapidatedEquatorPlatypus]({top_clips[1]['url']})")
                else:
                    await channel.send(f"No top clips found for aSquirrelOnCoffee's last stream. :sob:")
                streamer_live = False

def check_role(interaction):
    disallowed_user = 875226107673206834
    if interaction.user.id == disallowed_user:
        return False
    allowed_roles = [1229881444545986594, 1229882290260279431, 1229882993804447756]
    return any(role.id in allowed_roles for role in interaction.user.roles)

@tree.command(name = "topclips", description = "Get top 2 clips of a user's last stream", guild=discord.Object(id=1229878393256939660))
async def topclips_command(interaction, user: str):
    top_clips = await get_top_clips(user)
    if top_clips:
        await interaction.response.send_message(f"Top clips from **{user}'s** last stream: \n- **#1** [twitch.tv/JubilantJokerDoggo88]({top_clips[0]['url']}) \n- **#2** [twitch.tv/DilapidatedEquatorPlatypus]({top_clips[1]['url']})")
    else:
        await interaction.response.send_message(f"No clips found for {user}'s last stream. :sob:")

async def get_broadcaster_id(username):
    url = f"https://api.twitch.tv/helix/users?login={username}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            return data['data'][0]['id']

async def get_top_clips(username):
    broadcaster_id = await get_broadcaster_id(username)
    twelve_hours_ago = datetime.now() - timedelta(hours=12)
    twelve_hours_ago_iso = twelve_hours_ago.isoformat("T") + "Z"  # Convert to ISO 8601 format
    url = f"https://api.twitch.tv/helix/clips?broadcaster_id={broadcaster_id}&started_at={twelve_hours_ago_iso}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            clips = data['data']
            clips.sort(key=lambda clip: clip['view_count'], reverse=True)
            return clips[:2]

@tree.command(name = "echo", description = "Echo", guild=discord.Object(id=1229878393256939660))
async def echo_command(interaction, message: str):
    if not check_role(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    await interaction.response.send_message("Sent", ephemeral=True)
    await interaction.channel.send(message)


@tree.command(name = "ping", description = "returns pong + latency", guild=discord.Object(id=1229878393256939660))
async def ping_command(interaction):
    if not check_role(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    latency = client.latency 
    latency_ms = latency * 1000 
    await interaction.response.send_message(f"Pong! Bot is working. Latency: {latency_ms} ms")

@tree.command(name = "spam", description = "Spam Command", guild=discord.Object(id=1229878393256939660))
async def spam_command(interaction):
    if not check_role(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    await interaction.response.send_message("Please refrain from spamming the same message in chat, it can be distracting to aSquirrelOnCoffee and other viewers in the live stream and discord.")

@tree.command(name = "gethelp", description="You are not alone", guild=discord.Object(id=1229878393256939660))
async def help_command(interaction):
    await interaction.response.send_message("You are not alone. If you need help or are having suicidal thoughts, please call 988 inside the USA, 116123 in the UK or view [the complete list](https://blog.opencounseling.com/suicide-hotlines/) to see your local number. 🤍")

@tree.command(name = "petbeaver", description=":3", guild=discord.Object(id=1229878393256939660))
async def help_command(interaction):
    await interaction.response.send_message("+1 bet for beaver. :white_heart:")

@tree.command(name = "clear", description = "Clears a specified number of messages", guild=discord.Object(id=1229878393256939660))
async def clear_command(interaction, amount: int):
    allowed_roles = [1229881444545986594, 1229882290260279431, 1229882993804447756]
    if not any(role.id in allowed_roles for role in interaction.user.roles):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    if amount < 1:
        await interaction.response.send_message("You must delete at least one message.", ephemeral=True)
        return

    await interaction.response.send_message(f"Clearing {amount} messages...", ephemeral=True)

    messages = []
    async for message in interaction.channel.history(limit=amount+1):
        messages.append(message)

    for message in messages:
        await message.delete()
        await asyncio.sleep(.4)

@tree.command(name="reply", description="Reply to a user's DM", guild=discord.Object(id=1229878393256939660))
async def reply_command(interaction, user: discord.User, *, reply: str):
    allowed_roles = [1229881444545986594, 1229882290260279431, 1229882993804447756]
    if not any(role.id in allowed_roles for role in interaction.user.roles):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    await user.send(f"{reply}")
    await interaction.response.send_message(f"Message sent to {user}.", ephemeral=True)

@client.event
async def on_message(message):
    global count
    global last_message_time
    if message.guild is None and not message.author.bot:
        forward_channel_id = 1229888802898837535
        forward_channel = client.get_channel(forward_channel_id)
        await forward_channel.send(f"Message from {message.author.mention}: \n\n> {message.content} \n\nReply to the user using `/reply @user message`")

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Streaming(name="Playing Minecraft", url="https://www.twitch.tv/asquirreloncoffee"))
    await tree.sync(guild=discord.Object(id=1229878393256939660))
    client.loop.create_task(notify_when_live())
    print(f"Logged in as {client.user}")
    print("Ready!")

load_dotenv('rufus/token.env')
token = os.getenv('TOKEN')
client.run(token)