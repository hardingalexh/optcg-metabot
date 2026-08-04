## get leaders from the limitless tcg API

import json

import requests

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

    ## OP-17 shim
    op17_leaders = [
        {"card_id": "OP17-001", "set": "OP17", "name": "Edward.Newgate"},
        {"card_id": "OP17-020", "set": "OP17", "name": "Shanks"},
        {"card_id": "OP17-039", "set": "OP17", "name": "Rocks.D.Xebec"},
        {"card_id": "OP17-058", "set": "OP17", "name": "Kaido"},
        {"card_id": "OP17-079", "set": "OP17", "name": "Monkey.D.Luffy"},
        {"card_id": "OP17-099", "set": "OP17", "name": "Charlotte LinLin"},
    ]
    leaders += op17_leaders
    with open("leaders.json", "w") as jsonfile:
        json.dump(leaders, jsonfile, indent=2)


if __name__ == "__main__":
    scrape()
