#!/usr/bin/env python3

import logging
import discord
from re import sub

from config import BOT_TOKEN, D_CALLSIGNS, D_CALLSIGNS_DICT, DEBUG,\
    D_TEMPLATE_BOOK, D_TEMPLATE_HELP, D_TEMPLATE_AUTHOR
from bookinfo import get_books_info, get_authors_info

# logging set up
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# init client
client = discord.Client()

def get_reply_strings_book(books_info):
    """
    Formats the reply message for discord.

    Input:
     - books_info list with dictionaries with information about each book
    Output:
     - reply_texts list with strings containing formatted replies"""

    reply_texts = []
    for book_info in books_info:
        reply_text = ""
        if book_info:
            for i, book in enumerate(book_info):
                if "description" in book.keys():
                    # format description
                    # line breaks
                    book["description"] = book["description"].replace('\n', "")
                    book["description"] = book["description"].replace("<br/>", "\n")
                    # bold
                    book["description"] = book["description"].replace("<b>", "**")
                    book["description"] = book["description"].replace("</b>", "**")
                    # remove html
                    book["description"] = sub('<[^<]+?>', '', book["description"])
                else:
                    book["description"] = "No description."
                reply_text += D_TEMPLATE_BOOK.format(
                    number=i+1,
                    title=book["title"],
                    author=book["author"],
                    rating=book["rating"],
                    link=book["link"]
                )
                reply_text += "```{}```".format(book["description"])
        else:
            reply_text += "No results found."
        reply_texts.append(reply_text)
    return(reply_texts)

def get_reply_strings_author(books_info, authors_info):
    """
    Formats the reply message for discord.

    Input:
     - books_info list with dictionaries with information about each book
     - authors_info same with autors information
    Output:
     - reply_texts list with strings containing formatted replies"""

    reply_texts = []
    for author_info, book_info in zip(authors_info, books_info):
        reply_text = ""
        if author_info:
            if book_info:
                for i, book in enumerate(book_info):
                    reply_text += D_TEMPLATE_BOOK.format(
                        number=i+1,
                        title=book["title"],
                        author=book["author"],
                        rating=book["rating"],
                        link=book["link"]
                    )
            if "description" in author_info.keys():
                # format description
                # line breaks
                author_info["description"] = author_info["description"].replace('\n', "")
                author_info["description"] = author_info["description"].replace("<br/>", "\n")
                # bold
                author_info["description"] = author_info["description"].replace("<b>", "**")
                author_info["description"] = author_info["description"].replace("</b>", "**")
                # remove html
                author_info["description"] = sub('<[^<]+?>', '', author_info["description"])
            else:
                author_info["description"] = "No description."
            reply_text += D_TEMPLATE_AUTHOR.format(
                name=author_info["author"],
                link=author_info["link"],
                description=author_info["description"]
            )
        else:
            reply_text += "No results found."
        if len(reply_text) > 1999:
            reply_text = reply_text[:1990] + "```"
        reply_texts.append(reply_text)
    return(reply_texts)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    # check it is a message to us
    if len(message.content.lower().split(" ", 1)) > 1:
        command, search_string = message.content.lower().split(" ", 1)
    else:
        command, search_string = ["",""]
    if command in D_CALLSIGNS:
        if search_string == "help":
            await client.send_message(message.channel, D_TEMPLATE_HELP)

        elif command == D_CALLSIGNS_DICT["book"]:
            if DEBUG:
                print("Looking for book: {}".format(search_string))
            books_info = get_books_info((search_string, ))
            reply_string = get_reply_strings_book(books_info)[0]
            await client.send_message(message.channel, reply_string)
            if DEBUG:
                print("Sent message")

        elif command == D_CALLSIGNS_DICT["author"]:
            if DEBUG:
                print("Looking for author: {}".format(search_string))
            books_info, authors_info = get_authors_info((search_string, ))
            reply_string = get_reply_strings_author(books_info, authors_info)[0]
            await client.send_message(message.channel, reply_string)
            if DEBUG:
                print("Sent message")


client.run(BOT_TOKEN)
