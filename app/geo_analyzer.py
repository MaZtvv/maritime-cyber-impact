"""Parse asset locations and aggregate geographic impact."""

import pandas as pd

from impact_engine import score_to_label

# Known country ISO-3 codes for Plotly choropleth
COUNTRY_ISO3: dict[str, str] = {
    "États-Unis": "USA",
    "etats-unis": "USA",
    "USA": "USA",
    "Émirats Arabes Unis": "ARE",
    "emirats arabes unis": "ARE",
    "Singapour": "SGP",
    "singapour": "SGP",
    "Japon": "JPN",
    "japon": "JPN",
    "Brésil": "BRA",
    "bresil": "BRA",
    "France": "FRA",
    "france": "FRA",
    "Allemagne": "DEU",
    "allemagne": "DEU",
    "Pays-Bas": "NLD",
    "pays-bas": "NLD",
    "Chine": "CHN",
    "chine": "CHN",
    "Corée du Sud": "KOR",
    "coree du sud": "KOR",
    "Royaume-Uni": "GBR",
    "royaume-uni": "GBR",
    "Belgique": "BEL",
    "belgique": "BEL",
    "Espagne": "ESP",
    "espagne": "ESP",
    "Italie": "ITA",
    "italie": "ITA",
    "Canada": "CAN",
    "canada": "CAN",
    "Australie": "AUS",
    "australie": "AUS",
}


def parse_location(location_str: str) -> tuple[str, str]:
    """Return (city, country) from a 'City, Country' string."""
    if not location_str or pd.isna(location_str):
        return ("Unknown", "Unknown")
    parts = str(location_str).rsplit(",", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return parts[0].strip(), "Unknown"


def aggregate_geo_impact(
    all_impacts: dict[str, float],
    asset_index: dict,
) -> pd.DataFrame:
    """Build a DataFrame of geographic impact aggregated by location."""
    from collections import defaultdict

    location_max: dict[str, float] = defaultdict(float)
    location_count: dict[str, int] = defaultdict(int)
    location_country: dict[str, str] = {}

    for asset_id, impact in all_impacts.items():
        info = asset_index.get(asset_id, {})
        raw_loc = info.get("location", "")
        city, country = parse_location(raw_loc)
        key = f"{city}, {country}"
        location_max[key] = max(location_max[key], impact * 100.0)
        location_count[key] += 1
        location_country[key] = country

    rows = []
    for loc, max_imp in location_max.items():
        country = location_country[loc]
        iso3 = COUNTRY_ISO3.get(country, "")
        rows.append({
            "location": loc,
            "country": country,
            "iso3": iso3,
            "max_impact": round(max_imp, 2),
            "asset_count": location_count[loc],
            "severity": score_to_label(max_imp),
        })

    df = pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["location", "country", "iso3", "max_impact", "asset_count", "severity"]
    )
    return df.sort_values("max_impact", ascending=False).reset_index(drop=True)
