## get leaders from the limitless tcg API

import requests
import json

LEADERS_QUERY = (
    "https://onepiece.limitlesstcg.com/api/dm/search?q=%20category%3Aleader&lang=en"
)


def fetch_leaders():
    return requests.get(LEADERS_QUERY).json()


def dedupe_leaders(leaders):
    return [leader for leader in leaders if not leader.get("variant", False)]


def fill_leaders(leaders):
    out = []
    for leader in leaders:
        url = f"https://onepiece.limitlesstcg.com/api/dm/cards?q={leader.get('card_id')}~0&lang=en"
        request = requests.get(url).json()[0]
        out.append(request)
    return out


def scrape():
    leaders = dedupe_leaders(fetch_leaders())
    leaders = fill_leaders(leaders)
    with open("leaders.json", "w") as jsonfile:
        json.dump(leaders, jsonfile)
