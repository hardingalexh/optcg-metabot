from io import BytesIO

import marketplace
import matplotlib.pyplot as plt
import pandas as pd
import parser
import requests
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from PIL import Image


def fetch_data(leader_id: str) -> pd.DataFrame:
    """fetches the data for the meta report, reformatting leader data to look like meta data

    Args:
        leader (str): leader ID

    Returns:
        pd.DataFrame: top 20 matches by games played
    """
    if leader_id:
        output = pd.read_csv("out_all.csv")
        output = output[output["leader_id"] == leader_id]
        # rename leader ID to the opponent ID
        mapper = {"leader_id": "source_leader_id", "opponent_id": "leader_id"}
        output = output.rename(columns=mapper)
    else:
        output = pd.read_csv("meta_all.csv")
    output = output.dropna().sort_values("total_games", ascending=False)[0:20]
    output["total_games_std"] = (
        output["total_games"] - output["total_games"].mean()
    ) / output["total_games"].std()
    output["total_w_pct"] = output["total_w_pct"] - 50

    return output


def retrieve_image(leader_id: str) -> Image:
    card_image_url = marketplace.get_image_url(leader_id)
    image_response = requests.get(card_image_url)
    if not image_response.ok:
        image_response = requests.get(card_image_url.replace("EN", "JP"))
    image = Image.open(BytesIO(image_response.content)).convert("RGB")
    return image


def build_chart(leaders: pd.DataFrame, leader_id: str = ""):
    if leader_id:
        fig = plt.figure(figsize=(12, 4), constrained_layout=True)
        ax_image = fig.add_axes([0.02, 0.05, 0.28, 0.9])
        ax_chart = fig.add_axes([0.38, 0.1, 0.58, 0.8])
        image = retrieve_image(leader_id)
        ax_image.imshow(image)
        ax_image.axis("off")
    else:
        fig, ax_chart = plt.subplots()
        fig.set_size_inches(12, 4)

    for x, y, opp_id in zip(
        leaders["total_games_std"], leaders["total_w_pct"], leaders["leader_id"]
    ):
        image = retrieve_image(f"{opp_id}~0")
        annotation = AnnotationBbox(
            OffsetImage(image, zoom=0.05),
            (x, y),
            frameon=False,
        )
        ax_chart.add_artist(annotation)

    ax_chart.set_title("Meta Report")
    ax_chart.set_xlabel("Matchup Representation")
    if not leader_id:
        ax_chart.set_xlim(left=-1.5, right=2.5)
        ax_chart.set_ylim(bottom=-15, top=15)
    else:
        xmin = leaders["total_games_std"].min() - 0.5
        xmax = leaders["total_games_std"].max() + 0.5
        ymin = leaders["total_w_pct"].min() - 5
        ymax = leaders["total_w_pct"].max() + 5
        ax_chart.set_xlim(left=xmin, right=xmax)
        ax_chart.set_ylim(bottom=ymin, top=ymax)

    ax_chart.axhline(y=0)
    ax_chart.axvline(x=0)
    ax_chart.set_ylabel("Win Rate (+50)")
    ax_chart.grid(True, alpha=0.3)
    return fig


def get_images(param):
    images = []
    if param:
        leaders = parser.parse_leader(param)
        for leader in leaders:
            leader_id = leader.get("card_id")
            results = fetch_data(leader_id)
            fig = build_chart(results, leader_id)
            images.append(marketplace.format_for_discord(leader_id, fig))
    else:
        results = fetch_data(None)
        fig = build_chart(results, None)
        images.append(marketplace.format_for_discord("meta", fig))
    return images
