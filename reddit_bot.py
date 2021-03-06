#!/usr/bin/env python3

"""
Reddit bot runner and specific functions.
"""
from datetime import datetime

from praw import Reddit
from praw.models import Comment
from requests import get
from re import sub

from config import TEMPLATE_BOOK, TEMPLATE_AUTHOR, SIGNATURE, CURSOR,\
    SQL_SEARCH, DEBUG, TEST, SQL_ADD_COMMENT, CONN,\
    SQL_CREATE_TABLE_REDDIT, BOOK_CALLSIGN, AUTHOR_CALLSIGN

from bookinfo import get_books_info, get_authors_info

BOT = Reddit('bookBot')

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


def get_reply_strings_book(books_info):
    reply_texts = []
    for book_info in books_info:
        reply_text = ""
        if book_info:
            for i, book in enumerate(book_info):
                if "description" in book.keys():
                    # format description
                    # line breaks
                    book["description"] = book["description"].replace('\n', "")
                    book["description"] = book["description"].replace("<br/>", "\n\n>")
                    # bold
                    book["description"] = book["description"].replace("<b>", "**")
                    book["description"] = book["description"].replace("</b>", "**")
                    # remove html
                    book["description"] = sub('<[^<]+?>', '', book["description"])
                else:
                    book["description"] = "No description."
                reply_text += TEMPLATE_BOOK.format(
                    number=i+1,
                    title=book["title"],
                    author=book["author"],
                    rating=book["rating"],
                    link=book["link"],
                    description=book["description"]
                )
        else:
            reply_text += "No results found."
        reply_text += SIGNATURE
        reply_texts.append(reply_text)
    return(reply_texts)

def get_reply_strings_author(books_info, authors_info):
    reply_texts = []
    for author_info, book_info in zip(authors_info, books_info):
        reply_text = ""
        if author_info:
            if "description" in author_info.keys():
                # format description
                # line breaks
                author_info["description"] = author_info["description"].replace('\n', "")
                author_info["description"] = author_info["description"].replace("<br/>", "\n\n>")
                # bold
                author_info["description"] = author_info["description"].replace("<b>", "**")
                author_info["description"] = author_info["description"].replace("</b>", "**")
                # remove html
                author_info["description"] = sub('<[^<]+?>', '', author_info["description"])
            else:
                author_info["description"] = "No description."
            reply_text += TEMPLATE_AUTHOR.format(
                name=author_info["author"],
                link=author_info["link"],
                description=author_info["description"]
            )

            if book_info:
                for i, book in enumerate(book_info):
                    reply_text += TEMPLATE_BOOK.format(
                        number=i+1,
                        title=book["title"],
                        author=book["author"],
                        rating=book["rating"],
                        link=book["link"],
                        description=""
                    )
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
            comment = Comment(BOT, _data=rawcomment)
            if not was_replied(comment, table):
                comments.append(comment)

    return(comments)


def reply(comments, reply_strings, table):
    for comment, reply_string in zip(comments, reply_strings):

        comment.reply(reply_string)
        if DEBUG:
            print("Replied to: {}".format(comment.permalink()))
        # saves to DB
        subreddit = comment.permalink().split("/")[2]
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
    CURSOR.execute(SQL_CREATE_TABLE_REDDIT.format(tablename=table))
    comments = get_comments(BOOK_CALLSIGN, table)
    search_strings = get_search_strings(comments, BOOK_CALLSIGN)
    books_info = get_books_info(search_strings)
    reply_strings = get_reply_strings_book(books_info)
    if not TEST:
        reply(comments, reply_strings, table)
    else:
        print(reply_strings)

    #authors
    table = "authors"
    CURSOR.execute(SQL_CREATE_TABLE_REDDIT.format(tablename=table))
    comments = get_comments(AUTHOR_CALLSIGN, table)
    search_strings = get_search_strings(comments, AUTHOR_CALLSIGN)
    books_info, authors_info = get_authors_info(search_strings)
    reply_strings = get_reply_strings_author(books_info, authors_info)
    if not  TEST:
        reply(comments, reply_strings, table)
    else:
        print(reply_strings)
    CONN.close()


if __name__ == "__main__":
    main()
