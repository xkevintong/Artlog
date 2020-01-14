import json

import utils

from furl import furl


def extract_pixiv_id(info):
    if "url" in info:
        url = furl(info["url"])
        if "illust_id" in url.query.params:
            return "art", int(url.query.params["illust_id"])
        elif "artworks" in str(url.path):
            return "art", int(str(url.path).split("/")[-1])
        elif "id" in url.query.params:
            return "artist", int(url.query.params["id"])

    return "other", -1


def extract_twitter_id(info):
    if "url" in info:
        url = furl(info["url"])
        if len(url.path.segments) == 1:
            return "artist", url.path.segments[0]
        elif url.path.segments[-2] == "photo":
            return "art", int(url.path.segments[-3])
        else:
            return "art", int(url.path.segments[2])

    return "other", -1


# todo: write test for this
def extract_image_ids():
    # todo: also do the files in final folder once
    file_list = utils.get_file_list_from_folder("drive_links/")

    for file in file_list:
        with open("drive_links/" + file) as links_file:
            links_list = json.load(links_file)
            for pixiv_info in links_list["pixiv"]:
                info_type, info_id = extract_pixiv_id(pixiv_info["url"])
                pixiv_info["type"] = info_type
                pixiv_info["id"] = info_id

            for twitter_info in links_list["twitter"]:
                info_type, info_id = extract_twitter_id(twitter_info["url"])
                twitter_info["type"] = info_type
                twitter_info["id"] = info_id

        with open("id_extracted/" + file) as extracted_file:
            json.dump(links_list, extracted_file, indent=4)


if __name__ == "__main__":
    extract_image_ids()
