#!/usr/bin/env python3
"""Compact leader scatter plot: importable and runnable.

Assumptions and style:
- Input CSVs are valid; avoid defensive casting.
- Keep implementation concise with clear comments.
- Running the file executes a small CLI wrapper.
"""

import argparse
import os
from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from matplotlib.offsetbox import AnnotationBbox, OffsetImage
from PIL import Image


def load_df(path: str) -> pd.DataFrame:
    """Load summary CSV and normalize leader column name if needed."""
    df = pd.read_csv(path)
    if "leader" not in df.columns and "leader_name" in df.columns:
        df = df.rename(columns={"leader_name": "leader"})
    return df


def compute_win_pct(df: pd.DataFrame) -> pd.Series:
    """(wins - losses) / (wins + losses) * 100; zero when no games."""
    denom = df["wins"] + df["losses"]
    return pd.Series(
        np.where(denom > 0, (df["wins"] - df["losses"]) / denom * 100.0, 0.0),
        index=df.index,
    )


def plot(
    df: pd.DataFrame,
    out: str | None = None,
    jitter: float = 0.0,
    seed: int = 1,
    image_zoom: float = 1.0,
):
    """Draw scatter and return (fig, ax). X is std-dev units of number_of_matches."""
    x_raw = df["number_of_matches"].astype(float)
    y = compute_win_pct(df)
    mean = x_raw.mean()
    std = x_raw.std() or 1.0
    x = (x_raw - mean) / std

    rng = np.random.default_rng(seed)
    xj = x + (rng.normal(scale=jitter, size=len(x)) if jitter else 0)

    sizes = 40 + (x_raw - x_raw.min()) / max(1.0, (x_raw.max() - x_raw.min())) * 220
    colors = ["green" if v > 0 else "red" if v < 0 else "gray" for v in y]

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.scatter(xj, y, s=sizes, c=colors, alpha=0.75, edgecolors="k", linewidths=0.3)
    ax.axvline(0.0, color="k", linestyle="--", linewidth=1)
    ax.axhline(0.0, color="k", linestyle="--", linewidth=1)

    ax.set_xlim(xj.min() - 0.5, xj.max() + 0.5)
    ticks = np.arange(int(np.floor(xj.min())), int(np.ceil(xj.max())) + 1)
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{t}\n({int(round(t * std + mean))})" for t in ticks])
    ax.set_ylim(-25, 25)
    ax.set_xlabel("Number of matches (std devs)")
    ax.set_ylabel("Win pct: (wins - losses) / (wins + losses) * 100")
    ax.set_title("Leaders: Four-Quadrant Scatter")

    # draw images when provided, otherwise annotate with names
    if "_image" in df.columns:
        ppp = fig.dpi / 72.0
        for i, row in enumerate(df.itertuples(index=False)):
            img = getattr(row, "_image", None)
            xi, yi = float(xj.iat[i]), float(y.iat[i])
            std_val, win_val = float(x.iat[i]), float(y.iat[i])
            label = f"{std_val:+.1f}\n{win_val:.1f}%"
            color = "green" if (std_val > 0 and win_val > 50.0) else "red"
            if img is None:
                ax.annotate(
                    row.leader,
                    (xi, yi),
                    xytext=(5, 2),
                    textcoords="offset points",
                    fontsize=8,
                )
                ax.annotate(
                    label,
                    (xi, yi),
                    xytext=(0, -12),
                    textcoords="offset points",
                    ha="center",
                    va="top",
                    fontsize=7,
                    color=color,
                )
                continue
            # size image to approximate marker
            s_val = float(sizes[i])
            pts = max(4.0, np.sqrt(s_val))
            desired_px = pts * ppp
            img_w = img.size[0] if hasattr(img, "size") else desired_px
            zoom = float(np.clip((desired_px / img_w) * image_zoom, 0.03, 1.0))
            im = OffsetImage(img, zoom=zoom)
            ab = AnnotationBbox(im, (xi, yi), frameon=False)
            ax.add_artist(ab)
            ax.annotate(
                label,
                (xi, yi),
                xytext=(0, -int(pts * 1.6)),
                textcoords="offset points",
                ha="center",
                va="top",
                fontsize=7,
                color=color,
            )
    else:
        for i, r in df.iterrows():
            ax.annotate(
                str(r["leader"]),
                (xj.iat[i], y.iat[i]),
                xytext=(5, 2),
                textcoords="offset points",
                fontsize=8,
            )

    plt.tight_layout()
    if out:
        fig.savefig(out, dpi=300)
        print(f"Saved plot to {out}")
    else:
        plt.show()
    return fig, ax


def _search_cards(name: str) -> list[str]:
    """Minimal remote search for card ids; returns list of card_id~variant strings."""
    q = f"https://onepiece.limitlesstcg.com/api/dm/search?lang=en&q={name}"
    try:
        # use a session that doesn't inherit environment proxy settings
        s = requests.Session()
        s.trust_env = False
        r = s.get(q, timeout=5)
        r.raise_for_status()
        return [f"{c.get('card_id')}~{c.get('variant')}" for c in r.json()]
    except Exception:
        return []


def _build_image_url(card_id: str) -> str:
    base = "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/one-piece"
    set_id = card_id.split("~")[0].split("-")[0]
    card_f = f"{card_id.replace('~', '_p').replace('_p0', '')}_EN"
    return f"{base}/{set_id}/{card_f}.webp"


def _fetch_url(url: str, timeout: int = 5):
    """Fetch URL using a session that ignores env proxies (safer in local dev).

    Returns response or raises.
    """
    s = requests.Session()
    s.trust_env = False
    return s.get(url, timeout=timeout)


def generate_leader_scatter(
    input_path: str = "meta_all.csv",
    out: str | None = None,
    top: int = 20,
    jitter: bool = True,
    jitter_scale: float = 0.3,
    seed: int = 1,
    use_images: bool = True,
    image_zoom: float = 1,
    source: str = "meta",
    leader_name: str | None = None,
):
    """Load data (meta or out), optionally fetch images, and call plot()."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(input_path)
    source = (source or "meta").lower()
    if source == "meta":
        df = load_df(input_path)
        if top > 0:
            df = df.nlargest(top, "number_of_matches")
    else:
        if not leader_name:
            raise ValueError("leader_name required for source='out'")
        out_df = pd.read_csv(input_path)
        key = str(leader_name).strip()
        m = out_df[(out_df["leader"] == key) | (out_df.get("leader_id", "") == key)]
        if m.empty:
            mask = out_df["leader"].str.contains(
                key, case=False, na=False
            ) | out_df.get("leader_id", "").astype(str).str.contains(key, na=False)
            m = out_df[mask]
        if m.empty:
            raise ValueError(f"No matchups for: {leader_name}")
        rows = []
        for _, r in m.iterrows():
            total = int(r.get("total_games") or 0)
            if (r.get("first_total_games") or 0) or (r.get("second_total_games") or 0):
                f = int(r.get("first_total_games") or 0)
                s = int(r.get("second_total_games") or 0)
                fp = float(r.get("first_w_pct") or 0) / 100.0
                sp = float(r.get("second_w_pct") or 0) / 100.0
                wins = int(round(fp * f + sp * s))
            else:
                wins = int(round(float(r.get("total_w_pct") or 0) / 100.0 * total))
            rows.append(
                {
                    "leader": r.get("opponent") or "",
                    "leader_id": r.get("opponent_id"),
                    "number_of_matches": total,
                    "wins": wins,
                    "losses": max(0, total - wins),
                }
            )
        df = pd.DataFrame(rows)
        if top > 0:
            df = df.nlargest(top, "number_of_matches")

    js = jitter_scale if jitter else 0.0

    if use_images:
        cache = {}
        imgs = []
        for _, row in df.iterrows():
            name = row["leader"]
            if name in cache:
                imgs.append(cache[name])
                continue
            img = None
            lid = row.get("leader_id")
            if lid:
                for v in ["", "~0", "~1"]:
                    try:
                        url = _build_image_url(str(lid) + v)
                        r = _fetch_url(url, timeout=5)
                        if r.ok:
                            img = Image.open(BytesIO(r.content)).convert("RGBA")
                            break
                    except Exception:
                        continue
            if img is None:
                cards = _search_cards(str(name))
                if cards:
                    try:
                        r = _fetch_url(_build_image_url(cards[0]), timeout=5)
                        if r.ok:
                            img = Image.open(BytesIO(r.content)).convert("RGBA")
                    except Exception:
                        img = None
            cache[name] = img
            imgs.append(img)
        df["_image"] = imgs
        # brief summary so caller knows whether images were attached
        fetched = sum(1 for i in imgs if i is not None)
        if fetched == 0:
            print("Warning: no images fetched; falling back to text labels.")
        else:
            print(f"Fetched {fetched}/{len(imgs)} images.")

    return plot(df, out, jitter=js, seed=seed, image_zoom=image_zoom)


def _cli():
    p = argparse.ArgumentParser()
    p.add_argument("input", nargs="?", default="meta_all.csv")
    p.add_argument("--out", default=None)
    p.add_argument("--source", choices=["meta", "out"], default="meta")
    p.add_argument("--leader", default=None)
    p.add_argument("--no-images", dest="use_images", action="store_false")
    args = p.parse_args()
    generate_leader_scatter(
        input_path=args.input,
        out=args.out,
        source=args.source,
        leader_name=args.leader,
        use_images=args.use_images,
    )


if __name__ == "__main__":
    generate_leader_scatter(use_images=True)
