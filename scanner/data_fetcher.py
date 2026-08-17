"""
Fetches product data from Open Food Facts (packaged food) and falls back to
Open Product Facts (everything else) -- see Logbook 7.2, Data Source 1.

Both are free, open, no-API-key-required databases under the Open Database
License (ODbL) -- see README.md for attribution. Open Food Facts asks every
client to send a descriptive User-Agent, so we do.

Full-text search ("search by name") is only supported on OpenFoodFacts' v1
search endpoint (/cgi/search.pl) -- the newer v2 /api/v2/search endpoint only
supports structured/tag filters (e.g. by category), which is what we use for
finding alternatives in the same category. See the API notes in README.md.
"""

import requests
import streamlit as st

USER_AGENT = "EcoScan-SchoolProject/1.0 (contact: your-team-email@example.com)"
HEADERS = {"User-Agent": USER_AGENT}
REQUEST_TIMEOUT = 8  # seconds

OFF_BASE = "https://world.openfoodfacts.org"
OPF_BASE = "https://world.openproductfacts.org"

FIELDS = "code,product_name,brands,categories,origins,countries,packaging,ingredients_text,labels,image_front_small_url"


def normalize_product(raw: dict, source: str) -> dict:
    """Converts an OpenFoodFacts/OpenProductFacts product object into the
    flat shape the rest of the app (scoring.py, recommender.py) expects."""
    origin = raw.get("origins") or raw.get("countries") or ""
    # Origins/countries can arrive as a comma list ("India,Vietnam") -- use
    # the first entry for the distance estimate.
    origin_first = origin.split(",")[0].strip() if origin else ""

    return {
        "barcode": raw.get("code", ""),
        "name": raw.get("product_name") or "Unnamed product",
        "brand": raw.get("brands", "") or "Unknown brand",
        "category": (raw.get("categories", "") or "").split(",")[0].strip(),
        "origin_country": origin_first,
        "packaging_text": raw.get("packaging", "") or "",
        "materials_text": raw.get("ingredients_text", "") or raw.get("categories", "") or "",
        "labels_text": raw.get("labels", "") or "",
        "image_url": raw.get("image_front_small_url", ""),
        "source": source,
    }


def _get_json(url: str, params: dict = None):
    response = requests.get(url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_by_barcode(barcode: str):
    """Tries Open Food Facts first, then Open Product Facts. Returns a
    normalised product dict, or None if not found in either database."""
    barcode = (barcode or "").strip()
    if not barcode:
        return None

    for base, source in [(OFF_BASE, "OpenFoodFacts"), (OPF_BASE, "OpenProductFacts")]:
        try:
            data = _get_json(f"{base}/api/v2/product/{barcode}.json", {"fields": FIELDS})
        except requests.exceptions.RequestException:
            continue
        if data.get("status") == 1 and data.get("product"):
            return normalize_product(data["product"], source)
    return None


@st.cache_data(show_spinner=False, ttl=3600)
def search_by_name(name: str, page_size: int = 10):
    """Full-text search by product name (Open Food Facts v1 search endpoint
    -- see module docstring for why v1, not v2)."""
    name = (name or "").strip()
    if not name:
        return []
    params = {
        "search_terms": name,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": page_size,
        "fields": FIELDS,
    }
    try:
        data = _get_json(f"{OFF_BASE}/cgi/search.pl", params)
    except requests.exceptions.RequestException:
        return []
    products = data.get("products", [])
    return [normalize_product(p, "OpenFoodFacts") for p in products if p.get("product_name")]


def search_by_category(category: str, exclude_barcode: str = None, page_size: int = 20):
    """Structured search used by the recommender to find same-category
    alternatives (Open Food Facts v2 search endpoint)."""
    category = (category or "").strip()
    if not category:
        return []
    params = {
        "categories_tags_en": category,
        "page_size": page_size,
        "fields": FIELDS,
    }
    try:
        data = _get_json(f"{OFF_BASE}/api/v2/search", params)
    except requests.exceptions.RequestException:
        return []
    products = data.get("products", [])
    results = [normalize_product(p, "OpenFoodFacts") for p in products if p.get("product_name")]
    if exclude_barcode:
        results = [p for p in results if p["barcode"] != exclude_barcode]
    return results
