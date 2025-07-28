import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

def main():
    envRes = load_dotenv()

    if not envRes:
        print("Error: Could not load .env file")
        return

    token = os.getenv('DISCORD_TOKEN')

    if not token:
        print("Error: Could not find DISCORD_TOKEN in .env file")
        return

    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    bot = commands.Bot(command_prefix='/', intents=intents)

    @bot.event
    async def on_ready():
        print(f"{bot.user.name} bot is ready");

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
    async def hello(ctx):
        await ctx.send(f"Hello {ctx.author.mention}!")

    @bot.command()
    async def poll(ctx, *, question):
        embed = discord.Embed(title="Leaderboard", description=question)
        poll_message = await ctx.send(embed=embed)
        #await poll_message.add_reaction("")

    bot.run(token, log_handler=handler, log_level=logging.DEBUG)

if __name__ == "__main__":
    main()
