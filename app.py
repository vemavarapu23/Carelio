"""
Carelio — Minnesota Food Support Prioritization Dashboard
Professional Data / Business Analyst version

Purpose
-------
This Streamlit app is designed as a decision-support dashboard for nonprofit,
grant, planning, and analytics stakeholders. It uses public county-level data
and transparent planning-level calculations to compare Minnesota counties by
food support priority.

Expected local files
--------------------
1) mn_food_access_data.csv
   Required columns:
   - County
   - Food Need Score
   - Health Risk Score
   - Final Priority Score

Optional local files are NOT required. This version intentionally avoids image
assets and heavy animations so the presentation feels professional.

Important data note
-------------------
Population values are official 2020 Census county counts. People-level numbers
such as estimated food-insecure residents, estimated food shelf visits, SNAP
estimates, and coverage gaps are planning-level estimates created inside this
app. They should be validated with primary source files before formal grant,
policy, or funding submission.
"""

from __future__ import annotations

import io
from typing import Dict, List

import altair as alt
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st


# =============================================================================
# Page setup
# =============================================================================
st.set_page_config(
    page_title="Carelio | MN Food Support Prioritization",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# Links / project metadata
# =============================================================================
SUPPORT_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfbSl0GJBjDDwKk2aMnV_-EHehBS6BmJjRyES5pE6lPMp92pQ/viewform?usp=publish-editor"
EMAIL_ADDRESS = "sruthivemavarapus@outlook.com"
LINKEDIN_URL = "https://www.linkedin.com/in/sruthi-vemavarapu-0b614b198"
GITHUB_URL = "https://github.com/vemavarapu23/Carelio"
LIVE_URL = "https://carelio-mn.streamlit.app/"


# =============================================================================
# County population — US Census Bureau 2020 Decennial Census
# Used as denominator for planning-level people estimates.
# =============================================================================
MN_COUNTY_POPULATION: Dict[str, int] = {
    "Aitkin": 15886,
    "Anoka": 356921,
    "Becker": 34423,
    "Beltrami": 46117,
    "Benton": 40889,
    "Big Stone": 4992,
    "Blue Earth": 67653,
    "Brown": 25153,
    "Carlton": 35404,
    "Carver": 105694,
    "Cass": 29779,
    "Chippewa": 11766,
    "Chisago": 57968,
    "Clay": 64222,
    "Clearwater": 8639,
    "Cook": 5463,
    "Cottonwood": 11080,
    "Crow Wing": 65340,
    "Dakota": 439882,
    "Dodge": 20897,
    "Douglas": 37591,
    "Faribault": 13649,
    "Fillmore": 21179,
    "Freeborn": 30281,
    "Goodhue": 46183,
    "Grant": 5979,
    "Hennepin": 1281565,
    "Houston": 18600,
    "Hubbard": 21357,
    "Isanti": 41622,
    "Itasca": 44976,
    "Jackson": 10566,
    "Kanabec": 16418,
    "Kandiyohi": 42239,
    "Kittson": 4352,
    "Koochiching": 12387,
    "Lac qui Parle": 6623,
    "Lake": 10592,
    "Lake of the Woods": 3843,
    "Le Sueur": 28887,
    "Lincoln": 5639,
    "Lyon": 25857,
    "McLeod": 35642,
    "Mahnomen": 5527,
    "Marshall": 9334,
    "Martin": 19761,
    "Meeker": 23297,
    "Mille Lacs": 26097,
    "Morrison": 33386,
    "Mower": 40062,
    "Murray": 8021,
    "Nicollet": 34274,
    "Nobles": 21959,
    "Norman": 6497,
    "Olmsted": 162847,
    "Otter Tail": 58746,
    "Pennington": 14111,
    "Pine": 29579,
    "Pipestone": 9034,
    "Polk": 31364,
    "Pope": 11249,
    "Ramsey": 547559,
    "Red Lake": 4111,
    "Redwood": 15170,
    "Renville": 14696,
    "Rice": 66972,
    "Rock": 9433,
    "Roseau": 15320,
    "St. Louis": 200080,
    "Scott": 150928,
    "Sherburne": 97238,
    "Sibley": 15058,
    "Stearns": 161075,
    "Steele": 36649,
    "Stevens": 9726,
    "Swift": 9358,
    "Todd": 24800,
    "Traverse": 3271,
    "Wabasha": 21451,
    "Wadena": 13973,
    "Waseca": 18680,
    "Washington": 267568,
    "Watonwan": 10843,
    "Wilkin": 6405,
    "Winona": 50484,
    "Wright": 138377,
    "Yellow Medicine": 9787,
}


# =============================================================================
# Minnesota county FIPS — used by Plotly county map
# =============================================================================
MN_COUNTY_FIPS: Dict[str, str] = {
    "Aitkin": "27001",
    "Anoka": "27003",
    "Becker": "27005",
    "Beltrami": "27007",
    "Benton": "27009",
    "Big Stone": "27011",
    "Blue Earth": "27013",
    "Brown": "27015",
    "Carlton": "27017",
    "Carver": "27019",
    "Cass": "27021",
    "Chippewa": "27023",
    "Chisago": "27025",
    "Clay": "27027",
    "Clearwater": "27029",
    "Cook": "27031",
    "Cottonwood": "27033",
    "Crow Wing": "27035",
    "Dakota": "27037",
    "Dodge": "27039",
    "Douglas": "27041",
    "Faribault": "27043",
    "Fillmore": "27045",
    "Freeborn": "27047",
    "Goodhue": "27049",
    "Grant": "27051",
    "Hennepin": "27053",
    "Houston": "27055",
    "Hubbard": "27057",
    "Isanti": "27059",
    "Itasca": "27061",
    "Jackson": "27063",
    "Kanabec": "27065",
    "Kandiyohi": "27067",
    "Kittson": "27069",
    "Koochiching": "27071",
    "Lac qui Parle": "27073",
    "Lake": "27075",
    "Lake of the Woods": "27077",
    "Le Sueur": "27079",
    "Lincoln": "27081",
    "Lyon": "27083",
    "McLeod": "27085",
    "Mahnomen": "27087",
    "Marshall": "27089",
    "Martin": "27091",
    "Meeker": "27093",
    "Mille Lacs": "27095",
    "Morrison": "27097",
    "Mower": "27099",
    "Murray": "27101",
    "Nicollet": "27103",
    "Nobles": "27105",
    "Norman": "27107",
    "Olmsted": "27109",
    "Otter Tail": "27111",
    "Pennington": "27113",
    "Pine": "27115",
    "Pipestone": "27117",
    "Polk": "27119",
    "Pope": "27121",
    "Ramsey": "27123",
    "Red Lake": "27125",
    "Redwood": "27127",
    "Renville": "27129",
    "Rice": "27131",
    "Rock": "27133",
    "Roseau": "27135",
    "St. Louis": "27137",
    "Scott": "27139",
    "Sherburne": "27141",
    "Sibley": "27143",
    "Stearns": "27145",
    "Steele": "27147",
    "Stevens": "27149",
    "Swift": "27151",
    "Todd": "27153",
    "Traverse": "27155",
    "Wabasha": "27157",
    "Wadena": "27159",
    "Waseca": "27161",
    "Washington": "27163",
    "Watonwan": "27165",
    "Wilkin": "27167",
    "Winona": "27169",
    "Wright": "27171",
    "Yellow Medicine": "27173",
}


# =============================================================================
# Source catalog — displayed in Methodology page and sidebar source expander
# =============================================================================
DATA_SOURCES: List[Dict[str, str]] = [
    {
        "Source": "Feeding America — Map the Meal Gap",
        "Used for": "County food insecurity context / Food Need Index",
        "Update frequency": "Annual, with reporting lag",
        "Primary link": "https://map.feedingamerica.org/",
        "County-level link": "https://map.feedingamerica.org/county/2021/overall/minnesota",
        "Notes": "Used to ground county-level food need context.",
    },
    {
        "Source": "MN DCYF — SNAP County Statistics",
        "Used for": "SNAP participation context",
        "Update frequency": "Monthly / annual files",
        "Primary link": "https://dcyf.mn.gov/snap-food-assistance-minnesota",
        "County-level link": "https://dcyf.mn.gov/sites/default/files/2026-04/rf-food-support-cy-2024.xls",
        "Notes": "Useful to replace planning-level SNAP estimates with official county values.",
    },
    {
        "Source": "The Food Group — Food Shelf Visits Report",
        "Used for": "Food shelf utilization context",
        "Update frequency": "Annual report",
        "Primary link": "https://www.thefoodgroupmn.org",
        "County-level link": "https://www.thefoodgroupmn.org/wp-content/uploads/2025/02/FINAL-Food-Shelf-Visits-2024-Report_22625.pdf",
        "Notes": "Useful for food shelf visit patterns and utilization context.",
    },
    {
        "Source": "Second Harvest Heartland — Statewide Hunger Study",
        "Used for": "Statewide hunger benchmark",
        "Update frequency": "Annual / periodic study",
        "Primary link": "https://www.2harvest.org/about-us/make-hunger-history",
        "County-level link": "https://www.2harvest.org/sites/default/files/2025-01/mhh_2024-statewidehungerstudy_0.pdf",
        "Notes": "Used as statewide benchmark context for food insecurity.",
    },
    {
        "Source": "US Census Bureau — ACS 5-Year Estimates",
        "Used for": "Poverty and socioeconomic risk context / Health Risk Index",
        "Update frequency": "Annual",
        "Primary link": "https://www.census.gov/programs-surveys/acs",
        "County-level link": "https://data.census.gov/table?q=poverty&g=040XX00US27$0500000",
        "Notes": "Useful for poverty and socioeconomic indicators.",
    },
    {
        "Source": "US Census Bureau — 2020 Decennial Census",
        "Used for": "Official county population denominators",
        "Update frequency": "Every 10 years",
        "Primary link": "https://data.census.gov",
        "County-level link": "https://data.census.gov/table?q=population&g=040XX00US27$0500000",
        "Notes": "Used as denominator for people-level planning estimates.",
    },
]


# =============================================================================
# Professional styling
# =============================================================================
st.markdown(
    """
    <style>
    :root {
        --navy: #0f172a;
        --blue: #1d4ed8;
        --blue-soft: #eff6ff;
        --slate: #475569;
        --border: #e2e8f0;
        --bg: #f8fafc;
        --green: #047857;
        --amber: #b45309;
        --red: #b91c1c;
    }

    .stApp {
        background: linear-gradient(180deg, #f8fafc 0%, #ffffff 44%, #f8fafc 100%);
        color: var(--navy);
    }

    .block-container {
        padding-top: 1.4rem;
        padding-bottom: 3rem;
        max-width: 1280px;
    }

    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid var(--border);
    }

    .hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 52%, #334155 100%);
        border-radius: 22px;
        padding: 34px 38px;
        color: white;
        margin-bottom: 22px;
        box-shadow: 0 18px 42px rgba(15, 23, 42, 0.16);
    }

    .eyebrow {
        color: #bfdbfe;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-size: 0.78rem;
        font-weight: 700;
        margin-bottom: 10px;
    }

    .hero h1 {
        font-size: 2.45rem;
        line-height: 1.1;
        margin: 0 0 12px 0;
        font-weight: 800;
    }

    .hero p {
        max-width: 900px;
        color: #dbeafe;
        font-size: 1.02rem;
        line-height: 1.65;
        margin: 0;
    }

    .card {
        background: white;
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 18px 19px;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
    }

    .metric-card {
        background: white;
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 17px 18px;
        min-height: 112px;
        box-shadow: 0 7px 18px rgba(15, 23, 42, 0.05);
    }

    .metric-label {
        color: #64748b;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 8px;
    }

    .metric-value {
        color: #0f172a;
        font-weight: 800;
        font-size: 1.72rem;
        line-height: 1.1;
    }

    .metric-help {
        color: #64748b;
        font-size: 0.86rem;
        margin-top: 8px;
        line-height: 1.4;
    }

    .section-title {
        font-size: 1.24rem;
        font-weight: 800;
        color: #0f172a;
        margin: 26px 0 12px 0;
    }

    .section-subtitle {
        color: #64748b;
        font-size: 0.96rem;
        margin-top: -6px;
        margin-bottom: 16px;
        line-height: 1.55;
    }

    .note-box {
        border-left: 4px solid #2563eb;
        background: #eff6ff;
        color: #1e3a8a;
        border-radius: 12px;
        padding: 14px 16px;
        line-height: 1.6;
        margin: 14px 0;
    }

    .warning-box {
        border-left: 4px solid #b45309;
        background: #fffbeb;
        color: #78350f;
        border-radius: 12px;
        padding: 14px 16px;
        line-height: 1.6;
        margin: 14px 0;
    }

    .success-box {
        border-left: 4px solid #047857;
        background: #ecfdf5;
        color: #064e3b;
        border-radius: 12px;
        padding: 14px 16px;
        line-height: 1.6;
        margin: 14px 0;
    }

    .tier-critical {
        background: #fee2e2;
        color: #991b1b;
        border: 1px solid #fecaca;
        border-radius: 999px;
        padding: 5px 11px;
        font-weight: 800;
        font-size: 0.82rem;
        display: inline-block;
    }

    .tier-high {
        background: #ffedd5;
        color: #9a3412;
        border: 1px solid #fed7aa;
        border-radius: 999px;
        padding: 5px 11px;
        font-weight: 800;
        font-size: 0.82rem;
        display: inline-block;
    }

    .tier-moderate {
        background: #dbeafe;
        color: #1e40af;
        border: 1px solid #bfdbfe;
        border-radius: 999px;
        padding: 5px 11px;
        font-weight: 800;
        font-size: 0.82rem;
        display: inline-block;
    }

    .tier-low {
        background: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
        border-radius: 999px;
        padding: 5px 11px;
        font-weight: 800;
        font-size: 0.82rem;
        display: inline-block;
    }

    .small-text {
        font-size: 0.88rem;
        color: #64748b;
        line-height: 1.5;
    }

    .source-link a {
        color: #1d4ed8;
        text-decoration: none;
        font-weight: 700;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.65rem;
    }

    .stDataFrame {
        border: 1px solid var(--border);
        border-radius: 14px;
        overflow: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# Helper functions
# =============================================================================
def fmt_int(value: float | int | None) -> str:
    """Format a number as a comma-separated integer."""
    if value is None or pd.isna(value):
        return "—"
    return f"{int(round(float(value))):,}"


def fmt_score(value: float | int | None) -> str:
    """Format a score with one decimal point."""
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):.1f}"


def fmt_pct(value: float | int | None) -> str:
    """Format a decimal as a percentage."""
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value) * 100:.1f}%"


def priority_tier(score: float) -> str:
    """Convert composite score into stakeholder-friendly priority tier."""
    if score >= 70:
        return "Critical"
    if score >= 55:
        return "High"
    if score >= 40:
        return "Moderate"
    return "Low"


def tier_order(tier: str) -> int:
    order = {"Critical": 1, "High": 2, "Moderate": 3, "Low": 4}
    return order.get(tier, 99)


def tier_html(tier: str) -> str:
    css = {
        "Critical": "tier-critical",
        "High": "tier-high",
        "Moderate": "tier-moderate",
        "Low": "tier-low",
    }.get(tier, "tier-low")
    return f'<span class="{css}">{tier}</span>'


def insight_for_county(row: pd.Series) -> str:
    """Generate a professional business insight sentence for a selected county."""
    county = row["County"]
    food = float(row["Food Need Score"])
    health = float(row["Health Risk Score"])
    score = float(row["Final Priority Score"])
    tier = row["Priority Tier"]

    if tier == "Critical":
        if food >= 70 and health >= 70:
            driver = "both food need and socioeconomic / health risk are elevated"
        elif food >= health:
            driver = "food need is the primary driver of the ranking"
        else:
            driver = "socioeconomic / health risk is the primary driver of the ranking"
        return (
            f"{county} is classified as Critical because {driver}. "
            f"Its composite score of {score:.1f} indicates it should be reviewed closely for outreach, funding, or service capacity planning."
        )

    if tier == "High":
        return (
            f"{county} is classified as High priority. The county shows an above-average priority signal, "
            f"with a Food Need Index of {food:.1f} and Risk Index of {health:.1f}."
        )

    if tier == "Moderate":
        return (
            f"{county} is in the Moderate tier. The county shows some measurable need, but the combined score "
            f"does not reach the higher-priority threshold in the current dataset."
        )

    return (
        f"{county} is in the Low tier compared with other counties in the current dataset. "
        f"This does not mean there is no need; it means the relative priority score is lower than higher-ranked counties."
    )


@st.cache_data(show_spinner=False)
def load_county_geojson() -> dict:
    """Load US county GeoJSON used for Minnesota county map."""
    url = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


@st.cache_data(show_spinner=False)
def load_data(path: str = "mn_food_access_data.csv") -> pd.DataFrame:
    """Load the county score file and standardize columns."""
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        st.error(
            "The file `mn_food_access_data.csv` was not found. Place it in the same folder as this app.py file."
        )
        st.stop()

    df.columns = [str(c).strip() for c in df.columns]

    required_base = ["County", "Food Need Score", "Health Risk Score"]
    missing = [col for col in required_base if col not in df.columns]
    if missing:
        st.error(
            "Your CSV is missing required columns: " + ", ".join(missing) +
            ". Required columns: County, Food Need Score, Health Risk Score, Final Priority Score."
        )
        st.stop()

    for col in ["Food Need Score", "Health Risk Score", "Final Priority Score"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Fallback if the prepared final score is not available.
    # In the original Carelio file, Final Priority Score is expected from the CSV.
    if "Final Priority Score" not in df.columns:
        df["Final Priority Score"] = (
            df["Food Need Score"] + df["Health Risk Score"]
        ) / 2
        st.info(
            "Final Priority Score was not found in the CSV, so this app used an equal-weight fallback: "
            "(Food Need Score + Health Risk Score) / 2."
        )

    df = df.dropna(subset=["County", "Food Need Score", "Health Risk Score", "Final Priority Score"]).copy()
    df["County"] = df["County"].astype(str).str.strip()

    df["Population"] = df["County"].map(MN_COUNTY_POPULATION).fillna(0).astype(int)
    df["FIPS"] = df["County"].map(MN_COUNTY_FIPS)
    df["Priority Tier"] = df["Final Priority Score"].apply(priority_tier)
    df["Priority Tier Order"] = df["Priority Tier"].apply(tier_order)

    enriched = df.apply(compute_planning_estimates, axis=1, result_type="expand")
    df = pd.concat([df, enriched], axis=1)

    return df.sort_values(
        by=["Priority Tier Order", "Final Priority Score"],
        ascending=[True, False],
    ).reset_index(drop=True)


def compute_planning_estimates(row: pd.Series) -> Dict[str, float | int]:
    """Create planning-level estimates from official population and score-based assumptions.

    Formula summary:
    - Estimated food insecurity rate = 0.08 + (Food Need Score / 100) * 0.20
      This creates a sliding scale from 8% to 28%.
    - Estimated food-insecure residents = Population * estimated food insecurity rate
    - Estimated food shelf visits = Estimated food-insecure residents * 40% * 4.5 visits/year
    - Estimated SNAP rate = 0.04 + (Food Need Score / 100) * 0.07
      This creates a sliding scale from 4% to 11%.
    - Estimated food shelves = max(1, round(Population / 11,700))
      11,700 approximates a statewide person-per-shelf planning benchmark.
    - Coverage gap = Estimated food-insecure residents / estimated food shelves
    """
    county = row["County"]
    population = int(MN_COUNTY_POPULATION.get(county, 0))
    food_score = float(row["Food Need Score"])

    estimated_food_insecurity_rate = 0.08 + (food_score / 100) * 0.20
    estimated_food_insecure_residents = int(population * estimated_food_insecurity_rate)

    estimated_food_shelf_visits = int(estimated_food_insecure_residents * 0.40 * 4.5)

    estimated_snap_rate = 0.04 + (food_score / 100) * 0.07
    estimated_snap_enrollment = int(population * estimated_snap_rate)

    estimated_food_shelves = max(1, round(population / 11_700)) if population > 0 else 0
    coverage_gap = (
        int(estimated_food_insecure_residents / estimated_food_shelves)
        if estimated_food_shelves
        else 0
    )

    return {
        "Estimated Food Insecurity Rate": round(estimated_food_insecurity_rate, 4),
        "Estimated Food-Insecure Residents": estimated_food_insecure_residents,
        "Estimated Food Shelf Visits": estimated_food_shelf_visits,
        "Estimated SNAP Enrollment": estimated_snap_enrollment,
        "Estimated Food Shelves": estimated_food_shelves,
        "Coverage Gap": coverage_gap,
    }


def filter_data(df: pd.DataFrame, selected_tiers: List[str], selected_counties: List[str]) -> pd.DataFrame:
    filtered = df.copy()
    if selected_tiers:
        filtered = filtered[filtered["Priority Tier"].isin(selected_tiers)]
    if selected_counties:
        filtered = filtered[filtered["County"].isin(selected_counties)]
    return filtered.reset_index(drop=True)


def render_metric_card(label: str, value: str, help_text: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-help">{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def source_table_html() -> str:
    rows = []
    for source in DATA_SOURCES:
        rows.append(
            "<tr>"
            f"<td><strong>{source['Source']}</strong></td>"
            f"<td>{source['Used for']}</td>"
            f"<td>{source['Update frequency']}</td>"
            f"<td class='source-link'><a href='{source['Primary link']}' target='_blank'>Primary source</a><br>"
            f"<a href='{source['County-level link']}' target='_blank'>County-level data</a></td>"
            f"<td>{source['Notes']}</td>"
            "</tr>"
        )

    return (
        "<table style='width:100%;border-collapse:collapse;font-size:0.9rem;'>"
        "<thead><tr style='background:#f1f5f9;color:#0f172a;'>"
        "<th style='text-align:left;padding:10px;border:1px solid #e2e8f0;'>Source</th>"
        "<th style='text-align:left;padding:10px;border:1px solid #e2e8f0;'>Used for</th>"
        "<th style='text-align:left;padding:10px;border:1px solid #e2e8f0;'>Update frequency</th>"
        "<th style='text-align:left;padding:10px;border:1px solid #e2e8f0;'>Links</th>"
        "<th style='text-align:left;padding:10px;border:1px solid #e2e8f0;'>Notes</th>"
        "</tr></thead>"
        "<tbody>"
        + "".join(
            row.replace("<td>", "<td style='padding:10px;border:1px solid #e2e8f0;vertical-align:top;'>")
            for row in rows
        )
        + "</tbody></table>"
    )


def build_priority_map(df: pd.DataFrame, selected_county: str | None = None) -> go.Figure:
    """Build Minnesota county choropleth map."""
    map_df = df.dropna(subset=["FIPS"]).copy()
    geojson = load_county_geojson()

    color_map = {
        "Critical": "#dc2626",
        "High": "#f97316",
        "Moderate": "#2563eb",
        "Low": "#16a34a",
    }

    fig = go.Figure()

    # Add one trace per tier for a clean categorical legend.
    for tier in ["Critical", "High", "Moderate", "Low"]:
        tier_df = map_df[map_df["Priority Tier"] == tier].copy()
        if tier_df.empty:
            continue

        fig.add_trace(
            go.Choropleth(
                geojson=geojson,
                locations=tier_df["FIPS"],
                z=[1] * len(tier_df),
                featureidkey="id",
                colorscale=[[0, color_map[tier]], [1, color_map[tier]]],
                showscale=False,
                marker_line_color="white",
                marker_line_width=0.75,
                customdata=tier_df[
                    [
                        "County",
                        "Priority Tier",
                        "Final Priority Score",
                        "Food Need Score",
                        "Health Risk Score",
                        "Estimated Food-Insecure Residents",
                        "Coverage Gap",
                    ]
                ],
                hovertemplate=(
                    "<b>%{customdata[0]} County</b><br>"
                    "Priority Tier: %{customdata[1]}<br>"
                    "Composite Score: %{customdata[2]:.1f}<br>"
                    "Food Need Index: %{customdata[3]:.1f}<br>"
                    "Risk Index: %{customdata[4]:.1f}<br>"
                    "Est. Food-Insecure Residents: %{customdata[5]:,}<br>"
                    "Coverage Gap: %{customdata[6]:,}<extra></extra>"
                ),
                name=tier,
            )
        )

    # Optional selected county outline.
    if selected_county and selected_county in map_df["County"].values:
        selected = map_df[map_df["County"] == selected_county]
        fig.add_trace(
            go.Choropleth(
                geojson=geojson,
                locations=selected["FIPS"],
                z=[1] * len(selected),
                featureidkey="id",
                colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
                showscale=False,
                marker_line_color="#0f172a",
                marker_line_width=3,
                hoverinfo="skip",
                name="Selected County",
            )
        )

    fig.update_geos(
        visible=False,
        projection_type="mercator",
        center={"lat": 46.3, "lon": -94.2},
        lataxis_range=[43.35, 49.55],
        lonaxis_range=[-97.55, -89.0],
    )

    fig.update_layout(
        height=575,
        margin=dict(l=0, r=0, t=8, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            title="Priority Tier",
            orientation="v",
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=1.01,
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor="#e2e8f0",
            borderwidth=1,
        ),
    )

    return fig


def build_top_counties_chart(df: pd.DataFrame, metric: str, top_n: int = 12) -> alt.Chart:
    chart_df = df.nlargest(top_n, metric).sort_values(metric, ascending=True)

    return (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            x=alt.X(metric, title=metric),
            y=alt.Y("County", sort=None, title=None),
            tooltip=[
                alt.Tooltip("County", title="County"),
                alt.Tooltip("Priority Tier", title="Priority Tier"),
                alt.Tooltip("Final Priority Score", title="Composite Score", format=".1f"),
                alt.Tooltip("Food Need Score", title="Food Need Index", format=".1f"),
                alt.Tooltip("Health Risk Score", title="Risk Index", format=".1f"),
                alt.Tooltip("Estimated Food-Insecure Residents", title="Est. Food-Insecure Residents", format=","),
            ],
        )
        .properties(height=360)
    )


def dataframe_for_display(df: pd.DataFrame, view_mode: str) -> pd.DataFrame:
    base_cols = [
        "County",
        "Priority Tier",
        "Final Priority Score",
        "Food Need Score",
        "Health Risk Score",
    ]

    grant_cols = [
        "Population",
        "Estimated Food-Insecure Residents",
        "Estimated Food Insecurity Rate",
        "Estimated Food Shelf Visits",
        "Estimated SNAP Enrollment",
    ]

    planning_cols = [
        "Population",
        "Estimated Food-Insecure Residents",
        "Estimated Food Shelves",
        "Coverage Gap",
    ]

    if view_mode == "Grant & Funding View":
        cols = base_cols + grant_cols
    elif view_mode == "Planning & Coverage View":
        cols = base_cols + planning_cols
    else:
        cols = base_cols

    display_df = df[cols].copy()

    if "Estimated Food Insecurity Rate" in display_df.columns:
        display_df["Estimated Food Insecurity Rate"] = display_df[
            "Estimated Food Insecurity Rate"
        ].apply(lambda x: f"{x * 100:.1f}%")

    for score_col in ["Final Priority Score", "Food Need Score", "Health Risk Score"]:
        if score_col in display_df.columns:
            display_df[score_col] = display_df[score_col].round(1)

    return display_df


# =============================================================================
# Sidebar controls
# =============================================================================
df = load_data()

with st.sidebar:
    st.markdown("### Carelio")
    st.caption("Minnesota food support prioritization dashboard")

    page = st.radio(
        "Navigation",
        [
            "Executive Dashboard",
            "County Deep Dive",
            "Methodology & Data Sources",
            "Business Use Case",
        ],
        index=0,
    )

    st.divider()

    view_mode = st.radio(
        "Stakeholder View",
        ["Data View", "Grant & Funding View", "Planning & Coverage View"],
        index=0,
        help="Changes the table and county details based on stakeholder needs.",
    )

    tier_options = ["Critical", "High", "Moderate", "Low"]
    selected_tiers = st.multiselect(
        "Priority Tier",
        tier_options,
        default=tier_options,
    )

    county_options = sorted(df["County"].unique().tolist())
    selected_counties = st.multiselect(
        "County Filter",
        county_options,
        default=[],
        help="Leave blank to include all counties.",
    )

    st.divider()

    with st.expander("Data transparency note", expanded=False):
        st.write(
            "Population values are official Census 2020 counts. People-level numbers are planning-level estimates "
            "created from population and score-based assumptions. Validate with primary source files before formal reporting."
        )

    with st.expander("Primary data links", expanded=False):
        for source in DATA_SOURCES:
            st.markdown(f"**{source['Source']}**")
            st.markdown(f"[{source['Used for']}]({source['Primary link']})")
            st.markdown(f"[County-level data]({source['County-level link']})")
            st.caption(source["Update frequency"])
            st.markdown("---")

filtered_df = filter_data(df, selected_tiers, selected_counties)

if filtered_df.empty:
    st.warning("No counties match the selected filters. Adjust the sidebar filters to continue.")
    st.stop()

selected_county_for_map = (
    selected_counties[0]
    if len(selected_counties) == 1
    else filtered_df.iloc[0]["County"]
)


# =============================================================================
# Header / hero
# =============================================================================
st.markdown(
    """
    <div class="hero">
        <div class="eyebrow">Decision-support dashboard · Minnesota · County-level analytics</div>
        <h1>Carelio — Minnesota Food Support Prioritization Dashboard</h1>
        <p>
            A professional analytics dashboard that helps nonprofit, grant, and planning teams identify
            where food support resources may need closer attention across Minnesota counties. The dashboard
            combines public source indicators, transparent scoring logic, planning-level estimates, and an
            interactive county map to support data-informed decisions.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# Page: Executive Dashboard
# =============================================================================
if page == "Executive Dashboard":
    total_counties = filtered_df["County"].nunique()
    top_row = filtered_df.sort_values("Final Priority Score", ascending=False).iloc[0]
    critical_count = int((filtered_df["Priority Tier"] == "Critical").sum())
    avg_score = filtered_df["Final Priority Score"].mean()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card(
            "Counties in current view",
            fmt_int(total_counties),
            "Filtered county count used for ranking and comparison.",
        )
    with c2:
        render_metric_card(
            "Highest priority county",
            str(top_row["County"]),
            f"Composite score: {fmt_score(top_row['Final Priority Score'])}",
        )
    with c3:
        render_metric_card(
            "Critical counties",
            fmt_int(critical_count),
            "Counties with composite score of 70 or above.",
        )
    with c4:
        render_metric_card(
            "Average composite score",
            fmt_score(avg_score),
            "Average score across the current filtered view.",
        )

    st.markdown('<div class="section-title">County Priority Map</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Map colors show the Priority Tier. Hover over a county to see the composite score, food need, risk index, estimated food-insecure residents, and coverage gap.</div>',
        unsafe_allow_html=True,
    )

    try:
        st.plotly_chart(
            build_priority_map(filtered_df, selected_county_for_map),
            use_container_width=True,
            config={"displayModeBar": False},
        )
    except Exception as exc:
        st.warning(
            "The county map could not load. This usually happens when the app cannot access the online county GeoJSON file. "
            f"Error: {exc}"
        )

    left, right = st.columns([1.2, 1])

    with left:
        st.markdown('<div class="section-title">Priority Ranking Table</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-subtitle">Use this table as the main analyst view for comparing counties and identifying where deeper review is needed.</div>',
            unsafe_allow_html=True,
        )
        table_df = dataframe_for_display(filtered_df, view_mode)
        st.dataframe(table_df, use_container_width=True, hide_index=True)

        csv_buffer = io.StringIO()
        filtered_df.to_csv(csv_buffer, index=False)
        st.download_button(
            "Download filtered county data",
            data=csv_buffer.getvalue(),
            file_name="carelio_filtered_county_prioritization.csv",
            mime="text/csv",
        )

    with right:
        metric_choice = st.selectbox(
            "Chart metric",
            [
                "Final Priority Score",
                "Food Need Score",
                "Health Risk Score",
                "Estimated Food-Insecure Residents",
                "Coverage Gap",
            ],
            index=0,
        )
        st.markdown('<div class="section-title">Top Counties by Selected Metric</div>', unsafe_allow_html=True)
        st.altair_chart(
            build_top_counties_chart(filtered_df, metric_choice, top_n=min(12, len(filtered_df))),
            use_container_width=True,
        )

    st.markdown(
        """
        <div class="warning-box">
        <strong>Interpretation note:</strong> The dashboard is a decision-support tool. It helps identify where closer review may be needed. 
        Planning-level estimates should be validated with official agency datasets before grant submission, funding allocation, or formal policy reporting.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# Page: County Deep Dive
# =============================================================================
elif page == "County Deep Dive":
    st.markdown('<div class="section-title">County Deep Dive</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Use this page to explain the ranking, drivers, and planning estimates for one selected county.</div>',
        unsafe_allow_html=True,
    )

    default_county = selected_county_for_map if selected_county_for_map in county_options else county_options[0]
    selected_county = st.selectbox(
        "Select county",
        county_options,
        index=county_options.index(default_county),
    )

    row = df[df["County"] == selected_county].iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card(
            "Composite Priority Score",
            fmt_score(row["Final Priority Score"]),
            "Combined county-level priority metric.",
        )
    with c2:
        render_metric_card(
            "Food Need Index",
            fmt_score(row["Food Need Score"]),
            "Relative food support need indicator.",
        )
    with c3:
        render_metric_card(
            "Risk Index",
            fmt_score(row["Health Risk Score"]),
            "Socioeconomic / health vulnerability indicator.",
        )
    with c4:
        render_metric_card(
            "Priority Tier",
            str(row["Priority Tier"]),
            "Tier based on composite score thresholds.",
        )

    st.markdown(
        f"""
        <div class="success-box">
        <strong>Key Driver Summary:</strong> {insight_for_county(row)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    map_col, detail_col = st.columns([1.25, 1])

    with map_col:
        st.markdown('<div class="section-title">County Location on Priority Map</div>', unsafe_allow_html=True)
        try:
            st.plotly_chart(
                build_priority_map(df, selected_county),
                use_container_width=True,
                config={"displayModeBar": False},
            )
        except Exception as exc:
            st.warning(f"Map could not load: {exc}")

    with detail_col:
        st.markdown('<div class="section-title">Planning Details</div>', unsafe_allow_html=True)

        if view_mode == "Data View":
            st.markdown(
                f"""
                <div class="card">
                    <p><strong>Data View</strong> focuses on core analytics metrics used for county comparison.</p>
                    <p><strong>Composite Score:</strong> {fmt_score(row['Final Priority Score'])}</p>
                    <p><strong>Food Need Index:</strong> {fmt_score(row['Food Need Score'])}</p>
                    <p><strong>Risk Index:</strong> {fmt_score(row['Health Risk Score'])}</p>
                    <p><strong>Priority Tier:</strong> {row['Priority Tier']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        elif view_mode == "Grant & Funding View":
            st.markdown(
                f"""
                <div class="card">
                    <p><strong>Grant & Funding View</strong> translates scores into human-scale planning numbers.</p>
                    <p><strong>Population:</strong> {fmt_int(row['Population'])}</p>
                    <p><strong>Estimated food-insecure residents:</strong> {fmt_int(row['Estimated Food-Insecure Residents'])}</p>
                    <p><strong>Estimated food insecurity rate:</strong> {row['Estimated Food Insecurity Rate'] * 100:.1f}%</p>
                    <p><strong>Estimated food shelf visits:</strong> {fmt_int(row['Estimated Food Shelf Visits'])}</p>
                    <p><strong>Estimated SNAP enrollment:</strong> {fmt_int(row['Estimated SNAP Enrollment'])}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
                <div class="note-box">
                <strong>Grant-style wording:</strong> {selected_county} County has an estimated {fmt_int(row['Estimated Food-Insecure Residents'])} residents experiencing food insecurity, based on Census population and Carelio's planning-level food need assumptions. This estimate can help frame outreach and funding conversations, but should be validated with official county-level source data before formal submission.
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:
            st.markdown(
                f"""
                <div class="card">
                    <p><strong>Planning & Coverage View</strong> focuses on service capacity and coverage gap.</p>
                    <p><strong>Population:</strong> {fmt_int(row['Population'])}</p>
                    <p><strong>Estimated food-insecure residents:</strong> {fmt_int(row['Estimated Food-Insecure Residents'])}</p>
                    <p><strong>Estimated food shelves:</strong> {fmt_int(row['Estimated Food Shelves'])}</p>
                    <p><strong>Coverage gap:</strong> {fmt_int(row['Coverage Gap'])} estimated food-insecure residents per estimated food shelf</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                """
                <div class="note-box">
                <strong>Business interpretation:</strong> A higher coverage gap may indicate that the county needs closer review for service reach, partner capacity, transportation barriers, or funding allocation.
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown('<div class="section-title">How This County Was Calculated</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="card">
            <p><strong>1. Population denominator:</strong> {selected_county} County population = {fmt_int(row['Population'])}, from US Census 2020 Decennial Census.</p>
            <p><strong>2. Food insecurity rate estimate:</strong> 0.08 + ({fmt_score(row['Food Need Score'])} / 100) × 0.20 = {row['Estimated Food Insecurity Rate'] * 100:.1f}%.</p>
            <p><strong>3. Estimated food-insecure residents:</strong> {fmt_int(row['Population'])} × {row['Estimated Food Insecurity Rate'] * 100:.1f}% = {fmt_int(row['Estimated Food-Insecure Residents'])}.</p>
            <p><strong>4. Estimated food shelf visits:</strong> {fmt_int(row['Estimated Food-Insecure Residents'])} × 40% × 4.5 visits/year = {fmt_int(row['Estimated Food Shelf Visits'])}.</p>
            <p><strong>5. Estimated SNAP enrollment:</strong> population × score-adjusted SNAP rate = {fmt_int(row['Estimated SNAP Enrollment'])}.</p>
            <p><strong>6. Coverage gap:</strong> estimated food-insecure residents ÷ estimated food shelves = {fmt_int(row['Coverage Gap'])}.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# Page: Methodology & Data Sources
# =============================================================================
elif page == "Methodology & Data Sources":
    st.markdown('<div class="section-title">Methodology & Data Sources</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">This page is written for stakeholder trust: where the data came from, how calculations work, and what should be treated as an estimate.</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="note-box">
        <strong>Professional summary:</strong> Carelio uses a transparent county-level prioritization framework. 
        The dashboard separates source-backed indicators from planning-level estimates so nonprofit, grant, and planning teams understand what is official data and what is calculated for decision support.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">1. Source Catalog</div>', unsafe_allow_html=True)
    st.markdown(source_table_html(), unsafe_allow_html=True)

    st.markdown('<div class="section-title">2. Core Scoring Framework</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            <div class="card">
                <h4>Food Need Index</h4>
                <p>Represents county-level food support need using public food insecurity context.</p>
                <p class="small-text">Primary context: Feeding America Map the Meal Gap.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="card">
                <h4>Risk Index</h4>
                <p>Represents socioeconomic / health-related vulnerability that may increase the severity of food insecurity.</p>
                <p class="small-text">Primary context: US Census ACS and related public indicators.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
            <div class="card">
                <h4>Composite Priority Score</h4>
                <p>Combines food need and risk into one comparable county-level score for ranking.</p>
                <p class="small-text">Used to assign Critical, High, Moderate, and Low priority tiers.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="warning-box">
        <strong>Important:</strong> The app expects the three core scores to be prepared in <code>mn_food_access_data.csv</code>. 
        If <code>Final Priority Score</code> is not found, the app uses a fallback average of Food Need Score and Risk Score. 
        For a production version, the scoring weights and source columns should be locked in a documented data dictionary.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">3. Priority Tier Thresholds</div>', unsafe_allow_html=True)
    threshold_df = pd.DataFrame(
        {
            "Composite Priority Score": ["70+", "55–69", "40–54", "Below 40"],
            "Priority Tier": ["Critical", "High", "Moderate", "Low"],
            "Business Meaning": [
                "Highest priority for review, outreach, funding, or service planning.",
                "Above-average need; should be considered for targeted attention.",
                "Some measurable need; monitor and compare with local context.",
                "Lower relative priority in this dataset; does not mean no need exists.",
            ],
        }
    )
    st.dataframe(threshold_df, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">4. Planning-Level Estimate Calculations</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="card">
        <p><strong>Population</strong> = official county population from US Census Bureau 2020 Decennial Census.</p>
        <p><strong>Estimated food insecurity rate</strong> = 0.08 + (Food Need Index / 100) × 0.20. This creates a sliding range from 8% to 28%.</p>
        <p><strong>Estimated food-insecure residents</strong> = Population × Estimated food insecurity rate.</p>
        <p><strong>Estimated food shelf visits</strong> = Estimated food-insecure residents × 40% × 4.5 visits per year.</p>
        <p><strong>Estimated SNAP enrollment</strong> = Population × [0.04 + (Food Need Index / 100) × 0.07]. This creates a sliding range from 4% to 11%.</p>
        <p><strong>Estimated food shelves</strong> = max(1, round(Population / 11,700)).</p>
        <p><strong>Coverage gap</strong> = Estimated food-insecure residents ÷ Estimated food shelves.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="warning-box">
        <strong>Responsible use:</strong> These estimates are useful for planning conversations and prioritization. 
        They should not be presented as official county counts unless replaced with direct source data from Feeding America, MN DCYF, The Food Group, or another authoritative source.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">5. How to Explain This in a Meeting</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="card">
        <p>
        <strong>Plain English explanation:</strong> Carelio brings multiple public data sources into one county-level decision-support dashboard. 
        I used the source data to create food need and risk indicators, combined them into a composite priority score, and then translated the score into practical planning estimates such as estimated food-insecure residents, food shelf visits, SNAP context, and coverage gap. 
        The goal is to help stakeholders compare counties and decide where deeper review, outreach, or funding attention may be needed.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# Page: Business Use Case
# =============================================================================
elif page == "Business Use Case":
    st.markdown('<div class="section-title">Business Use Case</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">This section positions Carelio as a Data Analyst / Business Analyst solution, not a student project.</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="card">
        <h3>Business Problem</h3>
        <p>
        Nonprofits, grant teams, and planning stakeholders often use separate data sources to understand hunger, SNAP participation, population, and county-level vulnerability. 
        That makes it difficult to quickly identify which counties may need closer attention for funding, outreach, service planning, or partner conversations.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
            <div class="card">
            <h3>Analyst Solution</h3>
            <p>
            Carelio converts public source indicators into a structured county-level prioritization dashboard. 
            It standardizes scores, ranks counties, assigns priority tiers, and provides an interactive map and table for comparison.
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
            <div class="card">
            <h3>Stakeholder Value</h3>
            <p>
            The dashboard helps users move from raw public data to a practical decision-support view: where to review, where to target outreach, and where funding or service capacity conversations may be useful.
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-title">Stakeholder Views</div>', unsafe_allow_html=True)
    view_df = pd.DataFrame(
        {
            "View": ["Data View", "Grant & Funding View", "Planning & Coverage View"],
            "Primary User": ["Data analyst / internal reporting team", "Grant writers / donors / nonprofit leadership", "Program planners / policy stakeholders"],
            "Main Question Answered": [
                "Which counties rank highest by score?",
                "How large is the potential human impact?",
                "Where might service coverage gaps need review?",
            ],
            "Key Outputs": [
                "Composite score, food need, risk index, priority tier",
                "Estimated residents, estimated visits, SNAP context",
                "Estimated food shelves, coverage gap, planning interpretation",
            ],
        }
    )
    st.dataframe(view_df, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">Professional Project Summary</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="success-box">
        <strong>Resume / interview wording:</strong> Built a county-level decision-support dashboard using Python, Pandas, Streamlit, and public Minnesota datasets to prioritize food support needs across 87 counties. Designed a transparent scoring framework, interactive county map, stakeholder-specific views, and planning-level estimates to support nonprofit outreach, grant, and resource planning decisions.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">Recommended Next Improvements</div>', unsafe_allow_html=True)
    next_steps = pd.DataFrame(
        {
            "Improvement": [
                "Replace estimates with official county counts",
                "Add refresh date and data dictionary",
                "Add trend analysis",
                "Add export-ready grant summary",
                "Add QA checks",
            ],
            "Business Value": [
                "Improves credibility for formal grant and policy use.",
                "Improves stakeholder trust and repeatability.",
                "Shows whether county need is increasing or decreasing over time.",
                "Helps non-technical users quickly reuse insights.",
                "Makes the dashboard more production-ready.",
            ],
        }
    )
    st.dataframe(next_steps, use_container_width=True, hide_index=True)


# =============================================================================
# Footer
# =============================================================================
st.divider()
st.markdown(
    f"""
    <div class="small-text">
    <strong>Carelio</strong> · Minnesota Food Support Prioritization Dashboard · Built for decision support using public data and transparent planning assumptions. 
    Contact: <a href="mailto:{EMAIL_ADDRESS}">{EMAIL_ADDRESS}</a> · 
    <a href="{GITHUB_URL}" target="_blank">GitHub</a> · 
    <a href="{LIVE_URL}" target="_blank">Live App</a>
    </div>
    """,
    unsafe_allow_html=True,
)
