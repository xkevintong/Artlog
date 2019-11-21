import json
import os
import re

from bs4 import BeautifulSoup
import requests
from tldextract import extract
import arrow  # todo: change to pendulum
import pendulum


def request_facebook_url(url):
    response = requests.get(url)
    response_soup = BeautifulSoup(response.content, "html.parser")

    # Facebook's redirection page for websites outside their domain
    redirected_domain = response_soup.find("span", class_="_5slv")
    script_url = response_soup.find(
        "script", text=re.compile("^document.location.replace")
    )
    fb_community_standards = response_soup.find(class_="mvm uiP fsm")

    if redirected_domain:
        return False, redirected_domain.get_text()
    elif script_url:
        # Clean up url from script
        return False, script_url.text.split('"')[1]
    elif fb_community_standards:
        if (
            fb_community_standards.a["href"]
            == "https://www.facebook.com/communitystandards"
        ):
            return True, url
    else:
        print("Something went wrong")
        print(response_soup.prettify())
        return True, f"ERROR: {url}"


def get_url_from_msg(msg):
    url_list = []
    # Get all touchable links
    for link in msg.find_all(class_="touchable _4qxt"):
        url_list.append(link["href"])

    # Facebook pages
    for link in msg.find_all(class_="_5msj"):
        url_list.append(link["href"])

    # If nothing matches, check if raw text has a link, otherwise dump text
    if not url_list:
        if msg.div.span.a is not None:
            url_list.append("".join(msg.span.a.find_all(text=True)))
        else:
            return [" ".join(msg.find_all(text=True))]

    return url_list


def get_time_from_msg(div):
    if div.find("abbr"):
        unix_time = json.loads(div.find("abbr")["data-store"])["time"]
        time = arrow.Arrow.fromtimestamp(unix_time)
        return time.to("US/Pacific").format("YYYY-MM-DD HH:mm")


def extract_links_from_html(html_file):
    raw_links_file = open(
        f"raw/links_messenger_{pendulum.now().format('YYYY-MM-DD_HHmm')}.json",
        "w",
        encoding="utf8",
    )

    soup = BeautifulSoup(open(html_file, encoding="utf8"), "html.parser")
    message_group = soup.find("div", {"id": "messageGroup"})
    msgs = message_group.find_all("div", class_="c")

    raw_links = []

    for msg in msgs:
        msg_time = get_time_from_msg(msg.div.next_sibling)
        for url in get_url_from_msg(msg.div):
            info = {"url": url, "time": msg_time}

            raw_links.append(info)

    json.dump(raw_links, raw_links_file, indent=4)


def remove_link_shim(read_all_files):
    file_list = [
        f for f in os.listdir("raw/") if os.path.isfile(os.path.join("raw/", f))
    ]
    if not read_all_files:
        file_list = [max(["raw/" + file for file in file_list], key=os.path.getctime)]

    for file in file_list:
        clean_list = []
        with open(file) as raw_file:
            raw_list = json.load(raw_file)
            for i, raw_info in enumerate(raw_list, start=1):
                if extract(raw_info["url"]).subdomain == "lm":
                    status, url = request_facebook_url(raw_info["url"])
                    clean_info = {
                        "url": url,
                        "time": raw_info["time"],
                        "banned": status,
                    }
                    clean_list.append(clean_info)
                else:
                    raw_info["banned"] = False
                    clean_list.append(raw_info)
                print(f"{i}/{len(raw_list)}")

        # Remove 'raw/' prefix
        with open(f"clean/{file[4:]}", "w") as clean_file:
            if len(raw_list) == len(clean_list):
                json.dump(clean_list, clean_file, indent=4)
            else:
                print("Something went wrong with removing link shim.")


def expand_twitter_links():
    expanded_list = []
    file_list = [
        f for f in os.listdir("clean/") if os.path.isfile(os.path.join("clean/", f))
    ]
    file = max(["clean/" + file for file in file_list], key=os.path.getctime)
    with open(file) as clean_file:
        clean_list = json.load(clean_file)
        for i, clean_info in enumerate(clean_list, start=1):
            url_extract = extract(clean_info["url"])
            if url_extract.domain == "t" and url_extract.suffix == "co":
                response = requests.get(clean_info["url"])
                if response.status_code == 200:
                    clean_info["deleted"] = False
                else:
                    clean_info["deleted"] = True
                clean_info["url"] = response.url
            else:
                clean_info["deleted"] = False
            expanded_list.append(clean_info)
            print(f"{i}/{len(clean_list)}")

        # Remove 'clean/' prefix
        with open(f"clean_twitter_links/{file[6:]}", "w") as expanded_file:
            json.dump(expanded_list, expanded_file, indent=4)


def sort_domains(read_all_files):
    valid_domains = [
        "pixiv",
        "twitter",
        "reddit",
        "artstation",
        "deviantart",
        "facebook",
    ]

    other_buckets = ["misc", "message", "banned", "deleted_tweet", "raw_images"]

    file_list = [
        f
        for f in os.listdir("clean_twitter_links/")
        if os.path.isfile(os.path.join("clean_twitter_links/", f))
    ]
    if not read_all_files:
        file_list = [
            max(
                ["clean_twitter_links/" + file for file in file_list],
                key=os.path.getctime,
            )
        ]

    for file in file_list:
        links = {}
        for domain in valid_domains:
            links[domain] = []

        # All other domains fall under misc, text messages fall under messages
        for key in other_buckets:
            links[key] = []

        with open(file) as clean_file:
            clean_list = json.load(clean_file)
            for i, clean_info in enumerate(clean_list):
                # Pop both keys and check if URL is deleted or banned before sorting
                # A URL cannot be both deleted and banned
                deleted = clean_info.pop("deleted")
                banned = clean_info.pop("banned")
                if deleted:
                    links["deleted_tweet"].append(clean_info)
                elif banned:
                    links["banned"].append(clean_info)
                elif clean_info["url"]:
                    url_extract = extract(clean_info["url"])
                    if url_extract.domain in valid_domains:
                        links[url_extract.domain].append(clean_info)
                    # Append facebook domain to its pages
                    elif clean_info["url"][:6] in ("/story", "/group"):
                        clean_info["url"] = "https://facebook.com" + clean_info["url"]
                        links["facebook"].append(clean_info)
                    elif clean_info["url"][:4] == "http":
                        links["misc"].append(clean_info)
                    else:
                        message = (
                            clean_info.pop("url").replace("Kevin Tong", "").strip()
                        )
                        if message:
                            clean_info["message"] = message
                            links["message"].append(clean_info)
                        else:
                            links["raw_images"].append({"time": clean_info["time"]})
                else:
                    print("Nothing extracted from div?")
                    links["message"].append(clean_info)

                print(f"{i}/{len(clean_list)}")

        # Remove 'clean/' prefix
        with open(f"sorted/{file[19:]}", "w") as sorted_file:
            json.dump(links, sorted_file, indent=4)


if __name__ == "__main__":
    ALL_FILES = False
    print("Beginning extraction.")
    extract_links_from_html("messenger/part2.html")
    print("Extraction finished. Removing link shim.")
    remove_link_shim(ALL_FILES)
    print("Link shim removed. Expanding twitter links.")
    expand_twitter_links()
    print("Twitter links expanded. Sorting domains.")
    sort_domains(ALL_FILES)
