"""
Rough straight-line distances (in km) from New Delhi, India to a product's
country of origin. This is a deliberately simple stand-in for real shipping-
route/logistics data (which would need a paid freight API) -- good enough to
rank products as "local," "regional," or "far-shipped" for a school prototype.

NOTE: If you retarget this app to a different country, just change the
reference point in the comment above and update the distances.
"""

COUNTRY_DISTANCE_FROM_INDIA_KM = {
    "India": 300,             # treated as short/domestic when exact city is unknown
    "Nepal": 900,
    "Pakistan": 700,
    "Bangladesh": 1200,
    "Sri Lanka": 2500,
    "Myanmar": 2200,
    "China": 3800,
    "Vietnam": 3200,
    "Thailand": 3000,
    "Malaysia": 3900,
    "Indonesia": 4700,
    "Philippines": 4600,
    "Singapore": 3800,
    "Japan": 5800,
    "South Korea": 4700,
    "Turkey": 4300,
    "United Arab Emirates": 1900,
    "Saudi Arabia": 2700,
    "Israel": 4100,
    "Egypt": 4400,
    "Kenya": 5100,
    "South Africa": 7900,
    "Nigeria": 7200,
    "United Kingdom": 6700,
    "Germany": 5900,
    "France": 6600,
    "Italy": 5800,
    "Spain": 7300,
    "Portugal": 7600,
    "Netherlands": 6200,
    "Belgium": 6300,
    "Switzerland": 5700,
    "Sweden": 5900,
    "Poland": 5400,
    "Russia": 4400,
    "United States": 12000,
    "Canada": 11500,
    "Mexico": 14700,
    "Brazil": 13500,
    "Argentina": 15600,
    "Australia": 10400,
    "New Zealand": 12600,
}

# Used whenever the origin country is missing or not in the table above --
# deliberately on the higher/more-conservative side.
DEFAULT_DISTANCE_KM = 6000
