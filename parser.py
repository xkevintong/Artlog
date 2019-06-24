import json

from bs4 import BeautifulSoup
import requests
from tldextract import extract
import arrow


def request_url_from_div(div):
    # Check for class="touchable _4qxt" 's href, which should be most links?
    if div.find(class_='touchable _4qxt'):
        url = div.find(class_='touchable _4qxt')['href']
        response = requests.get(url)
        response_soup = BeautifulSoup(response.content, 'html.parser')

        # Facebook's redirection page for websites outside their domain
        redirected_domain = response_soup.find('span', class_='_5slv')
        if redirected_domain:
            return redirected_domain.get_text()
        else:
            # TODO: search text for "The link you tried to visit goes against
            # our Community Standards."
            print(response_soup.prettify())
            return f"something went wrong, banned image??: {url}"


def get_url_from_msg(msg, domains):
    # Check for class="touchable _4qxt" 's href, which should be most links?
    if msg.div.span.a is not None:
        return "".join(msg.div.span.a.find_all(text=True))

    # Facebook page
    elif msg.find(class_="_39pi") is not None:
        return msg.find(class_="_39pi")["href"]

    # Check if message is a box without text
    word = msg.div.find(text=True)
    if word:
        if extract(word).domain in domains:
            return request_url_from_div(msg.div)

    # Dump text if nothing matches
    return " ".join(msg.div.find_all(text=True))


def get_time_from_msg(div):
    if div.find('abbr'):
        unix_time = json.loads(div.find('abbr')['data-store'])['time']
        time = arrow.Arrow.fromtimestamp(unix_time)
        return time.to('US/Pacific').format('YYYY-MM-DD HH:mm')


def parse_html():
    links_file = open('links.json', 'w', encoding='utf8')
    scratch = open('scratch.txt', 'w', encoding='utf8')

    soup = BeautifulSoup(open('smol.html', encoding='utf8'), 'html.parser')
    message_group = soup.find('div', {'id': 'messageGroup'})
    msgs = message_group.find_all('div', class_='c')

    num_divs = 0
    valid_domains = ["pixiv", "twitter", "reddit", "artstation", "deviantart", "facebook"]
    links = {}
    for domain in valid_domains:
        links[domain] = []

    # These aren't valid domains, but will collect
    invalid_ = ["misc", "message"]
    for key in invalid_:
        links[key] = []

    for i, msg in enumerate(msgs):
        num_divs += 1
        scratch.write(msg.prettify())
        info = {
            'url': get_url_from_msg(msg.div, valid_domains),
            'time': get_time_from_msg(msg.div.next_sibling)
        }

        if info['url']:
            domain = extract(info['url']).domain
            if domain in valid_domains:
                links[domain].append(info)
            else:
                links["misc"].append(info)
        else:
            print("Nothing extracted from div, probably a raw image")
            print(msg.prettify())
            links["message"] = info

    json.dump(links, links_file, indent=4)

    # TODO: count number of possible raw images
    # Check for raw images

    # Everything else should go in some Misc. section
    # is there really a misc section if i have to know how to pull the url
    # really just a have to sort manually section

    if i+1 != num_divs:
        print(f'{num_divs-i-1} messages were not correctly processed')
    else:
        print("All messages processed correctly!")


def download_twitter_images():
    twitter_links = json.load(open('links.json'))['twitter']
    for msg in twitter_links:
        response = requests.get(msg['url'])
        response_soup = BeautifulSoup(response.content, 'html.parser')
        image_source_div = response_soup.find('div', class_='AdaptiveMedia-photoContainer js-adaptive-photo')
        if image_source_div:
            image_source = image_source_div['data-image-url']
            image_name = image_source.rsplit('/', 1)[-1]

            # The large image's path can be reached by appending ':large'
            image_response = requests.get(image_source + ':large')
            with open(f'images\{image_name}', 'wb') as file:
                file.write(image_response.content)
        else:
            print("Image failed to download: " + msg['url'])

    return None


def download_pixiv_images():
    return None


def download_images():
    download_twitter_images()
    download_pixiv_images()


if __name__ == "__main__":
    # parse_html()
    download_images()
