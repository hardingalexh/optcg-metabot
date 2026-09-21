from datetime import datetime
from io import BytesIO

import discord
import matplotlib.pyplot as plt
import requests
from matplotlib.ticker import FuncFormatter
from PIL import Image

from utils import *

test_strings = ["09 Roger", "OP16 Galdino", "OP14 Nami", "OP-09 Luffy", "07 Foxy"]


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


def get_images(param):
    base_cards = get_card_numbers(param)
    images = []
    for x, card_id in enumerate(base_cards):
        limitless_id = get_limitless_id(card_id)
        card_prices = get_prices(limitless_id)
        card_image_url = get_image_url(card_id)
        card_prices_tcgp = card_prices.get("tcgplayer")
        images.append(
            generate_card_visualization(card_id, card_image_url, card_prices_tcgp)
        )
    return images
