"""
Unit tests for scanner/scoring.py.
Run from the project root with:  pytest
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner.scoring import (  # noqa: E402
    compute_sustainability_score,
    packaging_score,
    sourcing_score,
    transport_score,
    labor_score,
)
from scanner.utils import band_for_score, estimate_distance_km  # noqa: E402


def test_sourcing_score_rewards_positive_language():
    green_text = "organic sustainably sourced recycled biodegradable materials"
    plain_text = "synthetic virgin plastic materials"
    assert sourcing_score(green_text) > sourcing_score(plain_text)


def test_sourcing_score_stays_in_bounds():
    assert 0 <= sourcing_score("") <= 25
    assert 0 <= sourcing_score("organic " * 50) <= 25


def test_packaging_score_prefers_cardboard_over_plastic():
    assert packaging_score("recyclable cardboard box") > packaging_score("single-use plastic film")


def test_transport_score_prefers_closer_origin():
    assert transport_score("India") > transport_score("United States")
    assert transport_score("India") == 25.0


def test_transport_score_handles_unknown_country():
    # Unknown country should fall back to the conservative default distance,
    # not crash or return an out-of-range score.
    score = transport_score("Atlantis")
    assert 0 <= score <= 25


def test_labor_score_neutral_without_penalising_missing_labels():
    # No label present -> neutral baseline, not zero (see fairness note in scoring.py)
    neutral = labor_score("")
    assert neutral > 0
    assert labor_score("fair trade certified") > neutral


def test_total_score_within_0_100():
    product = {
        "materials_text": "organic cotton",
        "packaging_text": "recyclable cardboard",
        "origin_country": "India",
        "labels_text": "fair trade",
    }
    result = compute_sustainability_score(product)
    assert 0 <= result["total"] <= 100
    assert result["total"] == round(
        result["sourcing"] + result["packaging"] + result["transport"] + result["labor"], 1
    )


def test_band_for_score_matches_logbook_thresholds():
    assert band_for_score(10)[0] == "Needs improvement"
    assert band_for_score(55)[0] == "Okay choice"
    assert band_for_score(90)[0] == "Great choice"


def test_estimate_distance_km_known_and_unknown():
    assert estimate_distance_km("India") < estimate_distance_km("United States")
    assert estimate_distance_km("Nowhereland") > 0  # falls back to default, doesn't crash
