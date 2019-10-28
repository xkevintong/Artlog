import json

from bs4 import BeautifulSoup
import requests
from tldextract import extract
import arrow # todo: change to pendulum
import pendulum


def request_url_from_div(url):
    response = requests.get(url)
    response_soup = BeautifulSoup(response.content, "html.parser")

    # Facebook's redirection page for websites outside their domain
    redirected_domain = response_soup.find("span", class_="_5slv")
    if redirected_domain:
        return redirected_domain.get_text()
    else:
        # TODO: search text for "The link you tried to visit goes against
        # our Community Standards."
        print(response_soup.prettify())
        return f"something went wrong, banned image??: {url}"


def get_url_from_msg(msg, domains):
    url_list =[]
    # Get all touchable links
    touch_links = msg.find_all(class_="touchable _4qxt")
    # todo: try removing the if
    if touch_links:
        for link in touch_links:
            url_list.append(request_url_from_div(link["href"]))

    # Checks for a hyperlink in raw text
    # This only produces duplicates, probably hyperlink without touchable link
    # if msg.div.span.a is not None:
    #     url_list.append("".join(msg.span.a.find_all(text=True)))

    # Facebook pages
    fb_pages = msg.find_all(class_="_39pi")
    # todo: try removing the if
    if fb_pages:
        for link in fb_pages:
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


def parse_html():
    links_file = open("links_messenger.json", "w", encoding="utf8")
    # scratch = open("scratch.txt", "w", encoding="utf8")

    soup = BeautifulSoup(open("messenger/smol.html", encoding="utf8"), "html.parser")
    message_group = soup.find("div", {"id": "messageGroup"})
    msgs = message_group.find_all("div", class_="c")

    num_divs = 0
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

    for i, msg in enumerate(msgs):
        num_divs += 1
        # scratch.write(msg.prettify())
        msg_time = get_time_from_msg(msg.div.next_sibling)
        for url in get_url_from_msg(msg.div, valid_domains):
            info = {
                "url": url,
                "time": msg_time,
            }

            if info["url"]:
                domain = extract(info["url"]).domain
                if domain in valid_domains:
                    links[domain].append(info)
                else:
                    links["misc"].append(info)
            else:
                print("Nothing extracted from div, probably a raw image")
                print(msg.prettify())
                links["message"].append(info)

    json.dump(links, links_file, indent=4)

    # TODO: count number of possible raw images

    # Everything else should go in some Misc. section
    # is there really a misc section if i have to know how to pull the url
    # really just a have to sort manually section

    # todo: fix or remove this check
    if i + 1 != num_divs:
        print(f"{num_divs-i-1} messages were not correctly processed")
    else:
        print("All messages processed correctly!")


if __name__ == "__main__":
    parse_html()
