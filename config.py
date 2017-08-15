"""Constants, SQL and PRAW connectors"""

from sqlite3 import connect
from praw import Reddit

DEBUG = True
TEST = True

#sqlite3
CONN = connect("bookbot.db")
CURSOR = CONN.cursor()

SQL_CREATE_TABLE_REDDIT = """
CREATE TABLE IF NOT EXISTS {tablename} (
    id TEXT PRIMARY KEY,
    subreddit TEXT NOT NULL,
    created_at TIMESTAMP
);
"""
SQL_SEARCH = """SELECT * FROM {tablename} WHERE id='{id}'"""
SQL_ADD_COMMENT = """INSERT INTO {tablename} (id, subreddit, created_at) VALUES ('{id}', '{subreddit}', '{now}')"""

# Reddit params
BOT = Reddit('bookBot')

NUMBER_OF_POSTS = 100
BOOK_CALLSIGN = "!getbook"
AUTHOR_CALLSIGN = "!getauthor"

# comment templates
TEMPLATE_BOOK = """
{number}. {title} by {author}. ({rating}/5 *) [Link]({link})
"""
TEMPLATE_AUTHOR = """
[{name}]({link})


>{description}

"""
SIGNATURE = """
***
^^I'm ^^a ^^bot, ^^check ^^me ^^out ^^at: ^^https://github.com/RoberTnf/BookBot
"""

# goodreads params
NUMBER_OF_BOOKS = 1
NUMBER_OF_BOOKS_AUTHOR = 5
SEARCH_URL = "https://www.goodreads.com/search?q="
