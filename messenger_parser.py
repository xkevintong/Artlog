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
        return True, url


def get_url_from_msg(msg):
    url_list = []
    # Get all touchable links
    for link in msg.find_all(class_="touchable _4qxt"):
        url_list.append(link["href"])

    # Checks for a hyperlink in raw text
    # This only produces duplicates, probably hyperlink without touchable link
    # if msg.div.span.a is not None:
    #     url_list.append("".join(msg.span.a.find_all(text=True)))

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

    # TODO: count number of possible raw images


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
            for raw_info in raw_list:
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

        # Remove 'raw/' prefix
        with open(f"clean/{file[4:]}", "w") as clean_file:
            if len(raw_list) == len(clean_list):
                json.dump(clean_list, clean_file, indent=4)
            else:
                print("Something went wrong with removing link shim.")


def sort_domains(read_all_files):
    valid_domains = [
        "pixiv",
        "twitter",
        "reddit",
        "artstation",
        "deviantart",
        "facebook",
    ]

    invalid_domains = ["misc", "message"]

    file_list = [
        f for f in os.listdir("clean/") if os.path.isfile(os.path.join("clean/", f))
    ]
    if not read_all_files:
        file_list = [max(["clean/" + file for file in file_list], key=os.path.getctime)]

    for file in file_list:
        links = {}
        for domain in valid_domains:
            links[domain] = []

        # All other domains fall under misc, text messages fall under messages
        for key in invalid_domains:
            links[key] = []

        # todo: add a section for banned fb links and grab before sorting
        with open(file) as clean_file:
            clean_list = json.load(clean_file)
            for clean_info in clean_list:
                # todo: double check what a raw image looks like
                if clean_info["url"]:
                    domain = extract(clean_info["url"]).domain
                    if extract(clean_info["url"]).domain in valid_domains:
                        links[domain].append(clean_info)
                    elif domain and extract(clean_info["url"]).subdomain:
                        links["misc"].append(clean_info)
                    else:
                        links["message"].append(clean_info)
                else:
                    print("Nothing extracted from div, probably a raw image")
                    links["message"].append(clean_info)

        # Remove 'clean/' prefix
        with open(f"sorted/{file[6:]}", "w") as sorted_file:
            json.dump(links, sorted_file, indent=4)


if __name__ == "__main__":
    ALL_FILES = False
    extract_links_from_html("messenger/medi.html")
    remove_link_shim(ALL_FILES)
    sort_domains(ALL_FILES)
