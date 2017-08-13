#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3
import praw
import BeautifulSoup
import requests
import re

from datetime import datetime

DEBUG="TRUE"

#sqlite3
CONN = sqlite3.connect("bookbot.db")
CURSOR = CONN.cursor()
SQL_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS comments (
    id integer PRIMARY KEY,
    comment text NOT NULL,
    created_at TIMESTAMP
);
"""
SQL_SEARCH = """SELECT * FROM comments WHERE comment='{comment_perm}'"""
SQL_ADD_COMMENT = """INSERT INTO comments(comment, created_at) VALUES ('{comment_perm}', '{now}')"""

# Reddit params
BOT = praw.Reddit('bookBot')
SUBREDDIT_LIST = [
"testingground4bots",
"chess"
]
SUBREDDIT = BOT.subreddit("+".join(SUBREDDIT_LIST))
NUMBER_OF_POSTS = 100
CALLSIGN = "!book"
AUTHOR_CALLSIGN = "!author"

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


def get_search_string(comment):
    """
    Returns the string to be searched for in comment
    """

    filt=""
    for line in comment.body.lower().split("\n"):
        if CALLSIGN in line:
            search_string = line.split(CALLSIGN)[-1]
        elif AUTHOR_CALLSIGN in line:
            search_string = line.split(AUTHOR_CALLSIGN)[-1]
            filt = "author"



    return search_string, filt

def get_book_info(search_string, n):
    # parses goodread for info about books
    request_text = requests.get(SEARCH_URL + search_string).text
    if '<h3 class="searchSubNavContainer">No results.</h3>' not in request_text:
        soup = BeautifulSoup.BeautifulSoup(request_text)
        books_content = []
        for book_content in soup.findAll("tr"):
            if book_content["itemtype"] == "http://schema.org/Book":
                books_content.append(book_content)

        books_info = []
        # Avoid (books_info[-1]["link"]).text trying to read more books than exist
        n = min(n, len(books_content))
        for book_content in books_content[:n]:
            books_info.append({})
            books_info[-1]["title"] = book_content.find("span", {"itemprop" : "name"}).string
            books_info[-1]["author"] = book_content.find("a", { "class" : "authorName" }).span.string
            books_info[-1]["rating"] = book_content.find("span", {"class": "minirating"}).contents[-1][1:5]
            books_info[-1]["link"] = "https://www.goodreads.com" + book_content.find("a")["href"] +"&ac=1"

        if n == 1:
            request_text = requests.get(books_info[-1]["link"]).text
            soup = BeautifulSoup.BeautifulSoup(request_text)
            book_html = soup.find("div", {"id":"description"}).findAll("span")[-1].text
            re.sub('<[^<]+?>', '', book_html.encode("utf-8"))
            books_info[0]["description"] = book_html

        return(books_info)
    else:
        return(False)

def build_reply_string(books):
    reply_text = ""
    for i, book in enumerate(books):
        reply_text += TEMPLATE_BOOK.format(
            number=i+1,
            title=book["title"].encode("utf-8"),
            author=book["author"].encode("utf-8"),
            rating=book["rating"].encode("utf-8"),
            link=book["link"].encode("utf-8")
        )
    if len(books) == 1:
        reply_text += "\n\n>{}\n\n".format(books[0]["description"].encode("utf-8"))
    reply_text += SIGNATURE
    return(reply_text)

def was_replied(comment):
    rows = CURSOR.execute(SQL_SEARCH.format(comment_perm=comment.permalink()))
    return bool(rows.fetchall())


def main():

    print(str(datetime.now()))
    CURSOR.execute(SQL_CREATE_TABLE)
    # Parses SUBREDDIT to get comments in whichCALLSIGN is used
    for comment in SUBREDDIT.comments(limit=NUMBER_OF_POSTS):
        if (CALLSIGN in comment.body.lower()
            or AUTHOR_CALLSIGN in comment.body.lower()):
            search_string, filt = get_search_string(comment)

            # checks if already replied to this comment
            if was_replied(comment):
                if DEBUG:
                    print("Already replied to {}".format(comment.permalink()))
                continue

            # gets book info
            n = NUMBER_OF_BOOKS
            if filt:
                n = NUMBER_OF_BOOKS_AUTHOR
            book_info = get_book_info(search_string, n)
            if not book_info:
                if DEBUG:
                    print("No info for {}".format(search_string))
                CURSOR.execute(SQL_ADD_COMMENT.format(comment_perm=comment.permalink()))
                continue

            # replies
            reply_string = build_reply_string(book_info)
            comment.reply(reply_string)
            if DEBUG:
                print("reply: \n{}".format(reply_string))

            # saves to DB
            CURSOR.execute(SQL_ADD_COMMENT.format(comment_perm=comment.permalink(), now=datetime.now()))
    CONN.commit()
    CONN.close()


if __name__ == "__main__":
    main()
