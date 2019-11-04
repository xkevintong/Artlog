import json

from pixivpy3 import *

from credentials import pixiv_username, pixiv_password

# get image id from pixiv json
# determine if its a single image or an album and get the original urls
# download the images
# like the work
# check if artist is followed?


def test():
    api = AppPixivAPI()
    api.login(pixiv_username, pixiv_password)
    json_result = api.illust_detail(69232275)
    print(json.dumps(json_result, indent=4))
    urls = []
    for page in json_result["illust"]["meta_pages"]:
        print(page["image_urls"]["original"])
        urls.append(page["image_urls"]["original"])

    for url in urls:
        api.download(url, path="images")


if __name__ == "__main__":
    test()
