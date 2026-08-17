"""
Greener-alternatives recommender.

This is a simple content-based recommender, not a trained model: score every
candidate product in the same category with the same scoring engine used for
the scanned product, then return the highest scoring ones. It's intentionally
easy to reason about -- a teacher or judge can ask "why was this suggested?"
and the answer is always "it scored higher on these specific factors," which
we can show.
"""

from scanner.scoring import compute_sustainability_score


def _better_factor_labels(original: dict, candidate: dict) -> list:
    """Returns the sub-score names where the candidate beats the original by
    a meaningful margin, used for the 'why it's better' tag in the UI."""
    labels = {
        "sourcing": "Better sourcing",
        "packaging": "Less packaging waste",
        "transport": "Shorter distance travelled",
        "labor": "Verified ethical labour",
    }
    reasons = []
    for key, label in labels.items():
        if candidate[key] - original[key] >= 3:
            reasons.append(label)
    return reasons or ["Higher overall sustainability score"]


def find_greener_alternatives(original_product: dict, original_score: dict,
                               candidates: list, top_n: int = 3) -> list:
    """
    original_product / candidates: normalised product dicts (see
    data_fetcher.normalize_product). Excludes the original product itself
    (matched by barcode when available, else by name) and anything that
    doesn't actually score higher.
    """
    scored_candidates = []
    original_barcode = original_product.get("barcode")
    original_name = (original_product.get("name") or "").strip().lower()

    for candidate in candidates:
        same_barcode = original_barcode and candidate.get("barcode") == original_barcode
        same_name = original_name and (candidate.get("name") or "").strip().lower() == original_name
        if same_barcode or same_name:
            continue

        candidate_score = compute_sustainability_score(candidate)
        if candidate_score["total"] <= original_score["total"]:
            continue

        scored_candidates.append({
            "product": candidate,
            "score": candidate_score,
            "why_better": _better_factor_labels(original_score, candidate_score),
        })

    scored_candidates.sort(key=lambda item: item["score"]["total"], reverse=True)
    return scored_candidates[:top_n]
