import json

from bs4 import BeautifulSoup
import requests
import tweepy
import arrow # change to pendulum

from credentials import consumer_key, consumer_secret, access_token, access_token_secret


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
    response_soup = BeautifulSoup(response.content, "html.parser")
    image_source_div = response_soup.find(
        "div", class_="AdaptiveMedia-photoContainer js-adaptive-photo"
    )
    if image_source_div:
        image_source = image_source_div["data-image-url"]
        image_name = image_source.rsplit("/", 1)[-1]

        # The large image's path can be reached by appending ':large'
        image_response = requests.get(image_source + ":large")
        with open(f"images\{image_name}", "wb") as file:
            file.write(image_response.content)
        return "Success", image_source
    else:
        print("Image failed to download: " + tweet_url)
        return "Failed", None


def like_tweet(tweepy_api, tweet_id):
    tweepy_api.create_favorite(tweet_id)


def download_twitter_images():
    api = twitter_auth()
    # todo: move logic for pulling twitter and pixiv somewhere else
    with open("links_messenger.json") as links:
        image_status = []
        for msg in json.load(links)["twitter"]:
            tweet_id = msg["url"].partition("status/")[2].partition("?")[0]
            num_media = 0
            if tweet_id:
                tweet = api.get_status(tweet_id)._json
                if not tweet["favorited"]:
                    try:
                        # todo: helper func these
                        for media in tweet["extended_entities"]["media"]:
                            num_media += 1
                            msg["source"] = media_source = media["media_url"]
                            media_name = media["media_url"].rsplit("/", 1)[-1]
                            media_response = requests.get(media_source + ":large")
                            with open(f"images\{media_name}", "wb") as file:
                                file.write(media_response.content)
                            print(media["media_url"])
                    except KeyError:
                        # todo: do something here?
                        pass
                    # Also check to see if a tweet was quoted
                    try:
                        for media in tweet["quoted_status"]["extended_entities"][
                            "media"
                        ]:
                            num_media += 1
                            msg["source"] = media_source = media["media_url"]
                            media_name = media["media_url"].rsplit("/", 1)[-1]
                            media_response = requests.get(media_source + ":large")
                            with open(f"images\{media_name}", "wb") as file:
                                file.write(media_response.content)
                            print(media["media_url"])
                    except KeyError:
                        pass

                    # Like the tweet after downloading
                    msg["already_liked"] = False
                    if num_media > 0:
                        like_tweet(api, tweet_id)

                else:
                    num_media = -1
                    msg["already_liked"] = True
            else:
                msg["error"] = "Not a tweet"
            msg["num_media"] = num_media
            # msg['status'], msg['source'] = _requests_twitter_download(msg['url'])
            msg["id"] = tweet_id
            msg["time_downloaded"] = arrow.now("US/Pacific").format("YYYY-MM-DD HH:mm")
            image_status.append(msg)

    with open("twitter.json", "w") as twitter:
        json.dump(image_status, twitter, indent=4)