"""
Sustainability scoring engine for EcoScan.

WHY RULE-BASED + LIGHTWEIGHT NLP, NOT A TRAINED ML MODEL:
At prototype stage we don't have a labelled dataset of "true" sustainability
scores to train a supervised model on -- and inventing fake ground-truth
labels would make the model worse, not better. So this file implements a
transparent, explainable scoring model:

  1. Three factors (Packaging, Transport, Labor) use taxonomy/keyword
     matching against fields OpenFoodFacts / OpenProductFacts already
     provide (packaging materials, country of origin, ethical labels).
  2. The fourth factor (Sourcing) additionally uses a small TF-IDF +
     cosine-similarity model over the ingredients/materials text. That's a
     lightweight, fully-local stand-in for the "large language model +
     semantic search" step in our original concept (see Logbook 5.1,
     AI Idea #2) -- it compares *meaning*, not just exact keyword matches,
     without needing a paid LLM API.

Each sub-score is 0-25, so the total is 0-100 -- matching the four
categories in our donut-chart breakdown (Sourcing / Packaging / Transport /
Labor) from Logbook section 8.

FUTURE IMPROVEMENT (see Logbook 9.5): once we log enough verified scores and
user feedback, this is the file we'd swap for a trained model -- the rest of
the app (data_fetcher, recommender, app.py) would not need to change.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from scanner.utils import estimate_distance_km, band_for_score

# ---------------------------------------------------------------------------
# Keyword banks (kept short and legible on purpose -- see Logbook 7.1 for the
# reasoning on why these fields were chosen, and the Data Expert's note on
# avoiding unfair bias below).
# ---------------------------------------------------------------------------

POSITIVE_PACKAGING_KEYWORDS = [
    "cardboard", "paper", "glass", "metal", "aluminium", "aluminum", "tin",
    "recyclable", "recycled", "compostable", "reusable", "carton",
]
NEGATIVE_PACKAGING_KEYWORDS = [
    "plastic", "pet", "polyethylene", "polystyrene", "styrofoam",
    "multilayer", "single-use", "film", "laminate",
]

ETHICAL_LABEL_KEYWORDS = [
    "fair trade", "fairtrade", "rainforest alliance", "sa8000", "b corp",
    "bcorp", "ethical", "living wage", "fair for life",
]

# Small reference corpora for the TF-IDF "semantic lean" check on the
# sourcing/materials text -- deliberately short and topic-focused.
POSITIVE_REFERENCE_TEXT = (
    "organic sustainably sourced recycled upcycled materials biodegradable "
    "compostable natural plant based fair trade responsibly sourced "
    "renewable low impact eco friendly cruelty free"
)
NEGATIVE_REFERENCE_TEXT = (
    "synthetic virgin plastic non biodegradable excessive packaging "
    "high emissions unsustainable harmful chemical intensive"
)

POSITIVE_SOURCING_KEYWORDS = [
    "organic", "recycled", "upcycled", "biodegradable", "compostable",
    "plant-based", "natural", "sustainably sourced", "fair trade",
    "responsibly sourced", "renewable",
]
NEGATIVE_SOURCING_KEYWORDS = [
    "synthetic", "virgin plastic", "non-biodegradable",
]


def _count_hits(text: str, keywords) -> int:
    text = (text or "").lower()
    return sum(1 for kw in keywords if kw in text)


def _semantic_lean(text: str) -> float:
    """Returns a value from -1 (reads like 'unsustainable' language) to +1
    (reads like 'sustainable' language) using TF-IDF + cosine similarity.
    Returns 0.0 (neutral) if there isn't enough text to compare."""
    text = (text or "").strip()
    if len(text) < 3:
        return 0.0
    documents = [text, POSITIVE_REFERENCE_TEXT, NEGATIVE_REFERENCE_TEXT]
    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf = vectorizer.fit_transform(documents)
        sims = cosine_similarity(tfidf[0:1], tfidf[1:3])[0]
    except ValueError:
        # Happens if the text is all stop-words / punctuation -- treat as neutral.
        return 0.0
    return float(sims[0] - sims[1])


def sourcing_score(materials_text: str) -> float:
    """0-25. Blends keyword hits with the TF-IDF semantic lean so a product
    described in different words than our keyword list can still score
    sensibly (e.g. 'grown without synthetic pesticides' vs. just 'organic')."""
    base = 12.5
    keyword_adjustment = 2.5 * _count_hits(materials_text, POSITIVE_SOURCING_KEYWORDS)
    keyword_adjustment -= 2.5 * _count_hits(materials_text, NEGATIVE_SOURCING_KEYWORDS)
    semantic_adjustment = _semantic_lean(materials_text) * 6.0
    score = base + keyword_adjustment + semantic_adjustment
    return round(max(0, min(25, score)), 1)


def packaging_score(packaging_text: str) -> float:
    """0-25. Keyword-matches packaging materials/descriptions."""
    base = 12.5
    pos = _count_hits(packaging_text, POSITIVE_PACKAGING_KEYWORDS)
    neg = _count_hits(packaging_text, NEGATIVE_PACKAGING_KEYWORDS)
    score = base + (2.5 * pos) - (2.5 * neg)
    return round(max(0, min(25, score)), 1)


def transport_score(origin_country: str) -> float:
    """0-25. Closer origin -> higher score. Banding chosen so 'domestic'
    products cluster near the top and long-haul air/sea freight near the
    bottom -- see scanner/geo_data.py for the distance table."""
    distance_km = estimate_distance_km(origin_country)
    if distance_km <= 500:
        return 25.0
    elif distance_km <= 2000:
        return 19.0
    elif distance_km <= 6000:
        return 12.0
    elif distance_km <= 10000:
        return 7.0
    else:
        return 3.0


def labor_score(labels_text: str) -> float:
    """0-25. NOTE ON FAIRNESS (see Logbook 2.1, Data Expert responsibilities):
    the *absence* of a fair-trade/ethical label does not mean a product was
    unethically made -- plenty of small or local producers can't afford
    certification. So an unlabeled product gets a neutral score rather than
    a penalty; only a recognised ethical-sourcing label raises it."""
    base = 12.5
    hits = _count_hits(labels_text, ETHICAL_LABEL_KEYWORDS)
    score = base + (6.25 * min(hits, 2))
    return round(max(0, min(25, score)), 1)


def compute_sustainability_score(product: dict) -> dict:
    """
    product is expected to have the normalised keys produced by
    scanner/data_fetcher.py: materials_text, packaging_text, origin_country,
    labels_text. Returns the full breakdown used by app.py and by the
    recommender.
    """
    sourcing = sourcing_score(product.get("materials_text", ""))
    packaging = packaging_score(product.get("packaging_text", ""))
    transport = transport_score(product.get("origin_country", ""))
    labor = labor_score(product.get("labels_text", ""))

    total = round(sourcing + packaging + transport + labor, 1)
    band_label, band_color = band_for_score(total)

    return {
        "total": total,
        "sourcing": sourcing,
        "packaging": packaging,
        "transport": transport,
        "labor": labor,
        "band_label": band_label,
        "band_color": band_color,
    }
