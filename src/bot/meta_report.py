import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from PIL import Image, ImageDraw

from bot import parser
from utils import *


def fetch_data(leader_id: str) -> pd.DataFrame:
    """fetches the data for the meta report, reformatting leader data to look like meta data

    Args:
        leader (str): leader ID

    Returns:
        pd.DataFrame: top 20 matches by games played
    """
    if leader_id:
        output = pd.read_csv("data/out_all.csv")
        output = output[output["leader_id"] == leader_id]
        # rename leader ID to the opponent ID
        mapper = {"leader_id": "source_leader_id", "opponent_id": "leader_id"}
        output = output.rename(columns=mapper)
    else:
        output = pd.read_csv("data/meta_all.csv")
    output = output.dropna(subset=["total_games", "total_w_pct"]).sort_values(
        "total_games", ascending=False
    )[0:20]
    output["total_games_std"] = (
        output["total_games"] - output["total_games"].mean()
    ) / output["total_games"].std()
    output["total_w_pct"] = output["total_w_pct"] - 50
    return output


def circle_crop_image(image: Image) -> Image:
    box = (75, 50, 525, 500)
    cropped = image.crop(box)

    height, width = cropped.size
    lum_image = Image.new("L", [height, width], 0)

    draw = ImageDraw.Draw(lum_image)
    draw.pieslice([(0, 0), (height, width)], 0, 360, fill=255, outline="black")
    image_arr = np.array(cropped)
    lum_image_arr = np.array(lum_image)
    final_image_arr = np.dstack((image_arr, lum_image_arr))
    return final_image_arr


def build_chart(leaders: pd.DataFrame, leader_id: str = ""):
    if leader_id:
        fig = plt.figure(figsize=(12, 4), constrained_layout=True)
        ax_image = fig.add_axes([0.02, 0.05, 0.28, 0.9])
        ax_chart = fig.add_axes([0.38, 0.1, 0.58, 0.8])
        image = retrieve_leader_image(leader_id)
        ax_image.imshow(image)
        ax_image.axis("off")
    else:
        fig, ax_chart = plt.subplots()
        fig.set_size_inches(12, 4)

    for x, y, opp_id in zip(
        leaders["total_games_std"], leaders["total_w_pct"], leaders["leader_id"]
    ):
        image = retrieve_leader_image(f"{opp_id}")
        image = circle_crop_image(image)
        annotation = AnnotationBbox(
            OffsetImage(image, zoom=0.075),
            (x, y),
            frameon=False,
        )
        ax_chart.add_artist(annotation)

    ax_chart.set_title("Meta Report")
    ax_chart.set_xlabel("Matchup Representation")
    xmin = math.floor(leaders["total_games_std"].min())
    xmax = math.ceil(leaders["total_games_std"].max())
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
        if len(leaders) > 10:
            raise Exception("too many leaders")
        for leader in leaders:
            leader_id = leader.get("card_id")
            results = fetch_data(leader_id)
            if len(results) > 0:
                fig = build_chart(results, leader_id)
                images.append(format_for_discord(leader_id, fig))
    else:
        results = fetch_data(None)
        fig = build_chart(results, None)
        images.append(format_for_discord("meta", fig))
    return images
