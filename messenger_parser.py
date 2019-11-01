import json
import os

from bs4 import BeautifulSoup
import requests
from tldextract import extract
import arrow # todo: change to pendulum
import pendulum


def request_facebook_url(url):
    response = requests.get(url)
    response_soup = BeautifulSoup(response.content, "html.parser")

    # Facebook's redirection page for websites outside their domain
    redirected_domain = response_soup.find("span", class_="_5slv")
    if redirected_domain:
        return redirected_domain.get_text()
    else:
        # TODO: search text for "The link you tried to visit goes against
        # our Community Standards."
        print("Something went wrong, banned image?")
        print(response_soup.prettify())
        return f"something went wrong, banned image??: {url}"


def get_url_from_msg(msg):
    url_list =[]
    # Get all touchable links
    for link in msg.find_all(class_="touchable _4qxt"):
        url_list.append(link["href"])

    # Checks for a hyperlink in raw text
    # This only produces duplicates, probably hyperlink without touchable link
    # if msg.div.span.a is not None:
    #     url_list.append("".join(msg.span.a.find_all(text=True)))

    # Facebook pages
    for link in msg.find_all(class_="_39pi"):
        url_list.append(link["href"])

    # Dump text if nothing matches
    if not url_list:
        return [" ".join(msg.find_all(text=True))]

    return url_list


def get_time_from_msg(div):
    if div.find("abbr"):
        unix_time = json.loads(div.find("abbr")["data-store"])["time"]
        time = arrow.Arrow.fromtimestamp(unix_time)
        return time.to("US/Pacific").format("YYYY-MM-DD HH:mm")


def sort_domains():
    valid_domains = [
        "pixiv",
        "twitter",
        "reddit",
        "artstation",
        "deviantart",
        "facebook",
    ]

    links = {}
    for domain in valid_domains:
        links[domain] = []

    # All other domains fall under misc, text messages fall under messages
    invalid_ = ["misc", "message"]
    for key in invalid_:
        links[key] = []

    # if info["url"]:
    #     domain = extract(info["url"]).domain
    #     if domain in valid_domains:
    #         links[domain].append(info)
    #     else:
    #         links["misc"].append(info)
    # else:
    #     print("Nothing extracted from div, probably a raw image")
    #     print(msg.prettify())
    #     links["message"].append(info)


def extract_links_from_html(html_file):
    raw_links_file = open(f"raw/links_messenger_{pendulum.now().format('YYYY-MM-DD_HHmm')}.json", "w", encoding="utf8")
    # scratch = open("scratch.txt", "w", encoding="utf8")

    soup = BeautifulSoup(open(html_file, encoding="utf8"), "html.parser")
    message_group = soup.find("div", {"id": "messageGroup"})
    msgs = message_group.find_all("div", class_="c")

    raw_links = []
    num_divs = 0

    for i, msg in enumerate(msgs):
        num_divs += 1
        # scratch.write(msg.prettify())
        msg_time = get_time_from_msg(msg.div.next_sibling)
        for url in get_url_from_msg(msg.div):
            info = {
                "url": url,
                "time": msg_time,
            }

            raw_links.append(info)

    json.dump(raw_links, raw_links_file, indent=4)

    # TODO: count number of possible raw images

    # todo: fix or remove this check
    if i + 1 != num_divs:
        print(f"{num_divs-i-1} messages were not correctly processed")
    else:
        print("All messages processed correctly!")


def remove_link_shim():
    for file in [f for f in os.listdir('raw/') if os.path.isfile(os.path.join('raw/', f))]:
        clean_list = []
        with open(f"raw/{file}") as raw_file:
            raw_list = json.load(raw_file)
            for raw_info in raw_list:
                if extract(raw_info["url"]).subdomain == "lm":
                    clean_info = {"url": request_facebook_url(raw_info["url"]),
                                  "time": raw_info["time"]}
                    clean_list.append(clean_info)
                else:
                    clean_list.append(raw_info)

        with open(f"clean/{file}", "w") as clean_file:
            if len(raw_list) == len(clean_list):
                json.dump(clean_list, clean_file, indent=4)
            else:
                print("Something went wrong with removing link shim.")


if __name__ == "__main__":
    extract_links_from_html("messenger/smol.html")
    remove_link_shim()

