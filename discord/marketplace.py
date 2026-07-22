import requests
import matplotlib.pyplot as plt
from datetime import datetime
from PIL import Image
from io import BytesIO

test_strings = ["09 Roger", "OP16 Galdino", "OP14 Nami", "OP-09 Luffy", "07 Foxy"]

# card_search_url = "https://onepiece.limitlesstcg.com/api/dm/cards?lang=en&q="
## card search format = OPXX-YYY

text_card_search_url = "https://onepiece.limitlesstcg.com/api/dm/search?lang=en&q="


def parse_set(set_str):
    ## accepted formats are OP01, 01, OP-01
    set_str = set_str.replace("-", "")
    if len(set_str) == 2:
        set_str = f"OP{set_str}"
    if len(set_str) != 4:
        pass
        ## we should error here
    return set_str


def get_card_numbers(param):
    set_str, card_name = param.split(" ")
    set_str = parse_set(set_str)
    search_param = f"{text_card_search_url}{card_name}%20!set%3A{set_str}"
    request = requests.get(search_param)
    response = request.json()

    ## needs error handling
    def get_card_base(card):
        return card.get("set", "") == set_str

    base_cards = list(filter(get_card_base, response))

    def format_with_variant(card):
        return f"{card.get('card_id')}~{card.get('variant')}"

    return [format_with_variant(card) for card in base_cards]


def get_limitless_ids(cards):
    card_search_url = "https://onepiece.limitlesstcg.com/api/dm/cards?lang=en&q="
    cards_string = "%2C".join(cards)
    request = requests.get(f"{card_search_url}{cards_string}")
    response = request.json()
    return [card.get("id") for card in response]


def get_prices(card):
    prices_url = f"https://onepiece.limitlesstcg.com/api/cards/{card}/prices"
    r = requests.get(prices_url)
    return r.json()


def format_cents(value):
    dollars = float(value) / 100.0
    return f"${dollars:.2f}"


def generate_card_visualization(card_image_url, card_prices):
    timestamps = [
        datetime.fromtimestamp(item[0] / 1000) or None for item in card_prices
    ]
    prices = [item[1] / 100.0 for item in card_prices]

    fig = plt.figure(figsize=(12, 4), constrained_layout=True)
    ax_image = fig.add_axes([0.0, 0.0, 1.0 / 3.0, 1.0])
    ax_chart = fig.add_axes([1.0 / 3.0, 0.0, 2.0 / 3.0, 1.0])

    image_response = requests.get(card_image_url)
    image = Image.open(BytesIO(image_response.content)).convert("RGB")
    ax_image.imshow(image)
    ax_image.axis("off")

    ax_chart.plot(timestamps, prices, color="tab:blue", marker="o", linewidth=2)
    ax_chart.set_title("Price History")
    ax_chart.set_xlabel("Date")
    ax_chart.set_ylabel("Price ($)")
    plt.setp(ax_chart.get_xticklabels(), rotation=45, ha="right")
    ax_chart.grid(True, alpha=0.3)

    output_path = "card_price_history.png"
    fig.savefig(output_path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    return output_path


for param in test_strings:
    base_cards = get_card_numbers(param)
    limitless_ids = get_limitless_ids(base_cards)
    for x, card_id in enumerate(base_cards):
        img_url = "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece"
        set_str = card_id.split("~")[0]
        set_str = set_str.split("-")[0]
        card_id = f"{card_id.replace('~', '_p').replace('_p0', '')}_EN"
        card_image_url = f"{img_url}/{set_str}/{card_id}.webp"
        card_prices = get_prices(limitless_ids[x])
        card_prices_tcgp = card_prices.get("tcgplayer")
        generate_card_visualization(card_image_url, card_prices_tcgp)
