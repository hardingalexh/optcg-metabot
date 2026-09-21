import os
from io import BytesIO

import discord
import matplotlib.pyplot as plt
import requests
from PIL import Image

TEXT_CARD_SEARCH_URL = "https://onepiece.limitlesstcg.com/api/dm/search?lang=en&q="


def parse_set(set_str: str) -> str:
    """Parses the set out of a string slice representing an set

    Args:
        set_str (str): A set string (like OP01, 01, OP-01)

    Returns:
        str: A set in the format of OP01
    """
    ## accepted formats are OP01, 01, OP-01
    set_str = set_str.replace("-", "")
    if len(set_str) == 2:
        set_str = f"OP{set_str}"
    if len(set_str) != 4:
        raise Exception("Invalid Set Type")
    return set_str.upper()


def get_card_numbers(param: str) -> list[str]:
    """for a given discord input, fetch the card numbers from limitless with version tag

    Args:
        param (str): _description_

    Returns:
        list[str]: _description_
    """
    params = param.split(" ")
    set_str = params[0]
    card_name = param.replace(f"{set_str} ", "")
    set_str = parse_set(set_str)
    search_param = f"{TEXT_CARD_SEARCH_URL}{card_name}%20"
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
    # return next([card.get("id") for card in response])


def get_image_url(card_id: str) -> str:
    """Gets the URL of a card image for a given card ID

    Args:
        card_id (str): Card ID string

    Returns:
        str: Card image URL
    """
    img_url = "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece"
    set_str = card_id.split("~")[0]
    set_str = set_str.split("-")[0]
    card_id_f = f"{card_id.replace('~', '_p').replace('_p0', '')}_EN"
    card_image_url = f"{img_url}/{set_str}/{card_id_f}.webp"
    return card_image_url


def format_for_discord(card_id: int, fig: plt) -> tuple[discord.File, discord.Embed]:
    """Formats the image into a discord embed using local attachments

    Args:
        card_id (int): card id
        fig (plt): matplotlib figure

    Returns:
        tuple[discord.File, discord.Embed]: file and embed ready for sending
    """
    output_path = f"tmp/{card_id}.png"
    fig.savefig(output_path, bbox_inches="tight", dpi=600)
    plt.close(fig)
    file = discord.File(output_path, filename=f"{card_id}.png")
    embed = discord.Embed()
    embed.set_image(url=f"attachment://{card_id}.png")
    return (file, embed)


def retrieve_leader_image(leader_id: str) -> Image:
    """For a given Leader, retrieve the image of the leader's card

    Args:
        leader_id (str): A leader ID

    Returns:
        Image: The leader image
    """
    image = None
    filename = f"data/leader_images/{leader_id}.png"
    ## fetch from disk
    if os.path.exists(filename):
        with Image.open(filename) as img:
            img.load()
            image = img
        return image
    else:
        image = download_leader_image(leader_id)
    return image


def download_leader_image(leader_id: str) -> Image:
    """Downloads the image for a given leader

    Args:
        leader_id (str): leader card id

    Returns:
        Image: the image file
    """
    ## download and save to disk otherwise
    card_image_url = get_image_url(leader_id)
    image_response = requests.get(card_image_url)
    if not image_response.ok:
        image_response = requests.get(card_image_url.replace("EN", "JP"))
    image = Image.open(BytesIO(image_response.content)).convert("RGB")
    image.save(f"data/leader_images/{leader_id}.png", format="png")
    return image
