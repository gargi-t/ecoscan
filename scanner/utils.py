"""Small helper functions shared across the EcoScan scoring engine."""

from scanner.geo_data import COUNTRY_DISTANCE_FROM_INDIA_KM, DEFAULT_DISTANCE_KM

# Rough published estimate for a full smartphone charge, used only to turn a
# small CO2 number into something a shopper can picture. Not a certified
# figure -- see README for sourcing notes.
CO2_KG_PER_SMARTPHONE_CHARGE = 0.0083

# kg CO2 per km "per unit shipped" -- a simplified, illustrative transport
# emission factor, not a certified logistics calculation.
EMISSION_FACTOR_KG_PER_KM = 0.00006


def estimate_distance_km(origin_country: str) -> float:
    """Looks up an approximate shipping distance for a product's origin
    country. Falls back to a conservative default if we don't recognise the
    country name (e.g. it arrived as an OpenFoodFacts tag like 'en:france')."""
    if not origin_country:
        return DEFAULT_DISTANCE_KM
    cleaned = origin_country.strip().title()
    return COUNTRY_DISTANCE_FROM_INDIA_KM.get(cleaned, DEFAULT_DISTANCE_KM)


def band_for_score(score: float):
    """Maps a 0-100 sustainability score to the red/yellow/green bands from
    Logbook section 8 (Prototype) -- 0-40 / 41-70 / 71-100."""
    score = max(0, min(100, score))
    if score <= 40:
        return "Needs improvement", "#E4572E"
    elif score <= 70:
        return "Okay choice", "#F3A712"
    else:
        return "Great choice", "#2E933C"


def estimate_co2_kg(distance_km: float, score_gap: float) -> float:
    """Very rough, illustrative CO2 estimate used for the 'impact summary'
    message -- scales with how much farther the current product travelled
    and how much better the alternative scores. This is a teaching aid, not
    a verified carbon accounting figure."""
    score_gap = max(score_gap, 0)
    return round(distance_km * EMISSION_FACTOR_KG_PER_KM * (score_gap / 100), 3)


def co2_to_smartphone_charges(co2_kg: float) -> int:
    if co2_kg <= 0:
        return 0
    return round(co2_kg / CO2_KG_PER_SMARTPHONE_CHARGE)


def impact_summary_message(current_score: float, alt_name: str, alt_score: float, origin_country: str) -> str:
    """Builds the friendly 'Impact Summary' sentence described in Logbook
    section 8 (Prototype > Visualization for the end user)."""
    distance_km = estimate_distance_km(origin_country)
    gap = alt_score - current_score
    if gap <= 0 or not alt_name:
        return "This product already scores as well as the greener alternatives we could find."
    co2_kg = estimate_co2_kg(distance_km, gap)
    charges = co2_to_smartphone_charges(co2_kg)
    return (
        f"By switching to {alt_name}, you could save approximately {co2_kg} kg of CO2 "
        f"-- roughly equivalent to charging a smartphone {charges} times."
    )
