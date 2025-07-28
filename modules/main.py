import discord
from discord.ext import commands
from discord import app_commands
import logging
from dotenv import load_dotenv
import os
import requests
from modules import constants as const

def main():
    envRes = load_dotenv()

    if not envRes:
        print("Error: Could not load .env file")
        return

    bot_token = os.getenv('DISCORD_TOKEN')

    if not bot_token:
        print("Error: Could not find DISCORD_TOKEN in .env file")
        return

    gh_token = os.getenv('GITHUB_TOKEN')

    if not gh_token:
        print("Error: Could not find GITHUB_TOKEN in .env file")
        return

    local_server_id = os.getenv("LOCAL_SERVER_ID")

    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    bot = commands.Bot(command_prefix='/', intents=intents)


    @bot.event
    async def on_ready():
        print(f"{bot.user.name} bot is ready");

        try:
            guild = discord.Object(id=local_server_id)
            synced = await bot.tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands to guild {guild.id}")

        except Exception as e:
            print(f"Error syncing commands: {e}")

    GUILD_ID = discord.Object(id=local_server_id)

    @bot.tree.command(name="hello", description="Say hello!", guild=GUILD_ID)
    async def sayHello(interaction: discord.Interaction):
        await interaction.response.send_message("Hello user!")

    @bot.event
    async def on_member_join(member):
        await member.send(f"Welcome to the server {member.name}")

    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return

        print(message.content)

        await bot.process_commands(message)

    @bot.command()
    async def poll(ctx, *, question):
        embed = discord.Embed(title="Leaderboard", description=question)
        poll_message = await ctx.send(embed=embed)
        #await poll_message.add_reaction("")

    @bot.tree.command(name="user", description="Fetch information about a user", guild=GUILD_ID)
    async def searchUser(interaction: discord.Interaction, username: str):
        query = const.getUser(username)
        headers = const.getAuthHeader(gh_token)
        response = requests.post(url=const.GITHUB_BASE_URL, json=query, headers=headers)
        status = response.status_code
        if status == 200:
            await interaction.response.send_message(f"${response.json()}")

    bot.run(bot_token, log_handler=handler, log_level=logging.DEBUG)

if __name__ == "__main__":
    main()
