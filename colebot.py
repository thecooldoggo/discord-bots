# Cole's Club Discord Bot
# Created by: @TheCoolDoggo
import discord
import os
import json
from dotenv import load_dotenv
from discord import app_commands
from discord import Embed
from discord import Member 
import aiohttp
import asyncio
import requests
from datetime import datetime, timedelta
import time

YOUTUBE_API_KEY = ''
CHANNEL_ID = 'UCwRbXtOEap9MujINjmXJkPQ'
LAST_VIDEO_ID = None

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
intents.messages = True
intents.message_content = True 
intents.members = True
streamer_live = False

with open("colebot/detention.json", "r") as f:
    detention_data = json.load(f)

with open("colebot/let-free.json", "r") as f:
    let_free_data = json.load(f)

detention_embed_data = detention_data['embeds'][0]
detention_embed = Embed.from_dict(detention_embed_data)

let_free_embed_data = let_free_data['embeds'][0]
let_free_embed = Embed.from_dict(let_free_embed_data)

headers = {
    'Authorization': 'token',
    'Client-ID': 'token',
}

async def check_new_video():
    global LAST_VIDEO_ID
    await client.wait_until_ready()
    channel = client.get_channel(1208244505086529576)

    # Load the last notified video ID from a file
    try:
        with open('colebot/last_video_id.txt', 'r') as file:
            LAST_VIDEO_ID = file.read().strip()
    except FileNotFoundError:
        LAST_VIDEO_ID = None

    while not client.is_closed():
        url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={CHANNEL_ID}&part=id&order=date&maxResults=1&type=video"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                latest_video_id = data['items'][0]['id']['videoId'] if data['items'] else None
                if latest_video_id and latest_video_id != LAST_VIDEO_ID:
                    await channel.send(f"<:youtube:1226691703868624926> Cole has posted a new video! <@&1231714925689180262> Check it out: https://www.youtube.com/watch?v={latest_video_id}")
                    LAST_VIDEO_ID = latest_video_id
                    # Save the last notified video ID to a file
                    with open('last_video_id.txt', 'w') as file:
                        file.write(latest_video_id)
        await asyncio.sleep(1800)


async def is_live():
    url = "https://api.twitch.tv/helix/streams?user_login=cole_rickards"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            return bool(data['data'])

async def notify_when_live():
    global streamer_live
    await client.wait_until_ready()
    channel = client.get_channel(1208244505086529576)
    while not client.is_closed():
        if await is_live():
            if not streamer_live:
                await channel.send("<:twitch:1226691726983299253> Cole is now live! Join up <@&1231714925689180262>. https://www.twitch.tv/cole_rickards")
                streamer_live = True
            await asyncio.sleep(30 * 30)
        else:
            if streamer_live:  # if the streamer was live but is no longer live
                top_clips = await get_top_clips('cole_rickards')
                if top_clips:
                    await channel.send(f"Top clips from **cole_rickards's** last stream: \n- **#1** [twitch.tv/JubilantJokerDoggo88]({top_clips[0]['url']}) \n- **#2** [twitch.tv/DilapidatedEquatorPlatypus]({top_clips[1]['url']})")
                else:
                    await channel.send(f"No top clips found for cole_rickards's last stream. :sob:")
                streamer_live = False

def check_role(interaction):
    disallowed_user = 875226107673206834
    if interaction.user.id == disallowed_user:
        return False
    allowed_roles = [1210721400927551559, 1208236554150092831, 1208236669363429427]
    return any(role.id in allowed_roles for role in interaction.user.roles)

@tree.command(name = "topclips", description = "Get top 2 clips of a user's last stream", guild=discord.Object(id=1208236402626527262))
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

@tree.command(name = "echo", description = "Echo", guild=discord.Object(id=1208236402626527262))
async def echo_command(interaction, message: str):
    if not check_role(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    await interaction.response.send_message("Sent", ephemeral=True)
    await interaction.channel.send(message)


@tree.command(name = "ping", description = "returns pong + latency", guild=discord.Object(id=1208236402626527262))
async def ping_command(interaction):
    if not check_role(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    latency = client.latency 
    latency_ms = latency * 1000 
    await interaction.response.send_message(f"Pong! Bot is working. Latency: **{latency_ms}** ms")

@tree.command(name = "english", description = "English Command", guild=discord.Object(id=1208236402626527262))
async def english_command(interaction):
    if not check_role(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    await interaction.response.send_message("Please speak English ONLY in chat. S’il vous plaît parlez l’anglais. Por favor, hable Inglés. Bitte sprecht Englisch. Si prega di parlare inglese. 英語を話してください. 영어를만 말하주세요. 請在聊天室中使用英語. Пожалуйста. говорите по-английски. الرجاء التحدث باللغه الانجليزيه فقط. Praat alsjeblieft Engels. Θα παρακαλουσαμε να μιλάτε μόνο Αγγλικά. Vennligst skriv engelsk I chatten. Govorite samo engleski u chatu. I hope you guys can understand 🩵")

@tree.command(name = "spam", description = "Spam Command", guild=discord.Object(id=1208236402626527262))
async def spam_command(interaction):
    if not check_role(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    await interaction.response.send_message("Please refrain from spamming the same message in chat, it can be distracting to Cole and other viewers in the live stream and discord.")

@tree.command(name = "rules", description = "Rules Command", guild=discord.Object(id=1208236402626527262))
async def rules_command(interaction):
    if not check_role(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    await interaction.response.send_message("Please read the <#1211074738416525402>. If a mod asks you to stop doing something, please listen to them. :white_heart:")

@tree.command(name = "caps", description = "Caps Command", guild=discord.Object(id=1208236402626527262))
async def caps_command(interaction):
    if not check_role(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    await interaction.response.send_message("Please try to avoid excessive use of CAPS. :thumbsup:")

@tree.command(name = "mod", description = "Mod Command", guild=discord.Object(id=1208236402626527262))
async def mod_command(interaction):
    if not check_role(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    await interaction.response.send_message("If you are interested in applying to become a mod, you can do so in <#1221093257539358731>. We are always looking for new mods to help out! :white_heart:")

@tree.command(name = "drama", description = "Drama Command", guild=discord.Object(id=1208236402626527262))
async def drama_command(interaction):
    if not check_role(interaction):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    await interaction.response.send_message("Please try not to cause any drama in chat. We like to have positive vibes only! Thank you! :white_heart:")

@tree.command(name = "gethelp", description="You are not alone", guild=discord.Object(id=1208236402626527262))
async def help_command(interaction):
    await interaction.response.send_message("You are not alone. If you need help or are having suicidal thoughts, please call 988 inside the USA, 116123 in the UK or view [the complete list](https://blog.opencounseling.com/suicide-hotlines/) to see your local number. 🤍")

@tree.command(name = "change-color", description = "Change the color of your role (vip only)", guild=discord.Object(id=1208236402626527262))
async def change_color_command(interaction, color: str):
    disallowed_user = 875226107673206834
    if interaction.user.id == disallowed_user:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    allowed_roles = [1210721400927551559, 1208236554150092831, 1208236669363429427, 1225440282179403806]
    if not any(role.id in allowed_roles for role in interaction.user.roles):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    color = discord.Color(int(color, 16))

    guild = client.get_guild(1208236402626527262)
    user_role = discord.utils.get(guild.roles, name=interaction.user.name)
    if user_role is None:
        user_role = await guild.create_role(name=interaction.user.name, color=color, permissions=discord.Permissions(send_messages=True))
        await interaction.user.add_roles(user_role)
        specified_role = discord.utils.get(guild.roles, id=1215290227808141353)
        await user_role.edit(position=specified_role.position + 1)

    await user_role.edit(color=color)
    await interaction.response.send_message("Role color changed to the specified color")

@tree.command(name = "clear", description = "Clears a specified number of messages", guild=discord.Object(id=1208236402626527262))
async def clear_command(interaction, amount: int):
    allowed_roles = [1210721400927551559, 1208236554150092831, 1208236669363429427]
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

@tree.command(name="reply", description="Reply to a user's DM", guild=discord.Object(id=1208236402626527262))
async def reply_command(interaction, user: discord.User, *, reply: str):
    allowed_roles = [1210721400927551559, 1208236554150092831, 1208236669363429427]
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
        forward_channel_id = 1227416892243836928
        forward_channel = client.get_channel(forward_channel_id)
        await forward_channel.send(f"Message from {message.author.mention}: \n\n> {message.content} \n\nReply to the user using `/reply @user message`")

@tree.command(name="blacklist", description="sends a user to blacklist", guild=discord.Object(id=1208236402626527262)) 
@app_commands.default_permissions(administrator=True)
async def detention(ctx: discord.Interaction, member: discord.Member, time_in_hours: int, reason: str = "No reason provided"):
    role_id = 1208236669363429427
    if role_id in [role.id for role in ctx.user.roles]:
        detention_role = discord.Object(id=1230864938512158761) 
        await member.add_roles(detention_role) 
        release_time = int(time.time()) + time_in_hours * 3600
        try:
            await ctx.response.send_message(f"{member.mention} has been sent to timeout for: {reason}.", ephemeral=True)
            detention_embed = Embed.from_dict(detention_embed_data)
            detention_embed.description += f"\nReason: {reason}\nRelease Time: <t:{release_time}:R>"
            await member.send(embed=detention_embed)
        except discord.Forbidden:
            print(f"Cannot DM {member.name} due to privacy settings.")
        except discord.NotFound:
            print("Interaction not found or already responded to.")
        await asyncio.sleep(time_in_hours * 3600)
        await member.remove_roles(detention_role) 
        try:
            await ctx.response.send_message(f"{member.mention} has been let free and was in timeout for {reason}. maybe read <#1211074738416525402> next time?")
            await member.send(embed=let_free_embed)
        except discord.Forbidden:
            print(f"Cannot DM {member.name} due to privacy settings.")
        except discord.NotFound:
            print("Interaction not found or already responded to.")
    else:
        await ctx.response.send_message("you do not have permission to use this command. nice try lol.")

@tree.command(name="let-free", description="removes a user from blacklist", guild=discord.Object(id=1208236402626527262)) 
@app_commands.default_permissions(administrator=True)
async def undetain(ctx: discord.Interaction, member: discord.Member):
    role_id = 1208236669363429427
    if role_id in [role.id for role in ctx.user.roles]:
        detention_role = discord.Object(id=1230864938512158761) 
        await member.remove_roles(detention_role) 
        try:
            await ctx.response.send_message(f"{member.mention} has been let free. maybe read <#1211074738416525402> next time?")
            await member.send(embed=let_free_embed)
        except discord.Forbidden:
            print(f"Cannot DM {member.name} due to privacy settings.")
        except discord.NotFound:
            print("Interaction not found or already responded to.")
    else:
        await ctx.response.send_message("you do not have permission to use this command. nice try lol.")


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Streaming(name="DM to talk", url="http://www.twitch.tv/cole_rickards"))
    await tree.sync(guild=discord.Object(id=1208236402626527262))
    client.loop.create_task(notify_when_live())
    client.loop.create_task(check_new_video())
    print(f"Logged in as {client.user}")
    print("Ready!")

load_dotenv('colebot/token.env')
token = os.getenv('TOKEN')
client.run(token)
