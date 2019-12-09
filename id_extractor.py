from furl import furl


def extract_pixiv_id(info):
    url = furl(info["url"])
    if "illust_id" in url.query.params:
        return "art", url.query.params["illust_id"]
    elif "artworks" in str(url.path):
        return "art", str(url.path).split("/")[-1]
    elif id in url.query.params:
        return "artist", url.query.params["id"]
    else:
        return "other", info["url"]


def extract_twitter_id(info):
    url = furl(info["url"])


def extract_image_ids():
    pass


if __name__ == "__main__":
    pass
