"""
EcoScan -- AI-Powered Sustainability Scanner
Run with:  streamlit run app.py
"""

import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from scanner.data_fetcher import fetch_by_barcode, search_by_name, search_by_category
from scanner.scoring import compute_sustainability_score
from scanner.recommender import find_greener_alternatives
from scanner.utils import impact_summary_message

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE_CSV = os.path.join(HERE, "data", "sample_products.csv")

st.set_page_config(page_title="EcoScan", page_icon="🌱", layout="centered")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_sample_dataset():
    return pd.read_csv(SAMPLE_CSV).fillna("")


def sample_row_to_product(row) -> dict:
    return {
        "barcode": str(row["barcode"]),
        "name": row["product_name"],
        "brand": row["brand"],
        "category": row["category"],
        "origin_country": row["origin_country"],
        "packaging_text": row["packaging_text"],
        "materials_text": row["materials_text"],
        "labels_text": row["labels_text"],
        "image_url": "",
        "source": "Sample dataset (offline demo)",
    }


def find_product(query: str, by: str):
    """Looks the product up live first; falls back to the bundled sample
    dataset so a demo still works without wifi (see README > Offline mode)."""
    if by == "Barcode":
        product = fetch_by_barcode(query)
        if product:
            return product
        sample = load_sample_dataset()
        match = sample[sample["barcode"].astype(str) == query.strip()]
    else:
        results = search_by_name(query)
        if results:
            return results[0]
        sample = load_sample_dataset()
        match = sample[sample["product_name"].str.contains(query, case=False, na=False)]

    if not match.empty:
        return sample_row_to_product(match.iloc[0])
    return None


def get_alternatives(product: dict, score: dict, top_n: int = 3):
    candidates = search_by_category(product.get("category", ""), exclude_barcode=product.get("barcode"))
    if not candidates:
        sample = load_sample_dataset()
        same_category = sample[sample["category"] == product.get("category", "")]
        candidates = [sample_row_to_product(r) for _, r in same_category.iterrows()]
    return find_greener_alternatives(product, score, candidates, top_n=top_n)


def gauge_figure(score_total: float, band_color: str) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score_total,
        number={"suffix": " / 100", "font": {"size": 36}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": band_color, "thickness": 0.3},
            "steps": [
                {"range": [0, 40], "color": "#FBE3DC"},
                {"range": [40, 70], "color": "#FDF0D5"},
                {"range": [70, 100], "color": "#DFF3E3"},
            ],
        },
    ))
    fig.update_layout(height=280, margin=dict(l=20, r=20, t=30, b=10))
    return fig


def breakdown_donut(score: dict) -> go.Figure:
    labels = ["Sourcing", "Packaging", "Transport", "Labor"]
    values = [score["sourcing"], score["packaging"], score["transport"], score["labor"]]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.6,
        marker={"colors": ["#2E7D32", "#66BB6A", "#A5D6A7", "#1B5E20"]},
    ))
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=30, b=10),
                       title="Score Breakdown", showlegend=True)
    return fig


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.title("🌱 EcoScan")
st.caption("AI-powered sustainability scores for everyday purchases -- SDG 12: Responsible Consumption & Production")

tab_scan, tab_insights = st.tabs(["🔍 Scan a Product", "📊 Dataset Insights"])

with tab_scan:
    st.write("Look a product up by barcode or by name to see its sustainability score.")

    search_mode = st.radio("Search by", ["Barcode", "Product name"], horizontal=True)
    placeholder = "e.g. 8901111000028" if search_mode == "Barcode" else "e.g. organic cotton t-shirt"
    query = st.text_input(f"Enter a {search_mode.lower()}", placeholder=placeholder)
    search_clicked = st.button("Check sustainability score", type="primary")

    if search_clicked and query.strip():
        with st.spinner("Fetching product data and scoring it..."):
            by = "Barcode" if search_mode == "Barcode" else "Name"
            product = find_product(query.strip(), by)

        if not product:
            st.error(
                "We couldn't find that product in Open Food Facts, Open Product Facts, "
                "or our sample dataset. Try a different barcode/name, or see README.md "
                "for how to add products to Open Food Facts yourself."
            )
        else:
            score = compute_sustainability_score(product)

            col_info, col_gauge = st.columns([1, 1])
            with col_info:
                if product.get("image_url"):
                    st.image(product["image_url"], width=140)
                st.subheader(product["name"])
                st.caption(f"{product['brand']} • {product.get('category') or 'Uncategorised'}")
                st.caption(f"Data source: {product.get('source', 'Unknown')}")
                st.markdown(f"**{score['band_label']}**")
            with col_gauge:
                st.plotly_chart(gauge_figure(score["total"], score["band_color"]), use_container_width=True)

            st.plotly_chart(breakdown_donut(score), use_container_width=True)

            st.subheader("🌿 Greener alternatives")
            alternatives = get_alternatives(product, score)
            if not alternatives:
                st.info("This is already one of the more sustainable options we could find in this category.")
            else:
                for alt in alternatives:
                    alt_product, alt_score = alt["product"], alt["score"]
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.markdown(f"**{alt_product['name']}** ({alt_product['brand']})")
                            st.caption(" • ".join(alt["why_better"]))
                        with c2:
                            st.metric("Score", f"{alt_score['total']:.0f}/100")

                st.subheader("📈 Impact summary")
                best = alternatives[0]
                st.success(impact_summary_message(
                    score["total"], best["product"]["name"], best["score"]["total"],
                    product.get("origin_country", ""),
                ))

    st.divider()
    with st.expander("ℹ️ How is this score calculated?"):
        st.markdown(
            "- **Sourcing (0-25):** keyword + lightweight NLP semantic-similarity check on "
            "ingredients/materials text\n"
            "- **Packaging (0-25):** keyword match on packaging materials (cardboard/glass/metal "
            "score higher than single-use plastic)\n"
            "- **Transport (0-25):** estimated shipping distance from the country of origin\n"
            "- **Labor (0-25):** presence of recognised fair-trade/ethical-sourcing labels "
            "(absence isn't penalised -- see scanner/scoring.py for why)\n\n"
            "See `scanner/scoring.py` for the full, commented logic."
        )

with tab_insights:
    st.write(
        "A look at the bundled sample dataset -- useful for demoing offline, and for the "
        "kind of analysis-side visualizations described in Logbook section 8."
    )
    df = load_sample_dataset()
    scored = df.apply(
        lambda row: compute_sustainability_score({
            "materials_text": row["materials_text"],
            "packaging_text": row["packaging_text"],
            "origin_country": row["origin_country"],
            "labels_text": row["labels_text"],
        }),
        axis=1, result_type="expand",
    )
    full = pd.concat([df, scored], axis=1)

    st.metric("Products in sample dataset", len(full))
    st.metric("Average sustainability score", f"{full['total'].mean():.1f} / 100")

    st.bar_chart(full["brand"].value_counts())
    st.caption("Products per brand in the sample dataset.")

    st.markdown(
        "For the world-map, word-cloud, and correlation-heatmap charts, run "
        "`python analysis/exploratory_analysis.py` -- they're saved as image files so they "
        "don't need to regenerate on every page load."
    )
