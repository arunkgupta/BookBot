#!/usr/bin/python
# -*- coding: utf-8 -*-

from sqlite3 import connect
from re import sub
from datetime import datetime

import praw
from bs4 import BeautifulSoup
from requests import get

DEBUG = True
TEST = False

#sqlite3
CONN = connect("bookbot.db")
CURSOR = CONN.cursor()

SQL_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS {tablename} (
    id TEXT PRIMARY KEY,
    subreddit TEXT NOT NULL,
    created_at TIMESTAMP
);
"""
SQL_SEARCH = """SELECT * FROM {tablename} WHERE id='{id}'"""
SQL_ADD_COMMENT = """INSERT INTO {tablename} (id, subreddit, created_at) VALUES ('{id}', '{subreddit}', '{now}')"""

# Reddit params
BOT = praw.Reddit('bookBot')

SUBREDDIT_LIST = [
"testingground4bots",
"chess",
"python",
"learnprogramming",
"programming"
]

if TEST:
    SUBREDDIT_LIST = [
    "testingground4bots"
    ]
SUBREDDIT = BOT.subreddit("+".join(SUBREDDIT_LIST))
NUMBER_OF_POSTS = 100
BOOK_CALLSIGN = "!getbook"
AUTHOR_CALLSIGN = "!getauthor"

# comment templates
TEMPLATE_BOOK = """
{number}. {title} by {author}. ({rating}/5 *) [Link]({link})
"""
SIGNATURE = """
***
^^I'm ^^a ^^bot, ^^check ^^me ^^out ^^at: ^^https://github.com/RoberTnf/BookBot
"""

# goodreads params
NUMBER_OF_BOOKS = 1
NUMBER_OF_BOOKS_AUTHOR = 5
SEARCH_URL = "https://www.goodreads.com/search?q="


def get_search_strings(comments, callsign):
    """
    Returns the string to be searched for in each comment
    """
    search_strings = []
    for comment in comments:
        for line in comment.body.lower().split("\n"):
            if callsign in line:
                search_string = line.split(callsign)[-1]
                if callsign == "!getauthor":
                    search_string += "&search%5Bfield%5D=author"
                search_strings.append(search_string)

    return search_strings

def get_books_info(search_strings, n=1):
    # parses goodread for info about books
    books_info = []
    for search_string in search_strings:
        request_text = get(SEARCH_URL + search_string,
                           headers={'User-Agent': 'BookBot-Agent'}).text
        if '<h3 class="searchSubNavContainer">No results.</h3>' not in request_text:
            soup = BeautifulSoup(request_text, "html.parser")
            books_content = []
            for book_content in soup.findAll("tr"):
                if book_content["itemtype"] == "http://schema.org/Book":
                    books_content.append(book_content)

            book_info = []
            # Avoid (books_info[-1]["link"]).text trying to read more books than exist
            n = min(n, len(books_content))
            for book_content in books_content[:n]:
                book_info.append({})
                book_info[-1]["title"] = book_content.find("span", {"itemprop" : "name"}).string
                book_info[-1]["author"] = book_content.find("a", { "class" : "authorName" }).span.string
                book_info[-1]["rating"] = book_content.find("span", {"class": "minirating"}).contents[-1][1:5]
                book_info[-1]["link"] = "https://www.goodreads.com" + book_content.find("a")["href"] +"&ac=1"

            if n == 1:
                request_text = get(book_info[-1]["link"]).text
                soup = BeautifulSoup(request_text, "html.parser")
                soup = soup.find("div", {"id":"description"})
                # check that the description exists
                if soup:
                    book_html = soup.findAll("span")[-1].text
                    sub('<[^<]+?>', '', book_html)
                    book_info[0]["description"] = book_html

            books_info.append(book_info)
        else:
            books_info.append(False)

    return(books_info)

def get_reply_strings(books_info):
    reply_texts = []
    for book_info in books_info:
        reply_text = ""
        if book_info:
            for i, book in enumerate(book_info):
                reply_text += TEMPLATE_BOOK.format(
                    number=i+1,
                    title=book["title"],
                    author=book["author"],
                    rating=book["rating"],
                    link=book["link"]
                )
            if "description" in book_info[0].keys():
                reply_text += "\n\n>{}\n\n".format(book_info[0]["description"])
        else:
            reply_text += "No results found."
        reply_text += SIGNATURE
        reply_texts.append(reply_text)
    return(reply_texts)

def was_replied(comment, table):
    rows = CURSOR.execute(SQL_SEARCH.format(tablename=table, id=comment.fullname))
    return bool(rows.fetchall())

def get_comments(callsign, table):
    # grab the request
    request = get('https://api.pushshift.io/reddit/search?q=%22{}%22&limit=100'.format(callsign[1:].lower()),
        headers = {'User-Agent': 'BookBot-Agent'})
    json = request.json()
    raw_comments = json["data"]
    comments = []

    for rawcomment in raw_comments:
        # object constructor requires empty attribute
        rawcomment['_replies'] = ''
        if callsign in rawcomment["body"].lower():
            comment = praw.models.Comment(BOT, _data=rawcomment)
            if not was_replied(comment, table):
                comments.append(comment)

    return(comments)


def reply(comments, reply_strings, table):
    for comment, reply_string in zip(comments, reply_strings):

        comment.reply(reply_string)

        # saves to DB
        subreddit = comment.permalink().split("/")[2]
        print(SQL_ADD_COMMENT.format(
            tablename=table,
            id=comment.fullname,
            subreddit=subreddit,
            now=datetime.now()))
        CURSOR.execute(SQL_ADD_COMMENT.format(
            tablename=table,
            id=comment.fullname,
            subreddit=subreddit,
            now=datetime.now()
            ))
        CONN.commit()

def main():

    # books
    table="books"
    CURSOR.execute(SQL_CREATE_TABLE.format(tablename=table))
    comments = get_comments(BOOK_CALLSIGN, table)
    search_strings = get_search_strings(comments, BOOK_CALLSIGN)
    books_info = get_books_info(search_strings)
    reply_strings = get_reply_strings(books_info)
    reply(comments, reply_strings, table)

    #authors
    table="authors"
    CURSOR.execute(SQL_CREATE_TABLE.format(tablename=table))
    comments = get_comments(AUTHOR_CALLSIGN, table)
    search_strings = get_search_strings(comments, AUTHOR_CALLSIGN)
    books_info = get_books_info(search_strings, n=5)
    reply_strings = get_reply_strings(books_info)
    reply(comments, reply_strings, table)
    CONN.close()


if __name__ == "__main__":
    main()
