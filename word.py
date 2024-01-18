import requests
from bs4 import BeautifulSoup


def get_word_of_the_day():
    url = "https://www.merriam-webster.com/word-of-the-day/"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")

        word = soup.h2.text

        description_container = soup.find("div", class_="wod-definition-container")

        desc = description_container.find("p").text.strip()

        content = {}
        content["word"] = word
        content["description"] = desc

        return content

    else:
        return None
