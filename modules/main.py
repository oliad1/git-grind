"""
Main script to run the discord bot
"""

import logging
import os
import sqlite3
import datetime
import requests
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord import app_commands
from modules import constants as const

def main(cursor: sqlite3.Cursor, conn: sqlite3.Connection):
    """
    Main function to run the bot (pylint...)
    """
    env_res = load_dotenv()

    if not env_res:
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

    # user (username, commits, numRepos, PRs, issues, pronouns, bio, user_status, lastFetched)
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
        FOREIGN KEY (username) REFERENCES users(username),
        PRIMARY KEY (guild_id, username)
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
        print(f"{bot.user.name} bot is ready")

        try:
            guild = discord.Object(id=str(local_server_id))
            synced = await bot.tree.sync(guild=guild)
            print(f"Synced {len(synced)} commands to guild {guild.id}")

        except discord.errors.HTTPException as e:
            print(f"Error syncing commands: {e}")

    guild_id = discord.Object(id=int(local_server_id))

    @bot.event
    async def on_member_join(member):
        await member.send(f"Welcome to the server {member.name}")

    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return

        print(message.content)

        await bot.process_commands(message)

    @bot.tree.command(name="user", description="Fetch information about a user", guild=guild_id)
    async def search_user(interaction: discord.Interaction, username: str):
        query = const.get_user(username)
        headers = const.get_auth_header(gh_token)
        response = requests.post(url=const.GITHUB_BASE_URL, json=query, headers=headers, timeout=10)
        status = response.status_code
        if status != 200:
            await interaction.response.send_message("Failed to get user info for "+username)
        if status == 200:
            user_data = (response.json())["data"]["user"]
            name = user_data["name"]
            handle = user_data["login"]
            avatar_url = user_data["avatarUrl"]
            contribution_data = user_data["contributionsCollection"]
            total_commits = contribution_data["totalCommitContributions"]
            total_repos = contribution_data["totalRepositoryContributions"]
            total_prs = contribution_data["pullRequestContributions"]["totalCount"]
            total_issues = contribution_data["issueContributions"]["totalCount"]
            pronouns = user_data["pronouns"]
            bio = user_data["bio"]
            user_status = user_data["status"]

            desc = ""

            if pronouns:
                name += ' ('+pronouns+')'

            if handle:
                desc += f'[{handle}]({const.GITHUB_URL}{handle})'+'\n'

            if bio:
                desc += bio+'\n'

            if user_status:
                desc += '> '+user_status["emoji"]+' '+user_status["message"]+'\n'

            embed = discord.Embed(
                title=name,
                description=desc,
                color=discord.Color.blue()
            )

            embed.add_field(name="", value=(
                f"**Commits:** {total_commits}\n"
                f"**Repositories:** {total_repos}\n"
                f"**PRs:** {total_prs}\n"
                f"**Issues:** {total_issues}"
            ), inline=False)

            embed.set_thumbnail(url=avatar_url)
            await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="add", description="Add a user to your server", guild=guild_id)
    async def add_user(interaction: discord.Interaction, username: str):
        query = const.get_user(username)
        headers = const.get_auth_header(gh_token)
        response = requests.post(url=const.GITHUB_BASE_URL, json=query, headers=headers, timeout=10)
        status = response.status_code
        if status != 200:
            await interaction.response.send_message("Failed to get user info for "+username)
        if status == 200:
            user_data = (response.json())["data"]["user"]
            name = user_data["name"]
            handle = user_data["login"]
            avatar_url = user_data["avatarUrl"]
            contribution_data = user_data["contributionsCollection"]
            total_commits = contribution_data["totalCommitContributions"]
            total_repos = contribution_data["totalRepositoryContributions"]
            total_prs = contribution_data["pullRequestContributions"]["totalCount"]
            total_issues = contribution_data["issueContributions"]["totalCount"]
            pronouns = user_data["pronouns"]
            bio = user_data["bio"]
            user_status = user_data["status"]

            desc = ""

            if pronouns:
                name += ' ('+pronouns+')'

            if handle:
                desc += f'[{handle}]({const.GITHUB_URL}{handle})'+'\n'

            if bio:
                desc += bio+'\n'

            if user_status:
                desc += '> '+user_status["emoji"]+' '+user_status["message"]+'\n'

            sql = """
            INSERT INTO users (username, commits, repos, prs, issues, pronouns, bio, last_fetched)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (username) DO UPDATE SET
                username = excluded.username,
                commits = excluded.commits,
                repos = excluded.repos,
                prs = excluded.prs,
                issues = excluded.issues,
                pronouns = excluded.pronouns,
                bio = excluded.bio,
                last_fetched = excluded.last_fetched
           """

            _ = cursor.execute(sql, (username, total_commits, total_repos, total_prs, total_issues, pronouns, bio, datetime.datetime.now()))

            conn.commit()

            sql = """
            INSERT INTO server_users (guild_id, username)
            VALUES (?, ?) 
            """

            _ = cursor.execute(sql, (guild_id.id, username))

            conn.commit()

            embed = discord.Embed(
                title="Added "+name,
                description=desc,
                color=discord.Color.blue()
            )

            embed.add_field(name="", value=(
                f"**Commits:** {total_commits}\n"
                f"**Repositories:** {total_repos}\n"
                f"**PRs:** {total_prs}\n"
                f"**Issues:** {total_issues}"
            ), inline=False)

            embed.set_thumbnail(url=avatar_url)
            await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="remove", description="Remove a user to your server", guild=guild_id)
    async def remove_user(interaction: discord.Interaction, username: str):
        # Check DB to see that user exists
        # Only delete server_users row, keep general user cache
        sql = """
        DELETE FROM server_users
        WHERE username = ?
        """

        _ = cursor.execute(sql, (username,))

        conn.commit()

        embed = discord.Embed(
            title="Deleted "+username,
            description="",
            color=discord.Color.blue()
        )

        embed.add_field(name="", value=(
            ""
        ), inline=False)

        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="leaderboard", description="Rank github stats with friends", guild=guild_id)
    @app_commands.choices(stat=[
        app_commands.Choice(name="Commits", value="commits"),
        app_commands.Choice(name="PRs", value="prs"),
        app_commands.Choice(name="Repos", value="repos"),
        app_commands.Choice(name="Issues", value="issues"),
    ])
    async def rank_users(interaction: discord.Interaction, stat: app_commands.Choice[str]): # Add param for comparing commits vs PRs vs issues
        # Read from SQLite file for this GUILD's
        # If commit store request was < 10 min ago then just use cache
        # Make an github API request for others, and save them to sqlite
        # Return sql in descending order
        # Users should be one to many (one user can be in multiple servers
        # user (username, commits, numRepos, PRs, issues, pronouns, bio, user_status, lastFetched)
        # server_users (guild_id/server_id, user_id)
        sql = f"""
        SELECT users.username, users.{stat.value}
        FROM users
        INNER JOIN server_users
        ON users.username = server_users.username
        WHERE server_users.guild_id = '{guild_id.id}'
        ORDER BY users.{stat.value} DESC
        """

        res = cursor.execute(sql)

        rows = res.fetchall()

        print("ROWS "+str(rows))

        leaderboard = ""

        for i, row in enumerate(rows):
            if i > 2:
                leaderboard += f"**{i+1}.** [**{row[0]}**]({const.GITHUB_URL}{row[0]}) - **{row[1]}\u200b** {stat.value}\n"
            else:
                leaderboard += f"**:{const.emoji[i]}_place:** [**{row[0]}**]({const.GITHUB_URL}{row[0]}) - **{row[1]}** {stat.value}\n"

        embed = discord.Embed(
            title=f"Alltime Leaderboard ({stat.name})",
            description="",
            color=discord.Color.blue()
        )

        embed.add_field(name="", value=(
            leaderboard
        ), inline=False)

        await interaction.response.send_message(embed=embed)

    bot.run(bot_token, log_handler=handler, log_level=logging.DEBUG)

if __name__ == "__main__":
    db_conn = sqlite3.connect(r'test.db')

    db_cursor = db_conn.cursor()

    db_cursor.execute("PRAGMA foreign_keys = ON;")

    main(db_cursor, db_conn)

    db_conn.close()
