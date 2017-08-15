"""
Gets info from goodreads.
"""

from re import sub
from bs4 import BeautifulSoup
from requests import get
from config import SEARCH_URL, NUMBER_OF_BOOKS, NUMBER_OF_BOOKS_AUTHOR

def get_books_info(search_strings):
    # parses goodread for info about books
    books_info = []
    for search_string in search_strings:
        request_text = get(SEARCH_URL + search_string,
                           headers={'User-Agent': 'BookBot-Agent'}).text
        if '<h3 class="searchSubNavContainer">No results.</h3>' not in request_text:
            soup = BeautifulSoup(request_text, "html.parser")
            books_content = []
            book_info = []
            # Avoid (books_info[-1]["link"]).text trying to read more books than exist
            books_content = soup.findAll("tr", {"itemtype":"http://schema.org/Book"})
            n = min(NUMBER_OF_BOOKS, len(books_content))
            for book_content in books_content[:n]:
                book_info.append({})
                book_info[-1]["title"] = book_content.find("span", {"itemprop" : "name"}).string
                book_info[-1]["author"] = book_content.find("a", { "class" : "authorName" }).span.string
                book_info[-1]["rating"] = book_content.find("span", {"class": "minirating"}).contents[-1][1:5]
                book_info[-1]["link"] = "https://www.goodreads.com" + book_content.find("a")["href"] +"&ac=1"
                request_text = get(book_info[-1]["link"]).text
                soup = BeautifulSoup(request_text, "html.parser")
                soup = soup.find("div", {"id":"description"})
                # check that the description exists
                if soup:
                    description_html = str(soup.findAll("span")[-1])
                    book_info[-1]["description"] = description_html
                else:
                    book_info[-1]["description"] = "No description found."
            books_info.append(book_info)
        else:
            books_info.append(False)

    return(books_info)

def get_authors_info(search_strings):
    # parses goodread for info about books
    books_info = []
    authors_info = []
    for search_string in search_strings:
        request_text = get(SEARCH_URL + search_string,
                           headers={'User-Agent': 'BookBot-Agent'}).text
        if '<h3 class="searchSubNavContainer">No results.</h3>' not in request_text:
            books_content = []
            book_info = []
            soup = BeautifulSoup(request_text, "html.parser")
            authors_info.append({})

            # go to the first author page
            authors_info[-1]["link"] = soup.find("a", {"class":"authorName"})["href"]
            request_text = get(soup.find("a", {"class":"authorName"})["href"]).text
            soup = BeautifulSoup(request_text, "html.parser")
            books_content = soup.findAll("tr", {"itemtype":"http://schema.org/Book"})

            authors_info[-1]["link"] = soup.find("a", {"class":"authorName"})["href"]
            authors_info[-1]["author"] = soup.find("a", {"class":"authorName"}).span.text
            # get description
            description_id = "freeTextauthor"+authors_info[-1]["link"].split("/")[-1].split(".")[0]
            description_html = soup.find("span", id=description_id)
            if not description_html:
                description_id = "freeTextContainerauthor"+authors_info[-1]["link"].split("/")[-1].split(".")[0]
                description_html = soup.find("span", id=description_id)
            if not description_html:
                description_html = "No biography."
            description_html = str(description_html)
            authors_info[-1]["description"] = description_html

            # Avoid (books_info[-1]["link"]).text trying to read more books than exist
            n = min(NUMBER_OF_BOOKS_AUTHOR, len(books_content))
            for book_content in books_content[:n]:
                book_info.append({})
                book_info[-1]["title"] = book_content.find("span", {"itemprop" : "name"}).string
                book_info[-1]["author"] = authors_info[-1]["author"]
                book_info[-1]["rating"] = book_content.find("span", {"class": "minirating"}).contents[-1][1:5]
                book_info[-1]["link"] = "https://www.goodreads.com" + book_content.find("a")["href"] +"&ac=1"
                request_text = get(book_info[-1]["link"]).text
                soup = BeautifulSoup(request_text, "html.parser")

            books_info.append(book_info)
        else:
            books_info.append(False)
            authors_info.append(False)
    return(books_info, authors_info)
