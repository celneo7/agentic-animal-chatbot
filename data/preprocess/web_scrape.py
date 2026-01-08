import requests
from bs4 import BeautifulSoup
import os
import re


animals = ['cat','dog', 'elephant']

headers = {
    "User-Agent": "AnimalRag/0.1/(https://github.com/celneo7/agentic-animal-chatbot)"
}


# helper function to preprocess text
def clean_header(text):
    return re.sub(r"\[.*?\]", "", text).strip()


def clean_text(text):
    text = re.sub(r"\[.*?\]", "", text)   # citations
    text = re.sub(r"\s+", " ", text)
    return text.strip()



for a in animals:
    # get URL
    page = requests.get(f'https://en.wikipedia.org/wiki/{a}', headers=headers)

    # scrape data
    scrape = BeautifulSoup(page.content, 'html.parser')

    # get relevant data and preprocess
    content = scrape.find("div", {"id": "mw-content-text"})
    title = scrape.find("h1").get_text(strip=True)

    output = []
    output.append(f"# {title}\n")

    for el in content.find_all(["h2", "h3", "p", "ul"]):
        if el.name == "h2":
            header = clean_header(el.get_text())
            output.append(f"\n## {header}\n")

        elif el.name == "h3":
            header = clean_header(el.get_text())
            output.append(f"\n### {header}\n")

        elif el.name in ["p", "ul"]:
            text = clean_text(el.get_text())
            if len(text) > 40:
                output.append(text + "\n")

    
    

    # save to file
    with open(os.curdir + f'/data/{a}_wiki.txt', 'w', encoding='utf-8') as f:
        f.write("\n".join(output))