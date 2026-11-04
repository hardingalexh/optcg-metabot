import datetime
import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from matplotlib.patches import Circle, Wedge
from PIL import Image, ImageDraw

from bot import parser
from utils import *

# Meta health index: probability that HEALTH_GAMES random opponents are all
# different leaders. Keep this constant fixed so the index stays comparable.
HEALTH_GAMES = 5
# (upper bound, label, color) - colors from the dataviz status palette
HEALTH_BANDS = [
    (0.30, "Unhealthy", "#d03b3b"),
    (0.50, "Concentrated", "#fab219"),
    (0.70, "Healthy", "#0ca30c"),
    (1.00, "Very Diverse", "#006300"),
]
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"


def meta_health_index(games: pd.Series, n: int = HEALTH_GAMES) -> float:
    """Probability that n random opponents are all different leaders

    Computed exactly as n! * e_n(p), where p is each leader's share of games
    and e_n is the elementary symmetric polynomial of degree n.

    Args:
        games (pd.Series): games played per leader
        n (int, optional): number of games. Defaults to HEALTH_GAMES.

    Returns:
        float: probability between 0 and 1
    """
    p = games / games.sum()
    e = [1.0] + [0.0] * n
    for x in p:
        for k in range(n, 0, -1):
            e[k] += x * e[k - 1]
    return math.factorial(n) * e[n]


def compute_meta_health(prefix: str = "all") -> dict:
    """Computes the meta health index from the full (untrimmed) meta dataset

    Args:
        prefix (str, optional): the dataset prefix. Defaults to "all".

    Returns:
        dict: index value, effective number of leaders, band label and color
    """
    games = pd.read_csv(f"data/meta_{prefix}.csv")["total_games"].dropna()
    p = games / games.sum()
    index = meta_health_index(games)
    label, color = next((l, c) for upper, l, c in HEALTH_BANDS if index <= upper)
    return {
        "index": index,
        "effective_leaders": 1 / (p**2).sum(),
        "label": label,
        "color": color,
    }


def draw_health_gauge(ax: plt.Axes, health: dict) -> None:
    """Draws a semicircle gauge for the meta health index onto the given axes

    Args:
        ax (plt.Axes): the axes to draw on
        health (dict): output of compute_meta_health
    """
    radius, width = 1.0, 0.28
    lower = 0.0
    for upper, _, color in HEALTH_BANDS:
        # 0% sits at 180 degrees (left), 100% at 0 degrees (right)
        ax.add_patch(
            Wedge(
                (0, 0),
                radius,
                180 * (1 - upper),
                180 * (1 - lower),
                width=width,
                facecolor=color,
                edgecolor="white",
                linewidth=2,
            )
        )
        lower = upper

    # tick labels at band edges
    for tick in [0.0] + [upper for upper, _, _ in HEALTH_BANDS]:
        angle = math.pi * (1 - tick)
        ax.text(
            1.13 * math.cos(angle),
            1.13 * math.sin(angle),
            f"{tick:.0%}",
            ha="center",
            va="center",
            fontsize=7,
            color=INK_MUTED,
        )

    # needle
    angle = math.pi * (1 - health["index"])
    needle = radius - width / 2
    ax.plot(
        [0, needle * math.cos(angle)],
        [0, needle * math.sin(angle)],
        color=INK_PRIMARY,
        linewidth=2.5,
        solid_capstyle="round",
        zorder=3,
    )
    ax.add_patch(Circle((0, 0), 0.06, facecolor=INK_PRIMARY, zorder=4))

    ax.text(
        0, 1.38, "Meta Health", ha="center", fontsize=11, weight="bold",
        color=INK_PRIMARY,
    )
    ax.text(
        0, -0.32, f"{health['index']:.0%}", ha="center", va="center",
        fontsize=22, weight="bold", color=INK_PRIMARY,
    )
    # band label in ink, with a color swatch carrying the band identity
    ax.add_patch(Circle((-0.42, -0.62), 0.05, facecolor=health["color"]))
    ax.text(
        -0.32, -0.62, health["label"], ha="left", va="center", fontsize=11,
        color=INK_PRIMARY,
    )
    ax.text(
        0, -0.92,
        f"Chance your next {HEALTH_GAMES} opponents\nare all different leaders",
        ha="center", va="center", fontsize=7.5, color=INK_SECONDARY,
    )
    ax.text(
        0, -1.2,
        f"Plays like ~{health['effective_leaders']:.0f} evenly played leaders",
        ha="center", va="center", fontsize=7.5, color=INK_SECONDARY,
    )

    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.35, 1.55)
    ax.set_aspect("equal")
    ax.axis("off")


def fetch_data(leader_id: str, prefix: str = "all") -> pd.DataFrame:
    """fetches the data for the meta report, reformatting leader data to look like meta data

    Args:
        leader (str): leader ID
        prefix (str): the dataset prefix

    Returns:
        pd.DataFrame: top 20 matches by games played
    """
    if leader_id:
        output = pd.read_csv(f"data/out_{prefix}.csv")
        output = output[output["leader_id"] == leader_id]
        # rename leader ID to the opponent ID
        mapper = {"leader_id": "source_leader_id", "opponent_id": "leader_id"}
        output = output.rename(columns=mapper)
    else:
        output = pd.read_csv(f"data/meta_{prefix}.csv")
    output = output.dropna(subset=["total_games", "total_w_pct"]).sort_values(
        "total_games", ascending=False
    )[0:20]
    output["total_games_std"] = (
        output["total_games"] - output["total_games"].mean()
    ) / output["total_games"].std()
    output["total_w_pct"] = output["total_w_pct"] - 50
    return output


def circle_crop_image(image: Image) -> Image:
    """For a given image, crop a circle roughly positioned to the character art

    Args:
        image (Image): the image content

    Returns:
        Image: the cropped image
    """
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


def build_chart(
    leaders: pd.DataFrame, leader_id: str, prefix: str, health: dict = None
) -> plt:
    """Builds the meta chart and returns the figure

    Args:
        leaders (pd.DataFrame): The leader matchup data
        leader_id (str, optional): The leader id, if left blank does the whole meta. Defaults to "".
        prefix (str): the dataset prefix
        health (dict, optional): meta health index, drawn as a gauge in the side panel
            when no leader is chosen. Defaults to None.

    Returns:
        plt.figure: matplotlib figure
    """
    if leader_id or health:
        fig = plt.figure(figsize=(12, 4), constrained_layout=True)
        ax_side = fig.add_axes([0.02, 0.05, 0.28, 0.9])
        ax_chart = fig.add_axes([0.38, 0.1, 0.58, 0.8])
        if leader_id:
            image = retrieve_leader_image(leader_id)
            ax_side.imshow(image)
            ax_side.axis("off")
        else:
            draw_health_gauge(ax_side, health)
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
    today = datetime.datetime.now()
    ax_chart.set_title(f"{prefix.title()} Meta Report ({today.strftime('%m/%d/%Y')})")
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


def get_images(param: str, prefix: str = "all") -> list[Image]:
    """For a given discord input, return the charts for all leaders

    Args:
        param (str): the leader string
        prefix (str, optional): The dataset prefix. Defaults to "all".

    Raises:
        Exception: Too many leaders

    Returns:
        list: images in a list
    """
    images = []
    if param:
        leaders = parser.parse_leader(param)
        if len(leaders) > 10:
            raise Exception("too many leaders")
        for leader in leaders:
            leader_id = leader.get("card_id")
            results = fetch_data(leader_id, prefix)

            if len(results) > 0:
                fig = build_chart(results, leader_id, prefix)
                images.append(format_for_discord(leader_id, fig))
    else:
        results = fetch_data(None, prefix)
        health = compute_meta_health(prefix)
        fig = build_chart(results, None, prefix, health)
        images.append(format_for_discord("meta", fig))
    return images
