import requests
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import discord
from datetime import datetime
from PIL import Image
from io import BytesIO

test_strings = ["09 Roger", "OP16 Galdino", "OP14 Nami", "OP-09 Luffy", "07 Foxy"]
text_card_search_url = "https://onepiece.limitlesstcg.com/api/dm/search?lang=en&q="


def parse_set(set_str):
    ## accepted formats are OP01, 01, OP-01
    set_str = set_str.replace("-", "")
    if len(set_str) == 2:
        set_str = f"OP{set_str}"
    if len(set_str) != 4:
        pass
        ## we should error here
    return set_str.capitalize()


def get_card_numbers(param: str) -> list[str]:
    """for a given discord input, fetch the card numbers from limitless with version tag

    Args:
        param (str): _description_

    Returns:
        list[str]: _description_
    """
    set_str, card_name = param.split(" ")
    set_str = parse_set(set_str)
    search_param = f"{text_card_search_url}{card_name}%20"
    request = requests.get(search_param)
    response = request.json()

    ## needs error handling
    def get_card_base(card):
        return set_str in card.get("card_id", "")

    base_cards = list(filter(get_card_base, response))

    def format_with_variant(card):
        return f"{card.get('card_id')}~{card.get('variant')}"

    return [format_with_variant(card) for card in base_cards]


def get_limitless_id(card: str) -> int:
    """for a list of card numbers with version attached, return their card ids for limitless

    Args:
        cards (list[str]): list of card strings

    Returns:
        list[int]: card ids
    """
    card_search_url = "https://onepiece.limitlesstcg.com/api/dm/cards?lang=en&q="
    # cards_string = "%2C".join(cards)
    request = requests.get(f"{card_search_url}{card}")
    response = request.json()
    return [card.get("id") for card in response][0]


def get_prices(card: str) -> list[list[int, int]]:
    """fetches the card prices for a given card

    Args:
        card (str): card id

    Returns:
        list[list[int, int]]: price history
    """
    prices_url = f"https://onepiece.limitlesstcg.com/api/cards/{card}/prices"
    r = requests.get(prices_url)
    return r.json()


def generate_card_visualization(
    card_id: int, card_image_url: str, card_prices: list[list[int, int]]
) -> tuple[discord.File, discord.Embed]:
    """Generates a visualization of the card image and price history

    Args:
        card_id (int): the card id
        card_image_url (str): the image url for the card
        card_prices (list[list[int, int]]): the card price history

    Returns:
        tuple[discord.File, discord.Embed]: the discord output
    """

    timestamps = [
        datetime.fromtimestamp(item[0] / 1000) or None for item in card_prices
    ]
    prices = [item[1] / 100.0 for item in card_prices]
    latest_price = prices[-1] if prices else 0.0

    fig = plt.figure(figsize=(12, 4), constrained_layout=True)
    ax_image = fig.add_axes([0.02, 0.05, 0.28, 0.9])
    ax_chart = fig.add_axes([0.38, 0.1, 0.58, 0.8])

    image_response = requests.get(card_image_url)
    if not image_response.ok:
        image_response = requests.get(card_image_url.replace("EN", "JP"))
    image = Image.open(BytesIO(image_response.content)).convert("RGB")
    ax_image.imshow(image)
    ax_image.axis("off")
    ax_image.text(
        0.5,
        -0.08,
        f"${latest_price:.2f}",
        transform=ax_image.transAxes,
        ha="center",
        va="top",
        fontsize=32,
        color="black",
    )

    ax_chart.plot(timestamps, prices, color="tab:blue", marker="o", linewidth=2)
    ax_chart.set_title("Price History")
    ax_chart.set_xlabel("Date")
    ax_chart.set_ylabel("Price ($)")
    ax_chart.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"${value:.2f}"))
    ax_chart.tick_params(axis="y", pad=6)
    plt.setp(ax_chart.get_xticklabels(), rotation=45, ha="right")

    ax_chart.grid(True, alpha=0.3)
    return format_for_discord(card_id, fig)


def format_for_discord(card_id: int, fig: plt) -> tuple[discord.File, discord.Embed]:
    """Formats the image into a discord embed using local attachments

    Args:
        card_id (int): card id
        fig (plt): matplotlib figure

    Returns:
        tuple[discord.File, discord.Embed]: file and embed ready for sending
    """
    output_path = f"{card_id}.png"
    fig.savefig(output_path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    file = discord.File(output_path, filename=f"{card_id}.png")
    embed = discord.Embed()
    embed.set_image(url=f"attachment://{card_id}.png")
    return (file, embed)


def get_images(param):
    base_cards = get_card_numbers(param)
    images = []
    for x, card_id in enumerate(base_cards):
        limitless_id = get_limitless_id(card_id)
        card_prices = get_prices(limitless_id)
        img_url = "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece"
        set_str = card_id.split("~")[0]
        set_str = set_str.split("-")[0]
        card_id_f = f"{card_id.replace('~', '_p').replace('_p0', '')}_EN"
        card_image_url = f"{img_url}/{set_str}/{card_id_f}.webp"
        card_prices_tcgp = card_prices.get("tcgplayer")
        images.append(
            generate_card_visualization(card_id, card_image_url, card_prices_tcgp)
        )
    return images
