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
CREATE TABLE IF NOT EXISTS comments (
    id integer PRIMARY KEY,
    subreddit text NOT NULL,
    created_at TIMESTAMP
);
"""
SQL_SEARCH = """SELECT * FROM comments WHERE id='{id}'"""
SQL_ADD_COMMENT = """INSERT INTO comments(id, subreddit, created_at) VALUES ('{id}', '{comment_perm}', '{now}')"""

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
CALLSIGN = "!getbook"
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
    request_text = get(SEARCH_URL + search_string).text
    if '<h3 class="searchSubNavContainer">No results.</h3>' not in request_text:
        soup = BeautifulSoup(request_text, "html.parser")
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
            request_text = get(books_info[-1]["link"]).text
            soup = BeautifulSoup(request_text, "html.parser")
            soup = soup.find("div", {"id":"description"})
            # check that the description exists
            if soup:
                book_html = soup.findAll("span")[-1].text
                sub('<[^<]+?>', '', book_html)
                books_info[0]["description"] = book_html

        return(books_info)
    else:
        return(False)

def build_reply_string(books):
    reply_text = ""
    for i, book in enumerate(books):
        reply_text += TEMPLATE_BOOK.format(
            number=i+1,
            title=book["title"],
            author=book["author"],
            rating=book["rating"],
            link=book["link"]
        )
    if "description" in books[0].keys():
        reply_text += "\n\n>{}\n\n".format(books[0]["description"])
    reply_text += SIGNATURE
    return(reply_text)

def was_replied(comment):
    rows = CURSOR.execute(SQL_SEARCH.format(comment_perm=comment.permalink()))
    return bool(rows.fetchall())

def get_comments_book():
    # grab the request
    request = get('https://api.pushshift.io/reddit/search?q=%22getBook%22&limit=100',
        headers = {'User-Agent': 'BookBot-Agent'})
    json = request.json()
    raw_comments = json["data"]
    comments = []

    for rawcomment in raw_comments:
        # object constructor requires empty attribute
        rawcomment['_replies'] = ''
        if CALLSIGN in rawcomment["body"].lower():
            comments.append(praw.models.Comment(BOT, _data=rawcomment))

    return(comments)


"""
def main():
    CURSOR.execute(SQL_CREATE_TABLE)
    # Parses SUBREDDIT to get comments in whichCALLSIGN is used
    comments = get_comments_book()
    # gets book info
    n = NUMBER_OF_BOOKS
    if filt:
        n = NUMBER_OF_BOOKS_AUTHOR
    book_info = get_book_info(search_string, n)
    if not book_info:
        if DEBUG:
            print("No info for {}".format(search_string))
        CURSOR.execute(SQL_ADD_COMMENT.format(comment_perm=comment.permalink(), now=datetime.now()))


    # replies
    reply_string = build_reply_string(book_info)
    comment.reply(reply_string)
    # saves to DB
    CURSOR.execute(SQL_ADD_COMMENT.format(comment_perm=comment.permalink(), now=datetime.now()))
    CONN.commit()_list
    if DEBUG:
        print("reply: \n{}".format(reply_string))

    CONN.close()
"""
def main():
    CURSOR.execute(SQL_CREATE_TABLE)
    get_comments_book()


if __name__ == "__main__":
    main()
