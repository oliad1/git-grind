# Git Grind
👾 CodeGrind for GitHub. Compare your stats with friends (commits, PRs, issues, etc.).

## How to run it
First clone the repo: 
```bash
git clone https://github.com/oliad1/git-grind.git
cd ./git-grind
```
Make sure you have Python 3.11 downloaded, then run the following in your terminal:
```ps
pip install -r requirements.txt
```
Create a `.env` file and populate it with the secrets in `.env.sample`.

Once finished, you can execute this to run the bot:
```ps
python -m modules.main
```

## Commands
- /user [username]
- /add [username]
- /remove [username]
- /leaderboard [stat]

## Contributing
To contribute to this project make a new branch, open a PR. Make sure you have a 10.00/10.0 when running `pylint .`
