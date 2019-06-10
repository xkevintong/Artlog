import json

from bs4 import BeautifulSoup
import requests
from tldextract import extract


def request_url_from_div(div):
    # Check for class="touchable _4qxt" 's href, which should be most links?
    if div.find(class_='touchable _4qxt') is not None:
        url = div.find(class_='touchable _4qxt')['href']
        response = requests.get(url)
        response_soup = BeautifulSoup(response.content, 'html.parser')

        # Facebook's redirection page for websites outside their domain
        return response_soup.find('span', class_='_5slv').get_text()


def get_url_from_msg(msg):
    # Check for class="touchable _4qxt" 's href, which should be most links?
    if msg.div.span.a is not None:
        return "".join(msg.div.span.a.find_all(text=True))

    # Facebook page
    elif msg.find(class_="story_body_container") is not None:
        return msg.find(class_="_39pi")["href"]

    return None


def parse():
    links_file = open('links.json', 'w', encoding='utf8')
    scratch = open('scratch.txt', 'w', encoding='utf8')

    soup = BeautifulSoup(open('tini.html', encoding='utf8'), 'html.parser')
    message_group = soup.find('div', {'id': 'messageGroup'})
    msgs = message_group.find_all('div', class_='msg')

    num_divs = 0
    valid_domains = ["pixiv", "twitter", "reddit", "artstation", "deviantart"]
    links = {}
    for domain in valid_domains:
        links[domain] = []

    # "misc" is not a valid domain, but will collect
    links["misc"] = []

    for i, msg in enumerate(msgs):
        num_divs += 1
        scratch.write(msg.prettify())

        # Write to json, then write once to file
        url = get_url_from_msg(msg)
        if url:
            domain = extract(url).domain
            if domain in valid_domains:
                links[domain].append(url)
            else:
                links["misc"].append(url)
        else:
            print("Nothing extracted from div")
            print(msg.prettify())

    json.dump(links, links_file, indent=4)

    # Check for links to facebook pages
    # Look for story_body_container

    # Check for raw images

    # Text messages have content within span

    # Everything else should go in some Misc. section
    # is there really a misc section if i have to know how to pull the url
    # really just a have to sort manually section

    if i+1 != num_divs:
        print(f'{num_divs-i-1} messages were not correctly processed')


if __name__ == "__main__":
    parse()
