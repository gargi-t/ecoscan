"""
Exploratory analysis over the sample product dataset -- see Logbook 8
(Data Visualization > Visualization for Analysis, Tool: Python).

Produces four charts into analysis/output/:
  1. brand_distribution.png   - bar chart of products per brand
  2. origin_country_chart.png - where products come from, ranked by distance
  3. materials_wordcloud.png  - most frequent materials/packaging words
  4. correlation_heatmap.png  - how the four sub-scores relate to each other

Run from the project root:
    python analysis/exploratory_analysis.py

NOTE on chart 2: our original plan (Logbook 8) was a world map. We built it
first with Plotly's choropleth, but static image export needs a headless
Chrome browser, which wasn't available in every environment we tested this
on (including the sandbox this was drafted in) -- so we switched to a
distance-ranked bar chart using the same country data instead. It answers
the same "where do our products come from" question and, as a bonus, lines
up directly with the Transport score. If your machine has Chrome installed,
swapping this function for a `plotly.express.choropleth` + `fig.write_image()`
call is a one-function change.
"""

import os
import sys

import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless-safe backend
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scanner.scoring import compute_sustainability_score  # noqa: E402
from scanner.utils import estimate_distance_km  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(HERE, "..", "data", "sample_products.csv")
OUTPUT_DIR = os.path.join(HERE, "output")

BRAND_COLOR = "#2E7D32"


def load_scored_dataframe() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH).fillna("")
    scores = df.apply(
        lambda row: compute_sustainability_score({
            "materials_text": row["materials_text"],
            "packaging_text": row["packaging_text"],
            "origin_country": row["origin_country"],
            "labels_text": row["labels_text"],
        }),
        axis=1,
        result_type="expand",
    )
    return pd.concat([df, scores], axis=1)


def chart_brand_distribution(df: pd.DataFrame, out_path: str):
    counts = df["brand"].value_counts().sort_values()
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(counts.index, counts.values, color=BRAND_COLOR)
    ax.set_xlabel("Number of products in our sample dataset")
    ax.set_title("Products per Brand")
    ax.bar_label(ax.containers[0], padding=3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def chart_origin_country_distance(df: pd.DataFrame, out_path: str):
    """Where our sample products come from, ranked by (approximate) shipping
    distance from India -- see the module docstring for why this replaced a
    literal world map, and scanner/geo_data.py for the distance table."""
    counts = df["origin_country"].value_counts().reset_index()
    counts.columns = ["origin_country", "product_count"]
    counts["distance_km"] = counts["origin_country"].apply(estimate_distance_km)
    counts = counts.sort_values("distance_km")

    colors = ["#2E7D32" if d <= 2000 else "#F3A712" if d <= 6000 else "#E4572E"
              for d in counts["distance_km"]]

    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.barh(counts["origin_country"], counts["distance_km"], color=colors)
    for bar, count in zip(bars, counts["product_count"]):
        ax.text(bar.get_width() + 150, bar.get_y() + bar.get_height() / 2,
                f"{count} product{'s' if count != 1 else ''}", va="center", fontsize=9)
    ax.set_xlabel("Approx. distance from India (km)")
    ax.set_title("Where Do Our Sample Products Come From?")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def chart_materials_wordcloud(df: pd.DataFrame, out_path: str):
    text = " ".join(df["materials_text"].tolist() + df["packaging_text"].tolist())
    cloud = WordCloud(
        width=1000, height=550, background_color="white",
        colormap="Greens", collocations=False,
    ).generate(text)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.imshow(cloud, interpolation="bilinear")
    ax.axis("off")
    ax.set_title("Most Common Materials & Packaging Words", fontsize=14)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def chart_correlation_heatmap(df: pd.DataFrame, out_path: str):
    cols = ["sourcing", "packaging", "transport", "labor", "total"]
    corr = df[cols].corr()
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="Greens", vmin=-1, vmax=1, ax=ax)
    ax.set_title("How the Score Factors Relate to Each Other")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = load_scored_dataframe()

    chart_brand_distribution(df, os.path.join(OUTPUT_DIR, "brand_distribution.png"))
    chart_origin_country_distance(df, os.path.join(OUTPUT_DIR, "origin_country_chart.png"))
    chart_materials_wordcloud(df, os.path.join(OUTPUT_DIR, "materials_wordcloud.png"))
    chart_correlation_heatmap(df, os.path.join(OUTPUT_DIR, "correlation_heatmap.png"))

    print(f"Scored {len(df)} sample products.")
    print(f"Average sustainability score: {df['total'].mean():.1f} / 100")
    print(f"Charts written to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
