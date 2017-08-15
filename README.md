# BookBot

Small reddit bot that monitors certain subreddits and when summoned replies with information about a book/author.

Contact me if you want the bot to monitor a subreddit.

## Usage

Only one command per comment and the command must be in its own line.


### Reddit

- !getbook Name of book
- !getauthor Author of book

### Discord
- !book Name of book
- !author Author of book
- !book help

## Installation

If you want to run an instance of this bot:

1. Clone it
2. pip install -r requirements.txt
3. Create your praw.ini and enviroment variable DISCORD_BOT with your discord bot token.
4. python reddit_bot.py o python discord_bot.py

## TODO

1. Comment the code more
2. Fix and clean the code
3. Add a DB for discord bot
