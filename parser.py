import json

from bs4 import BeautifulSoup
import requests
from tldextract import extract
import arrow
import tweepy

from credentials import *


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

    soup = BeautifulSoup(open('messenger/smol.html', encoding='utf8'), 'html.parser')
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

    # Everything else should go in some Misc. section
    # is there really a misc section if i have to know how to pull the url
    # really just a have to sort manually section

    if i+1 != num_divs:
        print(f'{num_divs-i-1} messages were not correctly processed')
    else:
        print("All messages processed correctly!")


def twitter_auth():
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    return tweepy.API(auth)


def twitter_test():
    api = twitter_auth()
    # single image, multiple image, link, text
    list = [1149892112973877248, 1149589694662840322]
    for id in list:
        status = api.get_status(id)
        # print(status)
        print(json.dumps(status._json, indent=4))


def _requests_twitter_download(tweet_url):
    response = requests.get(tweet_url)
    response_soup = BeautifulSoup(response.content, 'html.parser')
    image_source_div = response_soup.find('div', class_='AdaptiveMedia-photoContainer js-adaptive-photo')
    if image_source_div:
        image_source = image_source_div['data-image-url']
        image_name = image_source.rsplit('/', 1)[-1]

        # The large image's path can be reached by appending ':large'
        image_response = requests.get(image_source + ':large')
        with open(f'images\{image_name}', 'wb') as file:
            file.write(image_response.content)
        return 'Success', image_source
    else:
        print("Image failed to download: " + tweet_url)
        return 'Failed', None


def like_tweet(tweepy_api, tweet_id):
    tweepy_api.create_favorite(tweet_id)


def download_twitter_images():
    api = twitter_auth()
    with open('links.json') as links:
        image_status = []
        for msg in json.load(links)['twitter']:
            tweet_id = msg['url'].partition('status/')[2].partition('?')[0]
            num_media = 0
            if tweet_id:
                tweet = api.get_status(tweet_id)._json
                if not tweet['favorited']:
                    try:
                        # todo: helper func these
                        for media in tweet['extended_entities']['media']:
                            num_media += 1
                            msg['source'] = media_source = media['media_url']
                            media_name = media['media_url'].rsplit('/', 1)[-1]
                            media_response = requests.get(media_source + ':large')
                            with open(f'images\{media_name}', 'wb') as file:
                                file.write(media_response.content)
                            print(media['media_url'])
                    except KeyError:
                        pass
                    # Also check to see if a tweet was quoted
                    try:
                        for media in tweet['quoted_status']['extended_entities']['media']:
                            num_media += 1
                            msg['source'] = media_source = media['media_url']
                            media_name = media['media_url'].rsplit('/', 1)[-1]
                            media_response = requests.get(media_source + ':large')
                            with open(f'images\{media_name}', 'wb') as file:
                                file.write(media_response.content)
                            print(media['media_url'])
                    except KeyError:
                        pass

                    # Like the tweet after downloading
                    msg['already_liked'] = False
                    if num_media > 0:
                        like_tweet(api, tweet_id)

                else:
                    num_media = -1
                    msg['already_liked'] = True
            else:
                msg['error'] = "Not a tweet"
            msg['num_media'] = num_media
            # msg['status'], msg['source'] = _requests_twitter_download(msg['url'])
            msg['id'] = tweet_id
            msg['time'] = arrow.now('US/Pacific').format('YYYY-MM-DD HH:mm')
            image_status.append(msg)

    with open('twitter.json', 'w') as twitter:
        json.dump(image_status, twitter, indent=4)


def download_pixiv_images():
    pass


def download_images():
    download_twitter_images()
    download_pixiv_images()


if __name__ == "__main__":
    # parse_html()
    download_images()
