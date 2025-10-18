import discord
from discord.ext import commands
from discord import app_commands
import logging
from dotenv import load_dotenv
import os
import requests
from modules import constants as const
import sqlite3
import datetime

def main(cursor: sqlite3.Cursor, conn: sqlite3.Connection):
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

    # user (username, commits, numRepos, PRs, issues, pronouns, bio, userStatus, lastFetched)
    # server_users (guild_id/server_id, user_id)
    sql = """CREATE TABLE IF NOT EXISTS users (
        username TEXT NOT NULL,
        commits INTEGER,
        repos INTEGER,
        prs INTEGER,
        issues INTEGER,
        pronouns TEXT,
        bio TEXT,
        user_status TEXT,
        last_fetched TIMESTAMP NOT NULL,
        PRIMARY KEY (username)
    )
    """

    _ = cursor.execute(sql)

    conn.commit()

    sql = """CREATE TABLE IF NOT EXISTS server_users (
        guild_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        FOREIGN KEY (username) REFERENCES users(username)
    )
    """

    _ = cursor.execute(sql)

    conn.commit()

    handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True

    bot = commands.Bot(command_prefix='/', intents=intents)

    @bot.event
    async def on_ready():
        print(f"{bot.user.name} bot is ready");

        try:
            guild = discord.Object(id=str(local_server_id))
            synced = await bot.tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands to guild {guild.id}")

        except Exception as e:
            print(f"Error syncing commands: {e}")

    GUILD_ID = discord.Object(id=int(local_server_id))

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
        if status != 200:
            await interaction.response.send_message("Failed to get user info for "+username)
        if status == 200:
            userData = (response.json())["data"]["user"]
            name = userData["name"]
            handle = userData["login"]
            avatarUrl = userData["avatarUrl"]
            contributionData = userData["contributionsCollection"]
            totalCommits = contributionData["totalCommitContributions"]
            totalRepos = contributionData["totalRepositoryContributions"]
            totalPRs = contributionData["pullRequestContributions"]["totalCount"]
            totalIssues = contributionData["issueContributions"]["totalCount"]
            pronouns = userData["pronouns"]
            bio = userData["bio"]
            userStatus = userData["status"]

            desc = ""

            if pronouns:
                name += ' ('+pronouns+')'

            if handle:
                desc += f'[{handle}]({const.GITHUB_URL}{handle})'+'\n'
            
            if bio:
                desc += bio+'\n'

            if userStatus:
                desc += '> '+userStatus["emoji"]+' '+userStatus["message"]+'\n'

            embed = discord.Embed(
                title=name,
                description=desc,
                color=discord.Color.blue()
            )

            embed.add_field(name="", value=(
                f"**Commits:** {totalCommits}\n"
                f"**Repositories:** {totalRepos}\n"
                f"**PRs:** {totalPRs}\n"
                f"**Issues:** {totalIssues}"
            ), inline=False)

            embed.set_thumbnail(url=avatarUrl)
            await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="add", description="Add a user to your server", guild=GUILD_ID)
    async def addUser(interaction: discord.Interaction, username: str):
        query = const.getUser(username)
        headers = const.getAuthHeader(gh_token)
        response = requests.post(url=const.GITHUB_BASE_URL, json=query, headers=headers)
        status = response.status_code
        if status != 200:
            await interaction.response.send_message("Failed to get user info for "+username)
        if status == 200:
            userData = (response.json())["data"]["user"]
            name = userData["name"]
            handle = userData["login"]
            avatarUrl = userData["avatarUrl"]
            contributionData = userData["contributionsCollection"]
            totalCommits = contributionData["totalCommitContributions"]
            totalRepos = contributionData["totalRepositoryContributions"]
            totalPRs = contributionData["pullRequestContributions"]["totalCount"]
            totalIssues = contributionData["issueContributions"]["totalCount"]
            pronouns = userData["pronouns"]
            bio = userData["bio"]
            userStatus = userData["status"]

            desc = ""

            if pronouns:
                name += ' ('+pronouns+')'

            if handle:
                desc += f'[{handle}]({const.GITHUB_URL}{handle})'+'\n'
            
            if bio:
                desc += bio+'\n'

            if userStatus:
                desc += '> '+userStatus["emoji"]+' '+userStatus["message"]+'\n'

            sql = f"""
            INSERT INTO users (username, commits, repos, prs, issues, pronouns, bio, last_fetched)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            res = cursor.execute(sql, (username, totalCommits, totalRepos, totalPRs, totalIssues, pronouns, bio, datetime.datetime.now()))

            conn.commit()

            sql = """
            INSERT INTO server_users (guild_id, username)
            VALUES (?, ?) 
            """

            res = cursor.execute(sql, (GUILD_ID.id, username))

            conn.commit()

            for row in res.fetchall():
                for item in row:
                    print(item+" ")

            embed = discord.Embed(
                title="Added "+name,
                description=desc,
                color=discord.Color.blue()
            )

            embed.add_field(name="", value=(
                f"**Commits:** {totalCommits}\n"
                f"**Repositories:** {totalRepos}\n"
                f"**PRs:** {totalPRs}\n"
                f"**Issues:** {totalIssues}"
            ), inline=False)

            embed.set_thumbnail(url=avatarUrl)
            await interaction.response.send_message(embed=embed)


    @bot.tree.command(name="leaderboard", description="Rank github stats with friends", guild=GUILD_ID)
    async def rankUsers(interaction: discord.Interaction): # Add param for comparing commits vs PRs vs issues
        # Read from SQLite file for this GUILD's
        # If commit store request was < 10 min ago then just use cache
        # Make an github API request for others, and save them to sqlite
        # Return sql in descending order
        # Users should be one to many (one user can be in multiple servers
        # user (username, commits, numRepos, PRs, issues, pronouns, bio, userStatus, lastFetched)
        # server_users (guild_id/server_id, user_id)
        sql = f"""
        SELECT users.username, users.commits
        FROM users
        INNER JOIN server_users
        ON users.username = server_users.username
        WHERE server_users.guild_id = '{GUILD_ID.id}'
        ORDER BY users.commits DESC
        """

        res = cursor.execute(sql)

        rows = res.fetchall()

        print("ROWS "+str(rows))

        leaderboard = ""

        for i, row in enumerate(rows):
            if i > 2:
                leaderboard += f"**{i+1}.** [**{row[0]}**]({const.GITHUB_URL}{row[0]}) - **{row[1]}\u200b** commits\n"
            else:
                leaderboard += f"**:{const.emoji[i]}_place:** [**{row[0]}**]({const.GITHUB_URL}{row[0]}) - **{row[1]}** commits\n"

        embed = discord.Embed(
            title="Alltime Leaderboard (Commits)",
            description="",
            color=discord.Color.blue()
        )

        embed.add_field(name="", value=(
            leaderboard
        ), inline=False)

        await interaction.response.send_message(embed=embed)

    bot.run(bot_token, log_handler=handler, log_level=logging.DEBUG)

if __name__ == "__main__":
    conn = sqlite3.connect(r'test.db')

    cursor = conn.cursor()

    main(cursor, conn)

    conn.close()
