import base64
import io
import gzip
import json
import math
from html import escape
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import altair as alt
from pathlib import Path
import re
from urllib.parse import urlencode, urlsplit

st.set_page_config(page_title="Carelio", layout="wide")

# ============================================================
# Food-shelf directory helpers (included in app.py)
# ============================================================
DIRECTORY_URL = "https://www.hungersolutions.org/find-help/"
DATA_PATH = Path(__file__).with_name("food_shelves_mn.csv")
REQUIRED = (
    "Source_ID", "County", "Food_Shelf_Name", "Address", "Source_URL", "Retrieved_On"
)
OPTIONAL = ("City", "Phone", "Website", "Service_Type", "Status")


def normalize_county(value):
    value = re.sub(r"\s+county$", "", str(value).strip(), flags=re.I)
    value = re.sub(r"\s+", " ", value).casefold()
    return re.sub(r"^(saint|st\.)\s+", "st ", value)


def safe_url(value):
    value = str(value).strip()
    try:
        parsed = urlsplit(value)
        return value if parsed.scheme in {"https", "http"} and parsed.netloc else ""
    except ValueError:
        return ""


def load_food_shelves(path=DATA_PATH, valid_counties=None):
    """Return (validated records, diagnostic). Never turn a broken file into zeroes."""
    empty = pd.DataFrame(columns=[*REQUIRED, *OPTIONAL, "_county_key"])
    try:
        frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    except (OSError, ValueError, UnicodeError) as exc:
        return empty, f"Food-shelf data could not be loaded: {type(exc).__name__}."
    if not set(REQUIRED).issubset(frame.columns):
        return empty, "Food-shelf data is missing required columns."
    frame = frame.fillna("").copy()
    for col in frame:
        frame[col] = frame[col].astype(str).str.strip()
    for col in OPTIONAL:
        if col not in frame:
            frame[col] = ""
    frame["_county_key"] = frame["County"].map(normalize_county)
    for col in ["Website", "Source_URL"]:
        frame[col] = frame[col].map(safe_url)
    valid = frame[list(REQUIRED)].ne("").all(axis=1)
    dates = pd.to_datetime(frame["Retrieved_On"], format="%Y-%m-%d", errors="coerce")
    valid &= dates.notna() & (dates <= pd.Timestamp.now().normalize())
    if valid_counties is not None:
        valid &= frame["_county_key"].isin({normalize_county(c) for c in valid_counties})
    # Fail visibly instead of silently publishing misleading counts from malformed data.
    if not valid.all():
        return empty, "Food-shelf data contains incomplete or invalid records and needs review."
    if frame["Source_ID"].duplicated().any():
        return empty, "Food-shelf data contains repeated source IDs and needs review."
    identity = frame.apply(
        lambda r: "|".join(re.sub(r"[^a-z0-9]", "", r[c].casefold())
                           for c in ["County", "Food_Shelf_Name", "Address"]), axis=1
    )
    frame = frame.loc[~identity.duplicated()].copy()
    return frame.sort_values(["County", "Food_Shelf_Name"]).reset_index(drop=True), ""


def county_shelves(frame, county):
    return frame.loc[frame["_county_key"] == normalize_county(county)].copy()


def county_listing_count(frame, county, error=""):
    return None if error else len(county_shelves(frame, county))


def render_food_shelves(frame, county, error=""):
    st.subheader(f"🥫 Food Shelves in {county} County")
    if error:
        st.info("Food-shelf listings are temporarily unavailable. Use the directory below to find help.")
        with st.expander("Data loading details"):
            st.text(error)
        st.link_button("Find food support", DIRECTORY_URL)
        return

    selected = county_shelves(frame, county)
    if selected.empty:
        st.info(
            f"No listings matched {county} County in this snapshot. "
            "This does not mean there are no food shelves or no services for its residents. "
            "Nearby counties may also have options."
        )
        st.link_button("Search the full food-support directory", DIRECTORY_URL)
        return

    noun = "food-shelf listing" if len(selected) == 1 else "food-shelf listings"
    st.write(f"**{len(selected)} {noun}** in {county} County.")
    st.caption(
        "Contact the provider before visiting to confirm hours, appointments and eligibility. "
        "Listings include some mobile and restricted-access programs; some share an address."
    )
    query = st.text_input(
        "Find a food shelf or city", placeholder="Search these listings",
        key=f"shelf_search_{normalize_county(county)}",
    ).strip()
    visible = selected
    if query:
        mask = selected[["Food_Shelf_Name", "City", "Address"]].apply(
            lambda s: s.str.contains(query, case=False, regex=False)
        ).any(axis=1)
        visible = selected.loc[mask]
        st.caption(f"Showing {len(visible)} of {len(selected)} listings.")

    if visible.empty:
        st.info("No listings match that search. Try the city name or clear the search.")
    else:
        display = visible[["Food_Shelf_Name", "City", "Address", "Phone", "Website"]].copy()
        display["Directions"] = visible["Address"].map(
            lambda address: "https://www.google.com/maps/search/?" + urlencode({"api": "1", "query": address})
        )
        for col in ["City", "Address", "Phone"]:
            display[col] = display[col].replace("", "Not listed")
        display["Website"] = display["Website"].replace("", None)
        display = display.rename(columns={"Food_Shelf_Name": "Food shelf", "Phone": "Contact"})
        # A real HTML table keeps both text and backgrounds readable in dark or light mode.
        rows = []
        for record in display.to_dict("records"):
            cells = []
            for column in display.columns:
                value = record[column]
                if column in {"Website", "Directions"}:
                    url = safe_url(value) if value else ""
                    label = "Visit website" if column == "Website" else "View location"
                    content = (
                        f'<a href="{escape(url, quote=True)}" target="_blank" '
                        f'rel="noopener noreferrer">{label}</a>' if url else "Not listed"
                    )
                else:
                    content = escape(str(value))
                cells.append(f"<td>{content}</td>")
            rows.append("<tr>" + "".join(cells) + "</tr>")
        headers = "".join(f'<th scope="col">{escape(c)}</th>' for c in display.columns)
        st.markdown(
            '<div class="shelf-table-scroll" role="region" aria-label="County food-shelf listings" tabindex="0">'
            '<table class="shelf-table"><thead><tr>' + headers + '</tr></thead><tbody>'
            + "".join(rows) + '</tbody></table></div>', unsafe_allow_html=True,
        )

    st.caption(
        "Source: The Food Group / Hunger Solutions, Find Help directory. "
        f"Retrieved: {', '.join(sorted(selected['Retrieved_On'].unique()))}. "
        "Listed addresses determine counties; service areas may cross county borders. "
        "The count does not measure capacity or show that all local services are included."
    )
    left, right = st.columns(2)
    with left:
        st.link_button("Open the source directory", DIRECTORY_URL)
    with right:
        export = selected.drop(columns=[c for c in selected if c.startswith("_")])
        st.download_button(
            "Download county food shelves", export.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"carelio_{normalize_county(county).replace(' ', '_')}_food_shelves.csv",
            mime="text/csv", key=f"shelf_download_{normalize_county(county)}",
        )
    st.info(
        "Next step: contact these providers to understand current services and capacity "
        "before planning additional support."
    )


def build_county_comparison(data, first, second, shelves, shelf_error=""):
    """Use existing county values; directory counts never change priority scores."""
    if first == second:
        raise ValueError("Choose two different counties.")
    indexed = data.set_index("County")
    a, b = indexed.loc[first], indexed.loc[second]
    ranks = indexed["Final Priority Score"].rank(method="min", ascending=False)
    counts = [county_listing_count(shelves, name, shelf_error) for name in [first, second]]

    def count_label(value):
        if value is None:
            return "Unavailable"
        return "No listings in snapshot" if value == 0 else str(value)

    rows = [
        ("Priority score (0–100)", f"{a['Final Priority Score']:.2f}", f"{b['Final Priority Score']:.2f}"),
        ("Priority level", a["Urgency Level"], b["Urgency Level"]),
        ("Rank across all counties", f"#{int(ranks[first])} of {len(indexed)}", f"#{int(ranks[second])} of {len(indexed)}"),
        ("Food need score (0–100)", f"{a['Food Need Score']:.2f}", f"{b['Food Need Score']:.2f}"),
        ("Health risk score (0–100)", f"{a['Health Risk Score']:.2f}", f"{b['Health Risk Score']:.2f}"),
        ("Population · 2020 Census", f"{int(a['Population']):,}", f"{int(b['Population']):,}"),
        ("People facing food insecurity · model estimate", f"~{int(a['Est. People Food Insecure']):,}", f"~{int(b['Est. People Food Insecure']):,}"),
        ("Food-shelf directory listings", count_label(counts[0]), count_label(counts[1])),
    ]
    table = pd.DataFrame(rows, columns=["Indicator", first, second])
    messages = []
    difference = round(float(a["Final Priority Score"] - b["Final Priority Score"]), 2)
    if difference == 0:
        messages.append(f"{first} and {second} have the same priority score. Review the food need and health risk scores to understand the mix behind that result.")
    else:
        higher, lower = (first, second) if difference > 0 else (second, first)
        messages.append(f"{higher} has the higher priority score by {abs(difference):.2f} points. It shows greater combined food need and health risk in Carelio's scoring model than {lower}.")
    pop_difference = int(a["Population"]) - int(b["Population"])
    if pop_difference == 0:
        messages.append("Both counties have the same population in the 2020 Census data.")
    else:
        larger = first if pop_difference > 0 else second
        messages.append(f"{larger} has {abs(pop_difference):,} more residents in the 2020 Census data. This helps you understand the possible scale of outreach.")
    if shelf_error:
        messages.append("Food-shelf listings are unavailable, so a directory comparison cannot be made right now.")
    elif 0 in counts:
        missing = first if counts[0] == 0 else second
        if counts == [0, 0]:
            messages.append("Neither county has matching listings in this snapshot. This does not mean that food support is unavailable to residents.")
        else:
            messages.append(f"No directory listings match {missing} in this snapshot. This does not mean the county has no food shelves or that its residents have no support.")
    else:
        first_noun = "listing" if counts[0] == 1 else "listings"
        second_noun = "listing" if counts[1] == 1 else "listings"
        messages.append(f"The directory contains {counts[0]} {first_noun} for {first} and {counts[1]} {second_noun} for {second}. These counts show listed programs, not how many people they can serve.")
    return table, messages


def render_county_compare(data, shelves, shelf_error=""):
    counties = sorted(data["County"].dropna().unique().tolist())
    if len(counties) < 2:
        st.info("At least two counties are needed for a comparison.")
        return
    if st.session_state.get("compare_first") not in counties:
        st.session_state.compare_first = "Mahnomen" if "Mahnomen" in counties else counties[0]

    with st.container(border=True, key="county_compare_panel"):
        st.subheader("⚖️ Compare two counties")
        st.write("Choose two counties to see their need, population and listed food shelves together.")
        st.caption("You can choose from all counties, regardless of the dashboard's urgency filter.")
        left, right = st.columns(2)
        with left:
            first = st.selectbox("First county", counties, key="compare_first")
        remaining = [name for name in counties if name != first]
        if st.session_state.get("compare_second") not in remaining:
            st.session_state.compare_second = "Beltrami" if "Beltrami" in remaining else remaining[0]
        with right:
            second = st.selectbox("Second county", remaining, key="compare_second")

        table, messages = build_county_comparison(data, first, second, shelves, shelf_error)
        headers = "".join(f'<th scope="col">{escape(str(c))}</th>' for c in table.columns)
        body = "".join(
            '<tr><th scope="row">' + escape(str(row[0])) + '</th>'
            + "".join(f'<td>{escape(str(value))}</td>' for value in row[1:]) + '</tr>'
            for row in table.itertuples(index=False, name=None)
        )
        st.markdown(
            '<div class="shelf-table-scroll" role="region" aria-label="County comparison" tabindex="0">'
            '<table class="shelf-table compare-table"><thead><tr>' + headers
            + '</tr></thead><tbody>' + body + '</tbody></table></div>',
            unsafe_allow_html=True,
        )
        st.caption("Higher scores indicate greater relative need. Scores are not percentages of residents.")
        st.subheader("What does this tell us?")
        for message in messages:
            st.write("• " + message)
        st.info("Next step: review the county indicators and speak with local food-support providers about current needs, eligibility and capacity before deciding where to add support.")

        with st.expander("What do these numbers mean?"):
            st.markdown("""
**Priority score and level:** Carelio combines food need and health risk to help compare counties. Critical, High, Moderate and Low are the existing score bands.

**Rank:** Where the county sits among all counties in the dataset. A rank of 1 means the highest priority score. Tied scores share a rank.

**Food need and health risk scores:** Summaries of the county indicators already used in Carelio. They are relative scores, not counts of people.

**Population:** The county's total residents counted in the 2020 Census.

**People facing food insecurity — model estimate:** An estimate from Carelio's existing population-and-score assumptions. It is not an official county count or a prediction of how many people will visit a food shelf.

**Food-shelf directory listings:** Programs matched to the county in the directory snapshot. Some are mobile, have eligibility rules or share an address. Fewer listings alone do not prove a shortage of services.
""")
        snapshot = ", ".join(sorted(shelves["Retrieved_On"].unique())) if not shelf_error and not shelves.empty else "Unavailable"
        st.caption(f"Sources: existing Carelio county indicators; 2020 Census population; food-shelf directory snapshot: {snapshot}.")
        st.markdown("[Food-shelf source directory](https://www.hungersolutions.org/find-help/) · [Census population source](https://data.census.gov/table?q=population&g=040XX00US27$0500000)")
        export = table.copy()
        export["Food-shelf snapshot"] = snapshot
        export["Notes"] = "Scores are relative; people counts are model estimates except Census population; directory listings do not measure capacity."
        st.download_button(
            "Download this comparison", export.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"carelio_compare_{normalize_county(first).replace(' ', '_')}_{normalize_county(second).replace(' ', '_')}.csv",
            mime="text/csv", key="compare_download",
        )


# ============================================================
# Links
# ============================================================
SUPPORT_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfbSl0GJBjDDwKk2aMnV_-EHehBS6BmJjRyES5pE6lPMp92pQ/viewform?usp=publish-editor"
EMAIL_ADDRESS    = "sruthivemavarapus@outlook.com"
LINKEDIN_URL     = "https://www.linkedin.com/in/sruthi-vemavarapu-0b614b198"
GITHUB_URL       = "https://github.com/vemavarapu23/Carelio"
LIVE_URL         = "https://carelio-mn.streamlit.app/"

# ============================================================
# County Populations — US Census Bureau 2020 Decennial Census
# ============================================================
MN_COUNTY_POPULATION = {
    "Aitkin":15886,"Anoka":356921,"Becker":34423,"Beltrami":46117,
    "Benton":40889,"Big Stone":4992,"Blue Earth":67653,"Brown":25153,
    "Carlton":35404,"Carver":105694,"Cass":29779,"Chippewa":11766,
    "Chisago":57968,"Clay":64222,"Clearwater":8639,"Cook":5463,
    "Cottonwood":11080,"Crow Wing":65340,"Dakota":439882,"Dodge":20897,
    "Douglas":37591,"Faribault":13649,"Fillmore":21179,"Freeborn":30281,
    "Goodhue":46183,"Grant":5979,"Hennepin":1281565,"Houston":18600,
    "Hubbard":21357,"Isanti":41622,"Itasca":44976,"Jackson":10566,
    "Kanabec":16418,"Kandiyohi":42239,"Kittson":4352,"Koochiching":12387,
    "Lac qui Parle":6623,"Lake":10592,"Lake of the Woods":3843,
    "Le Sueur":28887,"Lincoln":5639,"Lyon":25857,"McLeod":35642,
    "Mahnomen":5527,"Marshall":9334,"Martin":19761,"Meeker":23297,
    "Mille Lacs":26097,"Morrison":33386,"Mower":40062,"Murray":8021,
    "Nicollet":34274,"Nobles":21959,"Norman":6497,"Olmsted":162847,
    "Otter Tail":58746,"Pennington":14111,"Pine":29579,"Pipestone":9034,
    "Polk":31364,"Pope":11249,"Ramsey":547559,"Red Lake":4111,
    "Redwood":15170,"Renville":14696,"Rice":66972,"Rock":9433,
    "Roseau":15320,"St. Louis":200080,"Scott":150928,"Sherburne":97238,
    "Sibley":15058,"Stearns":161075,"Steele":36649,"Stevens":9726,
    "Swift":9358,"Todd":24800,"Traverse":3271,"Wabasha":21451,
    "Wadena":13973,"Waseca":18680,"Washington":267568,"Watonwan":10843,
    "Wilkin":6405,"Winona":50484,"Wright":138377,"Yellow Medicine":9787,
}

# ============================================================
# Data Sources (with county-level download links)
# ============================================================
DATA_SOURCES = [
    {
        "emoji":"🥫", "name":"The Food Group / Hunger Solutions — Find Help",
        "what":"Food-shelf directory listings, addresses, contacts and provider links. Includes some mobile and restricted-access programs.",
        "frequency":"Local snapshot retrieved September 1, 2026; confirm details with providers",
        "url":"https://www.hungersolutions.org/find-help/",
        "county_url":"https://www.hungersolutions.org/find-help/?fwp_categories=food-shelves",
        "county_label":"Open food-shelf directory",
        "used_for":"Food-shelf listings by county; not service capacity or coverage",
    },
    {
        "emoji":"🟩","name":"Feeding America — Map the Meal Gap",
        "what":"County food insecurity rates & food budget shortfall. US rate: 14.3% in 2023.",
        "frequency":"Annual (~2-year reporting lag)",
        "url":"https://map.feedingamerica.org/",
        "county_url":"https://map.feedingamerica.org/county/2021/overall/minnesota",
        "county_label":"View MN county-level data",
        "used_for":"Food Need Score",
    },
    {
        "emoji":"🟦","name":"MN DCYF — SNAP County Statistics",
        "what":"Monthly county SNAP cases, persons enrolled, benefit amounts.",
        "frequency":"Monthly (CY2024 available)",
        "url":"https://dcyf.mn.gov/snap-food-assistance-minnesota",
        "county_url":"https://dcyf.mn.gov/sites/default/files/2026-04/rf-food-support-cy-2024.xls",
        "county_label":"Download CY2024 county Excel",
        "used_for":"SNAP enrollment context",
    },
    {
        "emoji":"🟪","name":"The Food Group — Food Shelf Visits 2024",
        "what":"Annual food shelf visit counts across 487 TEFAP sites. 2024: +18.4% avg increase.",
        "frequency":"Annual (2024 report: Feb 2025)",
        "url":"https://www.thefoodgroupmn.org",
        "county_url":"https://www.thefoodgroupmn.org/wp-content/uploads/2025/02/FINAL-Food-Shelf-Visits-2024-Report_22625.pdf",
        "county_label":"Download 2024 county report PDF",
        "used_for":"Food shelf utilization",
    },
    {
        "emoji":"🟧","name":"Second Harvest Heartland — Statewide Hunger Study",
        "what":"Household survey with Wilder Research. 1 in 5 MN households food insecure (2024).",
        "frequency":"Annual (Jan 2025)",
        "url":"https://www.2harvest.org/about-us/make-hunger-history",
        "county_url":"https://www.2harvest.org/sites/default/files/2025-01/mhh_2024-statewidehungerstudy_0.pdf",
        "county_label":"Download full study PDF",
        "used_for":"Statewide benchmarks",
    },
    {
        "emoji":"⬜","name":"County Health Rankings & Roadmaps — Minnesota Health Data",
        "what":"County-level health outcomes, health factors, and social/economic indicators.",
        "frequency":"Annual",
        "url":"https://www.countyhealthrankings.org/health-data/minnesota/data-and-resources",
        "county_url":"https://www.countyhealthrankings.org/health-data/minnesota/data-and-resources",
        "county_label":"View Minnesota county-level health data",
        "used_for":"Health Risk Score",
    },
    {
        "emoji":"🔲","name":"US Census Bureau — 2020 Decennial Census",
        "what":"Official county population counts. Used as denominators for all people-level estimates.",
        "frequency":"Every 10 years (next: 2030)",
        "url":"https://data.census.gov",
        "county_url":"https://data.census.gov/table?q=population&g=040XX00US27$0500000",
        "county_label":"View MN county population data",
        "used_for":"Population denominators",
    },
]

# ============================================================
# Minnesota County FIPS
# ============================================================
MN_COUNTY_FIPS = {
    "Aitkin":"27001","Anoka":"27003","Becker":"27005","Beltrami":"27007",
    "Benton":"27009","Big Stone":"27011","Blue Earth":"27013","Brown":"27015",
    "Carlton":"27017","Carver":"27019","Cass":"27021","Chippewa":"27023",
    "Chisago":"27025","Clay":"27027","Clearwater":"27029","Cook":"27031",
    "Cottonwood":"27033","Crow Wing":"27035","Dakota":"27037","Dodge":"27039",
    "Douglas":"27041","Faribault":"27043","Fillmore":"27045","Freeborn":"27047",
    "Goodhue":"27049","Grant":"27051","Hennepin":"27053","Houston":"27055",
    "Hubbard":"27057","Isanti":"27059","Itasca":"27061","Jackson":"27063",
    "Kanabec":"27065","Kandiyohi":"27067","Kittson":"27069","Koochiching":"27071",
    "Lac qui Parle":"27073","Lake":"27075","Lake of the Woods":"27077",
    "Le Sueur":"27079","Lincoln":"27081","Lyon":"27083","McLeod":"27085",
    "Mahnomen":"27087","Marshall":"27089","Martin":"27091","Meeker":"27093",
    "Mille Lacs":"27095","Morrison":"27097","Mower":"27099","Murray":"27101",
    "Nicollet":"27103","Nobles":"27105","Norman":"27107","Olmsted":"27109",
    "Otter Tail":"27111","Pennington":"27113","Pine":"27115","Pipestone":"27117",
    "Polk":"27119","Pope":"27121","Ramsey":"27123","Red Lake":"27125",
    "Redwood":"27127","Renville":"27129","Rice":"27131","Rock":"27133",
    "Roseau":"27135","St. Louis":"27137","Scott":"27139","Sherburne":"27141",
    "Sibley":"27143","Stearns":"27145","Steele":"27147","Stevens":"27149",
    "Swift":"27151","Todd":"27153","Traverse":"27155","Wabasha":"27157",
    "Wadena":"27159","Waseca":"27161","Washington":"27163","Watonwan":"27165",
    "Wilkin":"27167","Winona":"27169","Wright":"27171","Yellow Medicine":"27173",
}

# ============================================================
# Original helpers
# ============================================================
def get_base64_image(path):
    with open(path,"rb") as f: return base64.b64encode(f.read()).decode()

@st.cache_data
def load_data():
    df = pd.read_csv("mn_food_access_data.csv")
    df.columns = [c.strip() for c in df.columns]
    return df

def urgency_label(score):
    if score >= 70: return "Critical"
    elif score >= 55: return "High"
    elif score >= 40: return "Moderate"
    return "Low"

def urgency_badge(urgency):
    styles = {
        "Critical":("#ffe3e3","#b00020","pulse-critical"),
        "High":    ("#fff1d6","#b45309","pulse-high"),
        "Moderate":("#dbeafe","#1d4ed8","pulse-moderate"),
        "Low":     ("#dcfce7","#15803d","pulse-low"),
    }
    bg,fg,cls = styles.get(urgency,("#f3f4f6","#111827",""))
    return f'<div class="urgency-badge badge-pop {cls}" style="background:{bg};color:{fg};">Urgency Level: {urgency}</div>'

def metric_card(label,value):
    return f"""<div class="metric-card glass-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div></div>"""

def explain_score(score):
    if score >= 70: return "High priority — this county shows relatively higher food and health vulnerability compared with others in the dataset."
    elif score >= 55: return "Moderate-high priority — this county may deserve targeted review and stronger support attention."
    elif score >= 40: return "Moderate priority — some level of need is present and may benefit from additional review."
    return "Lower priority — comparatively lower need based on the current dataset."

def why_county_ranked(food_score, health_score, priority_score, urgency):
    if urgency == "Critical":
        title = "Why this county is critical"
        if food_score >= 70 and health_score >= 70:
            text = "Both food need and health risk are very high. The combined effect pushes this county into the highest urgency group."
        elif food_score >= 70:
            text = "Food need is especially high, driving this county into the critical tier."
        elif health_score >= 70:
            text = "Health risk is especially high, raising this county into the highest urgency level."
        else:
            text = "The combined effect of food need and health risk produces one of the strongest priority signals in the dataset."
    elif urgency == "High":
        title = "Why this county is high"
        if food_score >= 55 and health_score >= 55:
            text = "Both food need and health risk are elevated. Combined, the scores show strong need compared with many counties."
        elif food_score >= 55:
            text = "Food need is elevated and contributes strongly to the final priority score."
        elif health_score >= 55:
            text = "Health risk is elevated and increases the county's overall vulnerability."
        else:
            text = "The combined score remains above many other counties in the dataset."
    elif urgency == "Moderate":
        title = "Why this county is moderate"
        if food_score >= 40 and health_score >= 40:
            text = "Both food need and health risk are in the middle range — noticeable need, but not at the level of higher-priority counties."
        elif food_score >= 40:
            text = "Food need shows some concern, but the total combined risk does not reach a higher urgency group."
        elif health_score >= 40:
            text = "Health risk shows some concern, but the overall combined score stays in the middle range."
        else:
            text = "The combined result falls in the middle range compared with the rest of the dataset."
    else:
        title = "Why this county is low"
        if food_score < 40 and health_score < 40:
            text = "Both food need and health risk are comparatively lower than counties with greater concern."
        elif food_score < 40:
            text = "Food need is comparatively lower, which keeps the overall priority level lower."
        else:
            text = "Health risk is comparatively lower, which keeps the county in the low urgency group."
    return title, text

def compare_county_to_others(selected_row, current_df):
    county = selected_row["County"]
    score = float(selected_row["Final Priority Score"])
    avg_score = float(current_df["Final Priority Score"].mean())
    if score > avg_score:
        return f"{county} is above the current view average ({score:.2f} vs {avg_score:.2f}). Its combined food need and health risk are stronger than many other counties in this view."
    elif score < avg_score:
        return f"{county} is below the current view average ({score:.2f} vs {avg_score:.2f}). Its combined need is lower than many counties in this current view."
    return f"{county} is almost equal to the current view average ({score:.2f}). Its overall need level is near the middle of this filtered group."

def priority_formula_text():
    return ("Final Priority Score is based on the combined use of Food Need Score and Health Risk Score. "
            "This helps turn multiple indicators into one easier comparison for county-level prioritization.")

# ============================================================
# Enrichment helpers
# ============================================================
def compute_enriched(row):
    county = row["County"]
    pop = MN_COUNTY_POPULATION.get(county, 0)
    food_score = float(row["Food Need Score"])
    # Food insecurity rate: 8% (score=0) to 28% (score=100)
    # Based on statewide MN rate ~20% from Second Harvest Heartland 2024
    fi_rate = 0.08 + (food_score / 100) * 0.20
    est_fi = int(pop * fi_rate)
    # 40% of food insecure use food shelves, avg 4.5 visits/year (The Food Group 2024)
    est_visits = int(est_fi * 0.40 * 4.5)
    # SNAP: statewide ~7% of population, scaled by food need
    snap_rate = 0.04 + (food_score / 100) * 0.07
    est_snap = int(pop * snap_rate)
    # Coverage gap: MN has ~487 shelves / 5.7M people = 1 per 11,700 people
    est_shelves = max(1, round(pop / 11700))
    gap = int(est_fi / est_shelves) if est_shelves else 0
    return {
        "Population": pop,
        "Est. People Food Insecure": est_fi,
        "Est. Food Insecurity Rate (%)": round(fi_rate * 100, 1),
        "Est. Food Shelf Visits 2024": est_visits,
        "Est. SNAP Enrollment": est_snap,
        "Est. Food Shelves": est_shelves,
        "Coverage Gap (people/shelter)": gap,
    }

def fmt_num(n):
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    elif n >= 1_000: return f"{n:,.0f}"
    return str(n)

def coverage_gap_badge(gap, median_gap):
    if gap > median_gap * 1.3:
        return '<span style="background:#ffe3e3;color:#b00020;padding:4px 10px;border-radius:20px;font-size:13px;font-weight:700;">⚠️ High Coverage Gap</span>'
    elif gap > median_gap * 0.8:
        return '<span style="background:#fff1d6;color:#b45309;padding:4px 10px;border-radius:20px;font-size:13px;font-weight:700;">🔶 Moderate Gap</span>'
    return '<span style="background:#dcfce7;color:#15803d;padding:4px 10px;border-radius:20px;font-size:13px;font-weight:700;">✅ Lower Gap</span>'

# ============================================================
# Map builder
# ============================================================
# County boundaries are bundled below to keep this a single-file app.
# Source: https://github.com/plotly/datasets/blob/master/geojson-counties-fips.json
# Only the 87 Minnesota features are included (gzip-compressed GeoJSON).
MN_BOUNDARIES_B64 = (
    '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'
)


@st.cache_data
def load_county_geojson():
    return json.loads(gzip.decompress(base64.b64decode(MN_BOUNDARIES_B64)))


def map_text(value):
    """Treat missing CSV values as empty text, including optional coordinate fields."""
    return "" if pd.isna(value) else str(value).strip()


def build_food_map_payload(full_df, selected_county, selected_urgency, shelves, error=""):
    """Use directory coordinates only; retain unmapped listings in the table."""
    features = load_county_geojson()
    by_fips = {MN_COUNTY_FIPS.get(r["County"]): r for r in full_df.to_dict("records")}
    for feature in features["features"]:
        row = by_fips.get(feature["id"], {})
        name = row.get("County", feature["properties"].get("NAME", "County"))
        urgency = row.get("Urgency Level", "Unavailable")
        details = [f"<strong>{escape(name)} County</strong>", f"Priority level: {escape(urgency)}"]
        for label, column, pattern in [
            ("Priority score", "Final Priority Score", ".1f"),
            ("Population · 2020 Census", "Population", ",.0f"),
            ("People facing food insecurity · model estimate", "Est. People Food Insecure", ",.0f"),
        ]:
            if column in row and pd.notna(row[column]):
                details.append(f"{label}: {format(float(row[column]), pattern)}")
        feature["properties"] = {
            "name": name, "urgency": urgency, "selected": name == selected_county,
            "highlighted": selected_urgency == "All" or urgency == selected_urgency,
            "tooltip": "<br>".join(details),
        }

    selected = county_shelves(shelves, selected_county) if not error else shelves.iloc[:0]
    locations = {}
    unmapped = 0
    for record in selected.to_dict("records"):
        try:
            lat, lon = float(record.get("Latitude", "")), float(record.get("Longitude", ""))
            # Broad Minnesota bounds catch missing, reversed and implausible coordinates.
            valid = math.isfinite(lat) and math.isfinite(lon) and 43.4 <= lat <= 49.5 and -97.5 <= lon <= -89.0
        except (TypeError, ValueError):
            valid = False
        if not valid:
            unmapped += 1
            continue
        name = map_text(record.get("Food_Shelf_Name", "Food shelf"))
        address = map_text(record.get("Address", ""))
        phone = map_text(record.get("Phone", ""))
        website = safe_url(map_text(record.get("Website", "")))
        directions = "https://www.google.com/maps/search/?" + urlencode({"api": "1", "query": address or f"{lat},{lon}"})
        source = safe_url(map_text(record.get("Source_URL", ""))) or DIRECTORY_URL
        retrieved = map_text(record.get("Retrieved_On", ""))
        links = [f'<a href="{escape(directions, quote=True)}" target="_blank" rel="noopener noreferrer">Directions</a>']
        if website:
            links.append(f'<a href="{escape(website, quote=True)}" target="_blank" rel="noopener noreferrer">Website</a>')
        popup = (
            '<article class="provider"><h3>' + escape(name) + '</h3>'
            '<p>' + escape(address or "Address not listed") + '</p>'
            '<p><strong>Phone:</strong> ' + escape(phone or "Not listed") + '</p>'
            '<p class="provider-links">' + " · ".join(links) + '</p>'
            '<p class="provider-source"><a href="' + escape(source, quote=True)
            + '" target="_blank" rel="noopener noreferrer">Source directory</a>'
            + (" · Retrieved " + escape(retrieved) if retrieved else "") + '</p></article>'
        )
        # One marker per exact coordinate; every separately listed program stays accessible.
        location = locations.setdefault((lat, lon), {"lat": lat, "lon": lon, "names": [], "popups": []})
        location["names"].append(name)
        location["popups"].append(popup)

    markers = []
    for location in locations.values():
        count = len(location["names"])
        heading = f'<p><strong>{count} listings share this map location.</strong></p>' if count > 1 else ""
        markers.append({
            "lat": location["lat"], "lon": location["lon"], "count": count,
            "title": "; ".join(location["names"]),
            "popup": heading + "".join(location["popups"])
                     + '<p class="visit-note">Contact the provider before visiting to confirm hours, appointments and eligibility.</p>',
        })
    total = len(selected)
    mapped = total - unmapped
    if error:
        status = "Food-shelf locations are temporarily unavailable. Use the source directory in the food-shelf section below."
    elif total == 0:
        status = f"No listings matched {selected_county} County in this snapshot. This does not mean no food support is available."
    elif not mapped:
        status = f"None of the {total} listings has usable map coordinates. Their names and contact details are still in the table below."
    else:
        listing_word = "listing" if mapped == 1 else "listings"
        location_word = "location" if len(markers) == 1 else "locations"
        status = f"{mapped} food-shelf {listing_word} shown at {len(markers)} map {location_word} in {selected_county} County."
        if unmapped:
            status += f" {unmapped} more cannot be mapped; see the table below."
        if mapped > len(markers):
            status += " A numbered marker contains multiple listings."
    return {
        "county": selected_county, "urgency": selected_urgency, "geojson": features,
        "markers": markers, "total": total, "mapped": mapped, "unmapped": unmapped,
        "status": status, "error": bool(error),
    }


def build_map(full_df, filtered_df, selected_county, selected_urgency, shelves, error=""):
    payload = build_food_map_payload(full_df, selected_county, selected_urgency, shelves, error)
    # Escape script delimiters as well as HTML in popups, including untrusted CSV names.
    encoded = json.dumps(payload, ensure_ascii=True, allow_nan=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="">
<style>
*{box-sizing:border-box}[hidden]{display:none!important}body{margin:0;background:#fff;color:#111827;font:14px/1.45 system-ui,sans-serif;color-scheme:light}
.map-panel{border:1px solid #cbd5e1;border-radius:14px;padding:14px;background:#fff}
.toolbar{display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:10px}
button{font:inherit;color:#111827;background:#fff;border:1px solid #64748b;border-radius:7px;padding:6px 10px;cursor:pointer}
button:hover{background:#f1f5f9}button[aria-pressed="true"]{background:#e0e7ff;border-color:#1d4ed8}
button:focus-visible,a:focus-visible,input:focus-visible{outline:3px solid #1d4ed8;outline-offset:2px}
label{display:flex;align-items:center;gap:5px;font-size:13px}input{accent-color:#1d4ed8}
#map{height:420px;width:100%;border:1px solid #cbd5e1;border-radius:8px;background:#f1f5f9}
.map-status{margin:8px 0;color:#111827;font-size:13px}.hint{margin:8px 0 0;color:#374151;font-size:12px}
.legend{display:flex;flex-wrap:wrap;gap:5px 12px;margin-top:9px;font-size:12px}
.legend span{display:inline-flex;align-items:center;gap:5px}.swatch{width:11px;height:11px;border:1px solid #475569;display:inline-block}
.pin-key{border-radius:50%;background:#1d4ed8;border:2px solid white;box-shadow:0 0 0 1px #1d4ed8}
.food-marker{display:flex;align-items:center;justify-content:center;background:#1d4ed8;border:2px solid white;border-radius:50%;box-shadow:0 0 0 1px #111827,0 2px 5px #0004;color:#fff;font-size:11px;font-weight:800}
.leaflet-popup-content-wrapper,.leaflet-popup-tip,.leaflet-tooltip{background:#fff;color:#111827}
.leaflet-popup-content{max-height:240px;overflow:auto;margin:14px;font:13px/1.45 system-ui,sans-serif}
.leaflet-tooltip{max-width:260px;white-space:normal;font-size:12px}
.provider h3{margin:0 0 5px;font-size:15px;color:#111827}.provider p{margin:5px 0}
.provider+.provider{border-top:1px solid #cbd5e1;margin-top:12px;padding-top:12px}
.leaflet-container a,.provider a{color:#1e40af;text-decoration:underline}
.provider-source,.visit-note{font-size:11px;color:#374151}.visit-note{border-top:1px solid #cbd5e1;padding-top:8px}
.leaflet-bar a{background:#fff;color:#111827;text-decoration:none}
.leaflet-control-attribution{background:#fffffff0;color:#374151;font-size:10px}
#map-error{margin:8px 0;padding:10px;background:#fef3c7;color:#111827}
</style></head><body><section class="map-panel" aria-label="County food-shelf map">
<div class="toolbar"><button id="county-view" type="button" aria-pressed="true">County view</button><button id="state-view" type="button" aria-pressed="false">Minnesota view</button>
<label><input id="show-shelves" type="checkbox" checked>Show food shelves</label></div>
<p id="map-status" class="map-status" aria-live="polite">__STATUS__</p>
<p id="map-error" role="status">If the interactive map does not load, use the food-shelf names, addresses and directions in the table below.</p>
<div id="map" role="region" aria-label="Interactive county map. Use plus and minus to zoom; select a blue marker for food-shelf details."></div>
<div class="legend" aria-label="Map legend"><span><i class="swatch" style="background:#ef4444"></i>Critical</span><span><i class="swatch" style="background:#f59e0b"></i>High</span><span><i class="swatch" style="background:#3b82f6"></i>Moderate</span><span><i class="swatch" style="background:#22c55e"></i>Low</span><span id="other-legend"><i class="swatch" style="background:#d1d5db"></i>Other urgency levels</span><span><i class="swatch pin-key"></i>Food-shelf location</span></div>
<p class="hint">Black border = selected county. Click a blue marker for contact details. Hover over a county for its priority and population. To change counties, use the sidebar.</p>
<p class="hint">Locations come from the directory snapshot, not a live availability check. Listings do not measure capacity; some programs are mobile or restricted-access.</p>
</section>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
<script>
const data = __MAP_DATA__;
if (window.L) {
 try {
  const colors = {Low:'#22c55e',Moderate:'#3b82f6',High:'#f59e0b',Critical:'#ef4444'};
  const map = L.map('map', {scrollWheelZoom:false, minZoom:5, maxZoom:16});
  map.attributionControl.addAttribution('Boundaries: <a href="https://github.com/plotly/datasets/blob/master/geojson-counties-fips.json" target="_blank" rel="noopener noreferrer">Plotly datasets</a>');
  let selectedLayer;
  const counties = L.geoJSON(data.geojson, {
   style: feature => ({color:feature.properties.selected?'#111827':'#64748b',weight:feature.properties.selected?3:0.8,fillColor:feature.properties.highlighted?(colors[feature.properties.urgency]||'#d1d5db'):'#d1d5db',fillOpacity:0.6}),
   onEachFeature: (feature,layer) => {
    layer.bindTooltip(feature.properties.tooltip,{sticky:true});
    if(feature.properties.selected) selectedLayer=layer;
   }
  }).addTo(map);
  if(selectedLayer) selectedLayer.bringToFront();
  const markers = L.featureGroup();
  for(const point of data.markers) {
   const icon=L.divIcon({className:'food-marker',html:point.count>1?String(point.count):'',iconSize:[24,24],iconAnchor:[12,12],popupAnchor:[0,-10]});
   const marker=L.marker([point.lat,point.lon],{icon,title:point.title,alt:point.title,keyboard:true,riseOnHover:true});
   marker.bindPopup(point.popup,{maxWidth:280,minWidth:180,autoPanPadding:[20,20]});
   markers.addLayer(marker);
  }
  markers.addTo(map);
  const stateBounds=counties.getBounds();
  const countyBounds=L.latLngBounds([]);
  if(selectedLayer) countyBounds.extend(selectedLayer.getBounds());
  if(data.markers.length) countyBounds.extend(markers.getBounds());
  const countyButton=document.getElementById('county-view');
  const stateButton=document.getElementById('state-view');
  const status=document.getElementById('map-status');
  const showShelves=document.getElementById('show-shelves');
  function fitView(county) {
   map.closePopup();
   map.fitBounds(county && countyBounds.isValid()?countyBounds:stateBounds,{padding:[22,22],maxZoom:12});
   countyButton.setAttribute('aria-pressed',String(county));stateButton.setAttribute('aria-pressed',String(!county));
  }
  countyButton.addEventListener('click',()=>fitView(true));
  stateButton.addEventListener('click',()=>fitView(false));
  showShelves.disabled=!data.markers.length;
  showShelves.addEventListener('change',()=>{
   if(showShelves.checked){markers.addTo(map);status.textContent=data.status;}
   else{map.removeLayer(markers);status.textContent='Food-shelf markers are hidden. Turn on “Show food shelves” to see them again.';}
  });
  document.getElementById('other-legend').hidden=data.urgency==='All';
  fitView(true);
  document.getElementById('map-error').hidden=true;
 } catch(error) {
  document.getElementById('map-error').hidden=false;
 }
}
</script></body></html>""".replace("__STATUS__", escape(payload["status"])).replace("__MAP_DATA__", encoded)


def render_county_food_map(full_df, filtered_df, selected_county, selected_urgency, shelves, error=""):
    components.html(build_map(full_df, filtered_df, selected_county, selected_urgency, shelves, error), height=680, scrolling=True)


# ============================================================
# ANIMATED COMPONENTS
# ============================================================

def render_hero(b64):
    """Hero with canvas particle network + floating food emojis + typing effect."""
    html = f"""
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:transparent;overflow:hidden;}}
.hero{{
  position:relative;min-height:650px;display:flex;align-items:center;
  justify-content:center;text-align:center;border-radius:34px;overflow:hidden;
  background:linear-gradient(rgba(0,0,0,0.45),rgba(0,0,0,0.60)),
             url('data:image/avif;base64,{b64}');
  background-size:cover;background-position:center;
  box-shadow:0 30px 80px rgba(0,0,0,0.35);
  animation:heroRise 1s cubic-bezier(0.34,1.2,0.64,1) both;
}}
@keyframes heroRise{{from{{opacity:0;transform:translateY(30px) scale(0.97)}}to{{opacity:1;transform:none}}}}
canvas{{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;}}
.food-p{{position:absolute;bottom:-60px;font-size:1.6rem;opacity:0;pointer-events:none;z-index:1;
  animation:floatUp linear infinite;}}
@keyframes floatUp{{0%{{transform:translateY(0) rotate(0deg);opacity:0}}
  10%{{opacity:0.6}}80%{{opacity:0.25}}100%{{transform:translateY(-620px) rotate(300deg);opacity:0}}}}
.glow-ring{{position:absolute;inset:0;border-radius:34px;pointer-events:none;z-index:2;
  animation:ringPulse 5s ease-in-out infinite;}}
@keyframes ringPulse{{
  0%,100%{{box-shadow:inset 0 0 0 1.5px rgba(251,191,36,0.15),0 0 60px rgba(251,191,36,0.06)}}
  50%{{box-shadow:inset 0 0 0 1.5px rgba(251,191,36,0.40),0 0 120px rgba(251,191,36,0.18)}}
}}
.inner{{position:relative;z-index:3;max-width:1050px;padding:34px;}}
.logo{{color:#fff;font-size:118px;font-weight:900;letter-spacing:2px;line-height:1;
  text-shadow:0 6px 40px rgba(0,0,0,0.4);
  animation:logoDrop 1s cubic-bezier(0.34,1.56,0.64,1) 0.1s both;}}
@keyframes logoDrop{{from{{opacity:0;transform:translateY(-40px) scale(0.85)}}to{{opacity:1;transform:none}}}}
.tag{{display:inline-block;background:rgba(251,191,36,0.18);border:1px solid rgba(251,191,36,0.45);
  color:#fde68a;font-size:15px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;
  padding:7px 20px;border-radius:999px;margin-bottom:22px;
  animation:tagIn 0.6s ease-out 0.6s both;}}
@keyframes tagIn{{from{{opacity:0;transform:scale(0.85)}}to{{opacity:1;transform:scale(1)}}}}
.subtitle{{color:#fffaf2;font-size:34px;font-weight:800;line-height:1.35;margin-bottom:18px;
  overflow:hidden;white-space:nowrap;border-right:3px solid rgba(255,255,255,0.7);
  width:0;margin-left:auto;margin-right:auto;
  animation:typing 2.4s steps(44,end) 1s both, blink 0.75s step-end 1s infinite;}}
@keyframes typing{{from{{width:0}}to{{width:100%}}}}
@keyframes blink{{50%{{border-color:transparent}}}}
.desc{{color:rgba(255,255,255,0.88);font-size:19px;line-height:1.85;max-width:850px;margin:0 auto;
  animation:fadeUp 0.8s ease-out 3.2s both;}}
@keyframes fadeUp{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
.wave-bottom{{position:absolute;bottom:-1px;left:0;right:0;height:48px;z-index:2;}}
.wave-path{{fill:rgba(255,255,255,0.06);animation:waveSway 6s ease-in-out infinite;}}
@keyframes waveSway{{0%,100%{{d:path("M0,32 C300,52 600,12 900,32 C1100,48 1150,20 1200,32 L1200,48 L0,48 Z")}}
  50%{{d:path("M0,20 C250,40 550,8 850,28 C1050,44 1150,14 1200,20 L1200,48 L0,48 Z")}}}}
</style>
<div class="hero">
  <canvas id="c"></canvas>
  <div class="food-p" style="left:4%;animation-duration:10s;animation-delay:0s">🌽</div>
  <div class="food-p" style="left:11%;animation-duration:13s;animation-delay:1.6s">🥕</div>
  <div class="food-p" style="left:19%;animation-duration:9s;animation-delay:3.2s">🍎</div>
  <div class="food-p" style="left:28%;animation-duration:11s;animation-delay:0.8s">🥦</div>
  <div class="food-p" style="left:38%;animation-duration:14s;animation-delay:2.5s">🌾</div>
  <div class="food-p" style="left:50%;animation-duration:10.5s;animation-delay:4.2s">🥗</div>
  <div class="food-p" style="left:61%;animation-duration:9.5s;animation-delay:1.3s">🍊</div>
  <div class="food-p" style="left:71%;animation-duration:12s;animation-delay:2.9s">🫐</div>
  <div class="food-p" style="left:80%;animation-duration:10s;animation-delay:0.5s">🥬</div>
  <div class="food-p" style="left:89%;animation-duration:13s;animation-delay:3.7s">🍇</div>
  <div class="food-p" style="left:95%;animation-duration:9s;animation-delay:2s">🌽</div>
  <div class="glow-ring"></div>
  <div class="inner">
    <div class="tag">Minnesota · Food Security · 87 Counties</div>
    <div class="logo">Carelio</div>
    <div class="subtitle">Minnesota food support prioritization website</div>
    <div class="desc">A county-level decision-support website for nonprofits, grant teams, and planning partners to review priority counties, map patterns, and resource planning signals across Minnesota.</div>
  </div>
  <div class="wave-bottom">
    <svg viewBox="0 0 1200 48" preserveAspectRatio="none" width="100%" height="48">
      <path class="wave-path" d="M0,32 C300,52 600,12 900,32 C1100,48 1150,20 1200,32 L1200,48 L0,48 Z"/>
    </svg>
  </div>
</div>
<script>
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function resize(){{ canvas.width=canvas.offsetWidth; canvas.height=canvas.offsetHeight; }}
resize();
const pts=[];
for(let i=0;i<55;i++) pts.push({{
  x:Math.random()*canvas.width, y:Math.random()*canvas.height,
  vx:(Math.random()-.5)*0.55, vy:(Math.random()-.5)*0.55,
  r:Math.random()*1.8+0.6
}});
function draw(){{
  ctx.clearRect(0,0,canvas.width,canvas.height);
  pts.forEach(p=>{{
    p.x+=p.vx; p.y+=p.vy;
    if(p.x<0||p.x>canvas.width) p.vx*=-1;
    if(p.y<0||p.y>canvas.height) p.vy*=-1;
    ctx.beginPath(); ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
    ctx.fillStyle='rgba(255,255,255,0.55)'; ctx.fill();
  }});
  for(let i=0;i<pts.length;i++) for(let j=i+1;j<pts.length;j++){{
    const dx=pts[i].x-pts[j].x, dy=pts[i].y-pts[j].y;
    const d=Math.sqrt(dx*dx+dy*dy);
    if(d<110){{
      ctx.beginPath(); ctx.moveTo(pts[i].x,pts[i].y); ctx.lineTo(pts[j].x,pts[j].y);
      ctx.strokeStyle=`rgba(255,255,255,${{0.12*(1-d/110)}})`;
      ctx.lineWidth=0.6; ctx.stroke();
    }}
  }}
  requestAnimationFrame(draw);
}}
draw();
</script>
"""
    components.html(html, height=670, scrolling=False)


def render_section_hero(title, tagline, subnote, b64):
    """Animated inner page banner with gradient sweep + particles."""
    html = f"""
<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}
body{{background:transparent;overflow:hidden;}}
.sh{{
  position:relative;overflow:hidden;border-radius:30px;min-height:210px;
  background:linear-gradient(rgba(0,0,0,0.46),rgba(0,0,0,0.54)),
             url('data:image/avif;base64,{b64}');
  background-size:cover;background-position:center;
  display:flex;align-items:center;justify-content:center;text-align:center;padding:34px;
  box-shadow:0 18px 45px rgba(0,0,0,0.22);
  animation:rise 0.75s cubic-bezier(0.34,1.2,0.64,1) both;
}}
@keyframes rise{{from{{opacity:0;transform:translateY(20px) scale(0.97)}}to{{opacity:1;transform:none}}}}
.sweep{{position:absolute;inset:0;
  background:linear-gradient(105deg,transparent 30%,rgba(251,191,36,0.10) 50%,transparent 70%);
  animation:sweepMove 4s ease-in-out infinite;pointer-events:none;}}
@keyframes sweepMove{{0%,100%{{transform:translateX(-60%)}}50%{{transform:translateX(60%)}}}}
.fp{{position:absolute;font-size:1.1rem;opacity:0;animation:fp linear infinite;pointer-events:none;bottom:-20px;}}
@keyframes fp{{0%{{transform:translateY(0);opacity:0}}15%{{opacity:0.4}}85%{{opacity:0.1}}100%{{transform:translateY(-250px);opacity:0}}}}
.inner{{position:relative;z-index:2;}}
h1{{color:#fff;font-size:56px;font-weight:900;margin:0 0 10px;letter-spacing:.5px;
  animation:titlePop 0.8s cubic-bezier(0.34,1.56,0.64,1) 0.15s both;}}
@keyframes titlePop{{from{{opacity:0;transform:scale(0.85) translateY(10px)}}to{{opacity:1;transform:none}}}}
.tl{{color:#fde68a;font-size:18px;font-weight:700;margin:0 0 8px;animation:fu 0.6s ease-out 0.4s both;}}
.sn{{color:rgba(255,248,239,0.88);font-size:14.5px;line-height:1.7;font-weight:500;animation:fu 0.6s ease-out 0.6s both;}}
@keyframes fu{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:none}}}}
</style>
<div class="sh">
  <div class="sweep"></div>
  <div class="fp" style="left:6%;animation-duration:7s;animation-delay:0s">🌽</div>
  <div class="fp" style="left:90%;animation-duration:9s;animation-delay:2s">🥕</div>
  <div class="fp" style="left:50%;animation-duration:8s;animation-delay:4s">🍎</div>
  <div class="inner">
    <h1>{title}</h1>
    <div class="tl">{tagline}</div>
    <div class="sn">{subnote}</div>
  </div>
</div>
"""
    components.html(html, height=225, scrolling=False)


def render_animated_metrics(n, top_county, highest, critical):
    """4 metric cards — gradient border rotation + count-up."""
    html = f"""
<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}
body{{background:transparent;}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;padding:2px;}}
.wrap{{border-radius:20px;padding:2px;
  background:linear-gradient(135deg,#f59e0b,#fbbf24,#f97316,#f59e0b);
  background-size:300% 300%;
  animation:borderSpin 4s linear infinite;}}
.wrap:nth-child(2){{animation-delay:-1s;}}
.wrap:nth-child(3){{animation-delay:-2s;}}
.wrap:nth-child(4){{animation-delay:-3s;}}
@keyframes borderSpin{{0%{{background-position:0% 50%}}100%{{background-position:300% 50%}}}}
.card{{background:linear-gradient(145deg,#fff,#fff9f0);border-radius:18px;padding:18px;
  position:relative;overflow:hidden;
  opacity:0;transform:translateY(22px) scale(0.94);
  animation:cardIn 0.6s cubic-bezier(0.34,1.56,0.64,1) forwards;
  cursor:default;transition:transform 0.3s ease,box-shadow 0.3s ease;}}
.card:hover{{transform:translateY(-7px) scale(1.03);box-shadow:0 20px 35px rgba(245,158,11,0.20);}}
.wrap:nth-child(1) .card{{animation-delay:0.05s;}}
.wrap:nth-child(2) .card{{animation-delay:0.15s;}}
.wrap:nth-child(3) .card{{animation-delay:0.25s;}}
.wrap:nth-child(4) .card{{animation-delay:0.35s;}}
@keyframes cardIn{{to{{opacity:1;transform:none}}}}
.card::before{{content:"";position:absolute;top:0;left:-150%;width:80%;height:100%;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,0.5),transparent);
  transform:skewX(-20deg);animation:cardShine 5s ease infinite;}}
.wrap:nth-child(2) .card::before{{animation-delay:1.2s;}}
.wrap:nth-child(3) .card::before{{animation-delay:2.4s;}}
.wrap:nth-child(4) .card::before{{animation-delay:3.6s;}}
@keyframes cardShine{{0%{{left:-150%}}30%{{left:150%}}100%{{left:150%}}}}
.lbl{{color:#6b7280;font-size:12.5px;font-weight:600;margin-bottom:7px;text-transform:uppercase;letter-spacing:.06em;}}
.val{{color:#111827;font-size:27px;font-weight:800;line-height:1.1;}}
.dot{{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:7px;
  vertical-align:middle;background:#ef4444;
  animation:dp 1.8s ease-in-out infinite;}}
@keyframes dp{{0%,100%{{box-shadow:0 0 0 0 rgba(239,68,68,0.6)}}50%{{box-shadow:0 0 0 9px rgba(239,68,68,0)}}}}
</style>
<div class="grid">
  <div class="wrap"><div class="card"><div class="lbl">Counties in view</div><div class="val" id="v1">0</div></div></div>
  <div class="wrap"><div class="card"><div class="lbl">Top county</div><div class="val">{top_county}</div></div></div>
  <div class="wrap"><div class="card"><div class="lbl">Highest score</div><div class="val" id="v3">0.00</div></div></div>
  <div class="wrap"><div class="card"><div class="lbl">Critical counties</div><div class="val"><span class="dot"></span><span id="v4">0</span></div></div></div>
</div>
<script>
function cu(id,tgt,dur,fl){{
  const el=document.getElementById(id); if(!el)return;
  const s=performance.now();
  (function step(n){{
    const p=Math.min((n-s)/dur,1), e=1-Math.pow(1-p,3);
    el.textContent=fl?(e*tgt).toFixed(2):Math.floor(e*tgt);
    if(p<1)requestAnimationFrame(step); else el.textContent=fl?tgt.toFixed(2):tgt;
  }})(performance.now());
}}
setTimeout(()=>{{cu('v1',{n},900,false);cu('v3',{highest},1400,true);cu('v4',{critical},800,false);}},400);
</script>
"""
    components.html(html, height=112, scrolling=False)


def render_triple_gauge(food, health, priority, urgency):
    """Three concentric ring gauge: outer=food, middle=health, inner=priority."""
    gmap={"Critical":"#ef4444","High":"#f59e0b","Moderate":"#3b82f6","Low":"#22c55e"}
    gshadow={"Critical":"rgba(239,68,68,0.45)","High":"rgba(245,158,11,0.45)","Moderate":"rgba(59,130,246,0.4)","Low":"rgba(34,197,94,0.4)"}
    c=gmap.get(urgency,"#6b7280"); gs=gshadow.get(urgency,"transparent")
    html = f"""
<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}
body{{background:transparent;}}
.wrap{{display:flex;align-items:center;gap:24px;animation:fadeUp 0.6s ease-out both;}}
@keyframes fadeUp{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:none}}}}
.legend{{flex:1;}}
.row{{margin-bottom:16px;}}
.lbl{{display:flex;justify-content:space-between;align-items:center;font-size:13px;color:#6b7280;margin-bottom:6px;}}
.lbl-left{{display:flex;align-items:center;gap:6px;}}
.dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0;}}
.lbl span:last-child{{font-weight:800;color:#111827;font-size:14px;}}
.track{{background:#f0f0f0;border-radius:8px;height:11px;overflow:hidden;}}
.fill{{height:100%;border-radius:8px;width:0;transition:width 1.5s cubic-bezier(0.34,1.2,0.64,1);}}
.food-bar{{background:linear-gradient(90deg,#f97316,#fbbf24);}}
.hlth-bar{{background:linear-gradient(90deg,#8b5cf6,#c084fc);}}
</style>
<div class="wrap">
  <svg width="190" height="130" viewBox="0 0 190 130" style="flex-shrink:0;">
    <defs>
      <filter id="gf"><feGaussianBlur stdDeviation="3.5"/></filter>
      <linearGradient id="fg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#f97316"/>
        <stop offset="100%" stop-color="#fbbf24"/>
      </linearGradient>
      <linearGradient id="hg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#8b5cf6"/>
        <stop offset="100%" stop-color="#c084fc"/>
      </linearGradient>
    </defs>
    <!-- tracks -->
    <path d="M 14 110 A 82 82 0 0 1 176 110" fill="none" stroke="#ebebeb" stroke-width="11" stroke-linecap="round"/>
    <path d="M 24 110 A 72 72 0 0 1 166 110" fill="none" stroke="#ebebeb" stroke-width="10" stroke-linecap="round"/>
    <path d="M 36 110 A 60 60 0 0 1 154 110" fill="none" stroke="#ebebeb" stroke-width="9"  stroke-linecap="round"/>
    <!-- glow layers -->
    <path d="M 14 110 A 82 82 0 0 1 176 110" fill="none" stroke="url(#fg)" stroke-width="16" stroke-linecap="round"
          stroke-dasharray="0 258" id="fog" opacity="0.2" style="filter:url(#gf);transition:stroke-dasharray 1.5s ease-out;"/>
    <path d="M 24 110 A 72 72 0 0 1 166 110" fill="none" stroke="url(#hg)" stroke-width="14" stroke-linecap="round"
          stroke-dasharray="0 226" id="hog" opacity="0.2" style="filter:url(#gf);transition:stroke-dasharray 1.5s ease-out;"/>
    <path d="M 36 110 A 60 60 0 0 1 154 110" fill="none" stroke="{c}" stroke-width="12" stroke-linecap="round"
          stroke-dasharray="0 188" id="pog" opacity="0.25" style="filter:url(#gf);transition:stroke-dasharray 1.5s ease-out;"/>
    <!-- main arcs -->
    <path d="M 14 110 A 82 82 0 0 1 176 110" fill="none" stroke="url(#fg)" stroke-width="11" stroke-linecap="round"
          stroke-dasharray="0 258" id="fa" style="transition:stroke-dasharray 1.5s cubic-bezier(0.34,1.2,0.64,1);"/>
    <path d="M 24 110 A 72 72 0 0 1 166 110" fill="none" stroke="url(#hg)" stroke-width="10" stroke-linecap="round"
          stroke-dasharray="0 226" id="ha" style="transition:stroke-dasharray 1.5s cubic-bezier(0.34,1.2,0.64,1) 0.15s;"/>
    <path d="M 36 110 A 60 60 0 0 1 154 110" fill="none" stroke="{c}" stroke-width="9"  stroke-linecap="round"
          stroke-dasharray="0 188" id="pa" style="transition:stroke-dasharray 1.5s cubic-bezier(0.34,1.2,0.64,1) 0.3s;
          filter:drop-shadow(0 0 5px {gs});"/>
    <!-- center text -->
    <text id="pnum" x="95" y="92" text-anchor="middle" font-size="26" font-weight="900" fill="#111827">0</text>
    <text x="95" y="110" text-anchor="middle" font-size="10.5" fill="#9ca3af" font-weight="600">Priority Score</text>
    <text x="95" y="125" text-anchor="middle" font-size="10.5" font-weight="800" fill="{c}">{urgency}</text>
  </svg>
  <div class="legend">
    <div class="row">
      <div class="lbl">
        <div class="lbl-left"><div class="dot" style="background:linear-gradient(135deg,#f97316,#fbbf24)"></div><span>🍽 Food Need Score</span></div>
        <span id="fv">0</span>
      </div>
      <div class="track"><div class="fill food-bar" id="fb"></div></div>
    </div>
    <div class="row">
      <div class="lbl">
        <div class="lbl-left"><div class="dot" style="background:linear-gradient(135deg,#8b5cf6,#c084fc)"></div><span>🏥 Health Risk Score</span></div>
        <span id="hv">0</span>
      </div>
      <div class="track"><div class="fill hlth-bar" id="hb"></div></div>
    </div>
  </div>
</div>
<script>
const FA=257.6, HA=225.6, PA=188.0;
setTimeout(()=>{{
  document.getElementById('fa').setAttribute('stroke-dasharray',({food}/100)*FA+' '+FA);
  document.getElementById('fog').setAttribute('stroke-dasharray',({food}/100)*FA+' '+FA);
  document.getElementById('ha').setAttribute('stroke-dasharray',({health}/100)*HA+' '+HA);
  document.getElementById('hog').setAttribute('stroke-dasharray',({health}/100)*HA+' '+HA);
  document.getElementById('pa').setAttribute('stroke-dasharray',({priority}/100)*PA+' '+PA);
  document.getElementById('pog').setAttribute('stroke-dasharray',({priority}/100)*PA+' '+PA);
  document.getElementById('fb').style.width='{food}%';
  document.getElementById('hb').style.width='{health}%';
  const pEl=document.getElementById('pnum'), s=performance.now(), tgt={priority};
  (function t(n){{const p=Math.min((n-s)/1500,1),e=1-Math.pow(1-p,3);
    pEl.textContent=(e*tgt).toFixed(1); if(p<1)requestAnimationFrame(t); else pEl.textContent=tgt.toFixed(1);}})
  (performance.now());
  [['fv',{food}],['hv',{health}]].forEach(([id,tgt])=>{{
    const el=document.getElementById(id), s2=performance.now();
    (function t(n){{const p=Math.min((n-s2)/1500,1),e=1-Math.pow(1-p,3);
      el.textContent=(e*tgt).toFixed(1); if(p<1)requestAnimationFrame(t); else el.textContent=tgt.toFixed(1);}})
    (performance.now());
  }});
}},300);
</script>
"""
    components.html(html, height=155, scrolling=False)

# ============================================================
# Images
# ============================================================
header_banner = get_base64_image("header_banner.avif")
page_bg       = get_base64_image("page_bg.jpg")

# ============================================================
# CSS
# ============================================================
st.markdown(f"""
<style>
html{{scroll-behavior:smooth;}}
.stApp{{
  background:linear-gradient(rgba(255,255,255,0.72),rgba(255,255,255,0.82)),
             url("data:image/jpg;base64,{page_bg}");
  background-size:cover;background-position:center;background-attachment:fixed;
}}
.block-container{{padding-top:1rem;padding-bottom:2rem;max-width:1280px;animation:pageFade 0.7s ease-out;}}
section[data-testid="stSidebar"]{{
  background:rgba(255,247,236,0.97);border-right:2px solid rgba(240,190,95,0.45);
  backdrop-filter:blur(12px);animation:sideIn 0.6s ease-out both;
}}
@keyframes sideIn{{from{{opacity:0;transform:translateX(-20px)}}to{{opacity:1;transform:none}}}}
section[data-testid="stSidebar"] *{{color:#111827 !important;}}

div.stButton > button:first-child{{
  background:linear-gradient(135deg,#f59e0b,#f97316) !important;
  color:white !important;border:none !important;border-radius:999px !important;
  padding:0.9rem 2.3rem !important;font-size:1.02rem !important;font-weight:800 !important;
  box-shadow:0 14px 30px rgba(249,115,22,0.28) !important;
  transition:transform 0.25s cubic-bezier(0.34,1.56,0.64,1),box-shadow 0.25s ease !important;
  position:relative !important;overflow:hidden !important;
}}
div.stButton > button:first-child::after{{
  content:"" !important;position:absolute !important;inset:0 !important;
  background:radial-gradient(circle at center,rgba(255,255,255,0.35) 0%,transparent 65%) !important;
  opacity:0 !important;transition:opacity 0.4s ease !important;
}}
div.stButton > button:first-child:hover{{transform:translateY(-3px) scale(1.04) !important;box-shadow:0 22px 38px rgba(249,115,22,0.36) !important;}}
div.stButton > button:first-child:hover::after{{opacity:1 !important;}}
div.stButton > button:first-child:active{{transform:scale(0.97) !important;}}

.content-wrap{{background:rgba(255,255,255,0.72);border-radius:30px;padding:24px;
  backdrop-filter:blur(9px);box-shadow:0 12px 28px rgba(0,0,0,0.08);animation:fadeInSoft 0.8s ease-out;}}
.glass-card{{backdrop-filter:blur(6px);}}

.pink-box,.yellow-box,.white-box,.green-box,.blue-box,.contact-box,.chart-card{{
  border-radius:22px;padding:20px;margin-bottom:18px;
  box-shadow:0 6px 14px rgba(0,0,0,0.06);color:#111827 !important;
  animation:slideUp 0.6s ease-out both;transition:transform 0.3s ease,box-shadow 0.3s ease;
}}
.pink-box:hover,.yellow-box:hover,.white-box:hover,.green-box:hover,.blue-box:hover,.chart-card:hover{{
  transform:translateY(-5px);box-shadow:0 20px 36px rgba(0,0,0,0.13);
}}
.pink-box{{background:rgba(255,233,243,0.97);border:2px solid rgba(242,167,200,0.88);animation-delay:.05s;}}
.yellow-box{{background:rgba(255,245,196,0.97);border:2px solid rgba(244,201,93,0.88);animation-delay:.10s;}}
.white-box{{background:rgba(255,255,255,0.98);border:1px solid rgba(220,220,220,0.95);animation-delay:.15s;}}
.green-box{{background:rgba(232,247,236,0.98);border:1px solid rgba(144,196,157,0.95);animation-delay:.20s;}}
.blue-box{{background:rgba(232,244,255,0.98);border:1px solid rgba(147,197,253,0.95);animation-delay:.25s;}}
.chart-card{{background:rgba(255,255,255,0.98);border:1px solid rgba(243,217,164,0.90);animation-delay:.05s;}}
.contact-box{{background:rgba(255,255,255,0.98);border:2px solid rgba(234,215,164,0.92);padding:22px;box-shadow:0 8px 18px rgba(0,0,0,0.08);animation-delay:.10s;}}

.pink-box h3,.yellow-box h3,.white-box h3,.green-box h3,.blue-box h3,.chart-card h3{{color:#111827 !important;font-size:24px !important;margin:0 0 10px 0 !important;font-weight:700 !important;}}
.contact-box h3{{color:#111827 !important;font-size:24px !important;margin:0 0 10px !important;font-weight:800 !important;}}
.pink-box p,.yellow-box p,.white-box p,.green-box p,.blue-box p,.chart-card p,
.pink-box li,.yellow-box li,.white-box li,.green-box li,.blue-box li{{color:#111827 !important;font-size:16px !important;line-height:1.7 !important;margin-bottom:8px !important;}}
.contact-box p{{color:#111827 !important;font-size:16px !important;line-height:1.7 !important;font-weight:700 !important;}}
.pink-box ul,.yellow-box ul,.white-box ul,.green-box ul,.blue-box ul{{margin:8px 0 0 !important;padding-left:22px !important;}}

.metric-card{{
  background:linear-gradient(135deg,rgba(255,255,255,0.99),rgba(255,249,242,0.98));
  border:1px solid rgba(243,217,164,0.92);padding:18px;border-radius:18px;
  box-shadow:0 6px 14px rgba(255,138,0,0.10);margin-bottom:8px;
  animation:fadeInSoft 0.7s ease-out;
  transition:transform 0.35s cubic-bezier(0.34,1.56,0.64,1),box-shadow 0.35s ease;
  transform-style:preserve-3d;cursor:pointer;position:relative;overflow:hidden;
}}
.metric-card::before{{content:"";position:absolute;top:0;left:-120%;width:100%;height:100%;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,0.38),transparent);animation:shine 4.8s infinite;}}
.metric-card:hover{{transform:perspective(900px) rotateX(6deg) rotateY(-6deg) translateY(-8px) scale(1.04);box-shadow:0 22px 38px rgba(0,0,0,0.16);}}
.metric-card:active{{transform:scale(0.97);}}
.metric-label{{color:#6b7280 !important;font-size:15px !important;margin-bottom:6px !important;}}
.metric-value{{color:#111827 !important;font-size:28px !important;font-weight:700 !important;line-height:1.2 !important;}}

.urgency-badge{{padding:10px 16px;border-radius:12px;font-weight:700;display:inline-block;margin-top:8px;font-size:15px;}}
.pulse-critical{{animation:pCrit 1.8s cubic-bezier(0.215,0.61,0.355,1) infinite;}}
.pulse-high{{animation:pHigh 2.2s cubic-bezier(0.215,0.61,0.355,1) infinite;}}
.pulse-moderate{{animation:pMod 2.5s cubic-bezier(0.215,0.61,0.355,1) infinite;}}
.pulse-low{{animation:pLow 3s ease-in-out infinite;}}
@keyframes pCrit{{0%,100%{{box-shadow:0 0 0 0 rgba(176,0,32,0.55),0 4px 12px rgba(176,0,32,0.22)}}50%{{box-shadow:0 0 0 11px rgba(176,0,32,0),0 4px 20px rgba(176,0,32,0.32)}}}}
@keyframes pHigh{{0%,100%{{box-shadow:0 0 0 0 rgba(180,83,9,0.45),0 4px 10px rgba(180,83,9,0.18)}}50%{{box-shadow:0 0 0 9px rgba(180,83,9,0),0 4px 18px rgba(180,83,9,0.26)}}}}
@keyframes pMod{{0%,100%{{box-shadow:0 0 0 0 rgba(29,78,216,0.38)}}50%{{box-shadow:0 0 0 8px rgba(29,78,216,0)}}}}
@keyframes pLow{{0%,100%{{box-shadow:0 0 0 0 rgba(21,128,61,0.28)}}50%{{box-shadow:0 0 0 7px rgba(21,128,61,0)}}}}

.action-card-yellow,.action-card-pink,.action-card-orange{{
  border-radius:22px;padding:18px;min-height:180px;box-shadow:0 6px 14px rgba(0,0,0,0.05);
  animation:slideUp 0.6s ease-out both;transition:transform 0.3s cubic-bezier(0.34,1.56,0.64,1),box-shadow 0.3s ease;
  position:relative;overflow:hidden;
}}
.action-card-yellow::after,.action-card-pink::after,.action-card-orange::after{{
  content:"";position:absolute;inset:auto -30% -80% auto;width:180px;height:180px;
  border-radius:50%;background:rgba(255,255,255,0.18);filter:blur(8px);pointer-events:none;
}}
.action-card-yellow:hover,.action-card-pink:hover,.action-card-orange:hover{{transform:translateY(-8px) scale(1.02);box-shadow:0 20px 34px rgba(0,0,0,0.13);}}
.action-card-yellow{{background:linear-gradient(135deg,rgba(255,247,196,.98),rgba(255,238,172,.94));border:1px solid rgba(244,201,93,.95);animation-delay:.10s;}}
.action-card-pink{{background:linear-gradient(135deg,rgba(255,236,245,.98),rgba(255,220,238,.94));border:1px solid rgba(242,167,200,.95);animation-delay:.20s;}}
.action-card-orange{{background:linear-gradient(135deg,rgba(255,238,220,.98),rgba(255,224,187,.94));border:1px solid rgba(245,158,11,.95);animation-delay:.30s;}}
.action-card-yellow h3,.action-card-pink h3,.action-card-orange h3{{color:#5b21b6 !important;font-size:22px !important;margin:0 0 8px !important;}}
.action-card-yellow p,.action-card-pink p,.action-card-orange p{{color:#111827 !important;font-size:16px !important;line-height:1.6 !important;margin:0 !important;}}

.contact-icon-card{{
  display:flex;align-items:center;justify-content:center;gap:10px;
  padding:12px 16px;border-radius:16px;background:rgba(255,255,255,0.98);
  border:1px solid rgba(226,232,240,0.95);text-decoration:none !important;
  transition:transform 0.3s cubic-bezier(0.34,1.56,0.64,1),box-shadow 0.3s ease;
  box-shadow:0 6px 14px rgba(0,0,0,0.05);animation:popIn 0.5s ease-out both;
}}
.contact-icon-card:hover{{transform:translateY(-5px) scale(1.05);box-shadow:0 14px 26px rgba(0,0,0,0.12);}}
.contact-icon{{font-size:22px;line-height:1;}}
.contact-icon-label{{color:#111827 !important;font-size:15px !important;font-weight:800 !important;}}

.view-banner{{padding:10px 16px;border-radius:12px;margin-bottom:14px;font-size:14px;font-weight:600;animation:fadeInSoft 0.5s ease-out;}}
.v-analyst{{background:#eff6ff;border:1px solid #bfdbfe;color:#1e40af;}}
.v-fundraiser{{background:#fef3c7;border:1px solid #fcd34d;color:#92400e;}}
.v-policy{{background:#f0fdf4;border:1px solid #86efac;color:#166534;}}

.src-row{{padding:9px 0;border-bottom:1px solid rgba(0,0,0,0.06);}}
.src-row:last-child{{border-bottom:none;}}
.src-name{{font-weight:700;font-size:13px;color:#111827 !important;}}
.src-what{{font-size:12px;color:#4b5563 !important;margin:2px 0;}}
.src-freq{{font-size:11px;color:#9ca3af !important;}}

/* Calculation formula box */
.formula-box{{background:rgba(17,24,39,0.94);border-radius:12px;padding:14px 18px;margin:10px 0;
  font-family:monospace;font-size:13.5px;color:#fde68a !important;line-height:1.8;
  border-left:3px solid #f59e0b;}}
.formula-box span{{color:#86efac !important;}}

.section-caption{{color:#4b5563 !important;font-size:15px !important;margin-top:-2px !important;margin-bottom:10px !important;}}
.mini-note{{color:#111827 !important;font-size:15px !important;line-height:1.65 !important;}}
.footer-note{{font-size:13px !important;color:#111827 !important;font-weight:700 !important;line-height:1.7 !important;}}
.contact-name{{color:#111827 !important;font-size:16px !important;font-weight:800 !important;margin-bottom:12px !important;}}
.badge-pop{{animation:popIn 0.45s ease-out;}}

.stSelectbox div[data-baseweb="select"]>div,.stMultiSelect div[data-baseweb="select"]>div{{
  background:rgba(255,255,255,.995) !important;color:#111827 !important;
  border-radius:14px !important;border:1px solid rgba(244,201,93,.95) !important;
  min-height:48px !important;box-shadow:0 4px 10px rgba(0,0,0,.04) !important;transition:all 0.25s ease !important;
}}
.stSelectbox div[data-baseweb="select"]>div:hover{{border:1px solid rgba(245,158,11,.95) !important;box-shadow:0 8px 18px rgba(245,158,11,.12) !important;}}
.stSelectbox div[data-baseweb="select"] span,.stSelectbox div[data-baseweb="select"] input,
.stSelectbox div[data-baseweb="select"] svg{{color:#111827 !important;fill:#111827 !important;opacity:1 !important;}}
div[data-baseweb="popover"] *{{color:#111827 !important;}}
div[data-baseweb="popover"] ul,div[data-baseweb="popover"] li,
div[data-baseweb="popover"] div[role="option"]{{background:#fff !important;color:#111827 !important;}}
div[data-baseweb="popover"] div[aria-selected="true"]{{background:#fef3c7 !important;color:#111827 !important;}}
div[data-baseweb="popover"] div[role="option"]:hover{{background:#fff7dd !important;}}

.stExpander{{background:rgba(255,255,255,0.88) !important;border-radius:18px !important;
  border:1px solid rgba(226,232,240,0.95) !important;margin-bottom:12px !important;
  overflow:hidden !important;box-shadow:0 8px 18px rgba(0,0,0,0.04) !important;
  transition:box-shadow 0.3s ease !important;}}
.stExpander:hover{{box-shadow:0 12px 24px rgba(0,0,0,0.09) !important;}}
.stExpander summary{{font-weight:800 !important;color:#111827 !important;font-size:17px !important;}}

@keyframes pageFade{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes fadeInSoft{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
@keyframes slideUp{{from{{opacity:0;transform:translateY(22px) scale(0.96)}}to{{opacity:1;transform:none}}}}
@keyframes popIn{{0%{{opacity:0;transform:scale(0.88)}}60%{{opacity:1;transform:scale(1.06)}}100%{{opacity:1;transform:scale(1)}}}}
@keyframes shine{{0%{{left:-120%}}28%{{left:120%}}100%{{left:120%}}}}

/* Readable native controls, including when a visitor chooses Streamlit dark mode. */
[data-testid="stSidebar"] {{ color-scheme: light; }}
[data-testid="stSidebar"] :is(p, label, span, h1, h2, h3, h4, small),
[data-testid="stMain"] [data-testid="stHeading"] :is(h1, h2, h3, h4),
[data-testid="stMain"] [data-testid="stWidgetLabel"] :is(p, label),
[data-testid="stMain"] [data-testid="stCaptionContainer"] p {{
  color: #111111 !important; opacity: 1 !important;
}}
[data-testid="stSidebar"] a {{ color: #111111 !important; text-decoration: underline; }}
[data-testid="stSelectbox"], [data-testid="stMultiSelect"], [data-testid="stTextInput"] {{
  color: #111111 !important; color-scheme: light;
}}
[data-testid="stSelectbox"] [data-baseweb="select"] > div,
[data-testid="stMultiSelect"] [data-baseweb="select"] > div,
[data-testid="stTextInput"] [data-baseweb="input"],
[data-testid="stTextInput"] [data-baseweb="base-input"],
[data-testid="stSelectbox"] button,
[data-testid="stSelectbox"] div:has(> input[role="combobox"]),
[data-testid="stSelectbox"] [role="combobox"] {{
  background: #ffffff !important; color: #111111 !important;
  border-color: #64748b !important; border-radius: 8px !important;
}}
[data-testid="stSelectbox"] [data-baseweb="select"] *,
[data-testid="stMultiSelect"] [data-baseweb="select"] *,
[data-testid="stSelectbox"] input,
[data-testid="stTextInput"] input {{
  color: #111111 !important; -webkit-text-fill-color: #111111 !important;
  caret-color: #111111 !important; opacity: 1 !important;
}}
[data-testid="stTextInput"] input {{ background: #ffffff !important; }}
[data-testid="stTextInput"] input::placeholder {{
  color: #454545 !important; -webkit-text-fill-color: #454545 !important; opacity: 1 !important;
}}
[data-testid="stSelectbox"] svg {{ color: #111111 !important; fill: #111111 !important; }}
[data-baseweb="popover"], [data-baseweb="popover"] [data-baseweb="menu"],
[role="listbox"], [role="option"] {{
  background: #ffffff !important; color: #111111 !important; color-scheme: light;
}}
[role="option"] *, [data-baseweb="menu"] * {{ color: #111111 !important; }}
[role="option"][aria-selected="true"], [role="option"][data-highlighted],
[role="option"]:hover {{ background: #fff0c2 !important; color: #111111 !important; }}
[data-testid="stSelectbox"]:focus-within,
[data-testid="stTextInput"]:focus-within {{ outline: 2px solid #1d4ed8; outline-offset: 2px; border-radius: 8px; }}

/* The entire section is one native Streamlit container, with an opaque surface. */
:is(.st-key-food_shelves_panel, .st-key-county_compare_panel) {{
  background: #ffffff !important; color: #111111 !important;
  border: 1px solid #cbd5e1 !important; border-radius: 18px !important;
  padding: 24px !important; margin: 18px 0 !important; color-scheme: light;
  box-shadow: 0 4px 16px rgba(0,0,0,.07);
}}
:is(.st-key-food_shelves_panel, .st-key-county_compare_panel) :is(h1,h2,h3,h4,p,li,span,strong,label,small,caption),
:is(.st-key-food_shelves_panel, .st-key-county_compare_panel) [data-testid="stCaptionContainer"] p,
:is(.st-key-food_shelves_panel, .st-key-county_compare_panel) [data-testid="stWidgetLabel"] p {{
  color: #111111 !important; opacity: 1 !important;
}}
:is(.st-key-food_shelves_panel, .st-key-county_compare_panel) [data-testid="stCaptionContainer"] p {{
  font-size: 14px !important; line-height: 1.6 !important;
}}
:is(.st-key-food_shelves_panel, .st-key-county_compare_panel) [data-testid="stAlert"] {{
  background: #eef5ff !important; color: #111111 !important; border: 1px solid #bfd3f5;
}}
:is(.st-key-food_shelves_panel, .st-key-county_compare_panel) [data-testid="stLinkButton"] a,
:is(.st-key-food_shelves_panel, .st-key-county_compare_panel) [data-testid="stDownloadButton"] button {{
  background: #fff3d6 !important; color: #111111 !important;
  border: 1px solid #9b741f !important; border-radius: 8px !important;
  font-weight: 600 !important;
}}
:is(.st-key-food_shelves_panel, .st-key-county_compare_panel) a {{ color: #111111 !important; }}
:is(.st-key-food_shelves_panel, .st-key-county_compare_panel) :is(a,button):focus-visible,
.shelf-table-scroll:focus-visible {{ outline: 2px solid #1d4ed8; outline-offset: 3px; }}
.shelf-table-scroll {{
  width: 100%; max-height: 450px; overflow: auto;
  border: 1px solid #94a3b8; border-radius: 8px; background: #ffffff;
}}
.shelf-table {{ width: 100%; border-collapse: collapse; font-size: 14px; color: #111111; }}
.shelf-table th, .shelf-table td {{
  color: #111111 !important; padding: 12px; border-bottom: 1px solid #d8e0e8;
  text-align: left; vertical-align: top; line-height: 1.5;
}}
.shelf-table th {{ background: #f0f4f8 !important; position: sticky; top: 0; z-index: 1; }}
.shelf-table td {{ background: #ffffff !important; min-width: 105px; }}
.shelf-table td:first-child {{ min-width: 170px; font-weight: 600; }}
.shelf-table td:nth-child(3) {{ min-width: 180px; }}
.shelf-table tr:nth-child(even) td {{ background: #f8fafc !important; }}
.shelf-table a {{ color: #111111 !important; text-decoration: underline !important; font-weight: 600; }}
@media (max-width: 640px) {{ :is(.st-key-food_shelves_panel, .st-key-county_compare_panel) {{ padding: 16px !important; }} }}

.compare-table tbody th {{ position: static; background: #ffffff !important; min-width: 190px; }}
.compare-table tbody tr:nth-child(even) th {{ background: #f8fafc !important; }}
.compare-table thead th {{ min-width: 160px; }}
</style>
""", unsafe_allow_html=True)

# ============================================================
# Load & enrich data
# ============================================================
df_raw = load_data()
county_col   = "County"
food_col     = "Food Need Score"
health_col   = "Health Risk Score"
priority_col = "Final Priority Score"

for col in [food_col, health_col, priority_col]:
    df_raw[col] = pd.to_numeric(df_raw[col], errors="coerce")

df_raw = df_raw.dropna(subset=[county_col, food_col, health_col, priority_col]).copy()
df_raw["Urgency Level"] = df_raw[priority_col].apply(urgency_label)
df_raw = df_raw.sort_values(priority_col, ascending=False).reset_index(drop=True)

enriched = df_raw.apply(compute_enriched, axis=1, result_type="expand")
df = pd.concat([df_raw, enriched], axis=1)
median_gap = df["Coverage Gap (people/shelter)"].median()
food_shelves_df, food_shelves_error = load_food_shelves(valid_counties=MN_COUNTY_FIPS)
df["Food Shelf Listings"] = pd.array(
    [county_listing_count(food_shelves_df, c, food_shelves_error) for c in df[county_col]],
    dtype="Int64",
)
df["Food Shelf Data Status"] = df["Food Shelf Listings"].apply(
    lambda count: "Unavailable" if pd.isna(count) else
    "No matching listings in snapshot" if count == 0 else "Directory listings; not a complete count"
)
df["Food Shelf Snapshot"] = (
    ", ".join(sorted(food_shelves_df["Retrieved_On"].unique())) if not food_shelves_error else ""
)

# ============================================================
# Session state
# ============================================================
if "started"   not in st.session_state: st.session_state.started   = False
if "page"      not in st.session_state: st.session_state.page      = "menu"
if "view_mode" not in st.session_state: st.session_state.view_mode = "Analyst View"

# ============================================================
# Landing page
# ============================================================
if not st.session_state.started:
    render_hero(header_banner)
    _, col_c, _ = st.columns([1,1,1])
    with col_c:
        if st.button("🌽  Let's Start", use_container_width=True):
            st.session_state.started = True
            st.session_state.page = "menu"
            st.rerun()

# ============================================================
# Menu page
# ============================================================
elif st.session_state.page == "menu":
    render_section_hero(
        "Welcome to Carelio",
        "Choose how you want to explore the project",
        "Explore the dashboard, compare two counties, or learn about the project and its scoring.",
        header_banner,
    )
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("⌂ Home", use_container_width=True):
            st.session_state.started = False; st.session_state.page = "menu"; st.rerun()
    with col2:
        if st.button("Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"; st.rerun()
    with col3:
        if st.button("Compare Counties", use_container_width=True):
            st.session_state.page = "compare"; st.rerun()
    with col4:
        if st.button("About Me", use_container_width=True):
            st.session_state.page = "about"; st.rerun()

# ============================================================
# Compare counties
# ============================================================
elif st.session_state.page == "compare":
    render_section_hero(
        "Compare Counties", "Understand the differences",
        "Two counties, one clear view of need, population and food-support listings.",
        header_banner,
    )
    nav1, nav2, nav3 = st.columns(3)
    with nav1:
        if st.button("← Menu", use_container_width=True): st.session_state.page = "menu"; st.rerun()
    with nav2:
        if st.button("Open Dashboard", use_container_width=True): st.session_state.page = "dashboard"; st.rerun()
    with nav3:
        if st.button("⌂ Home", use_container_width=True): st.session_state.started = False; st.session_state.page = "menu"; st.rerun()
    render_county_compare(df, food_shelves_df, food_shelves_error)

# ============================================================
# About page
# ============================================================
elif st.session_state.page == "about":
    render_section_hero(
        "About Carelio",
        "Why it was created and how the scores should be understood",
        "A practical tool built to help identify where food support may deserve closer attention across Minnesota.",
        header_banner,
    )

    nav1, nav2, nav3 = st.columns(3)
    with nav1:
        if st.button("← Back", use_container_width=True): st.session_state.page = "menu"; st.rerun()
    with nav2:
        if st.button("⌂ Home", use_container_width=True): st.session_state.started = False; st.session_state.page = "menu"; st.rerun()
    with nav3:
        if st.button("Open Dashboard", use_container_width=True): st.session_state.page = "dashboard"; st.rerun()

    st.markdown('<div class="content-wrap">', unsafe_allow_html=True)

    with st.expander("💼 Data Analyst / Business Analyst View — Professional Summary", expanded=False):
        st.markdown("""<div class="white-box">
<h3>Carelio — Minnesota Food Support Prioritization Website</h3>
<p><strong>Professional positioning:</strong> Carelio is a county-level decision-support website, not just a visualization. It helps nonprofit, grant, and planning teams identify where food support resources may need closer attention across Minnesota.</p>
<p>The website combines public source indicators, transparent scoring logic, planning-level estimates, and an interactive county map to support data-informed decisions.</p>
</div>""", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""<div class="blue-box">
<h3>Business Problem</h3>
<p>Nonprofits, grant teams, and planning stakeholders often use separate data sources to understand hunger, SNAP participation, population, and county-level vulnerability.</p>
<p>This makes it difficult to quickly identify which counties may need closer attention for funding, outreach, service planning, or partner conversations.</p>
</div>""", unsafe_allow_html=True)
        with c2:
            st.markdown("""<div class="green-box">
<h3>Business Solution</h3>
<p>Carelio brings those signals into one decision-support view with county ranking, priority tiers, stakeholder views, map exploration, and clear methodology notes.</p>
<p>The goal is to move from raw public data to practical prioritization and planning conversations.</p>
</div>""", unsafe_allow_html=True)

        st.markdown("""<div class="yellow-box">
<h3>How the Website Should Be Read</h3>
<ul>
<li><strong>Dashboard:</strong> Shows the county ranking, KPI cards, map, and selected county details.</li>
<li><strong>Compare Counties:</strong> Puts two counties side by side and explains differences in scores, population and listed food shelves.</li>
<li><strong>County Detail:</strong> Explains why a county is ranked higher or lower.</li>
<li><strong>Food Shelves:</strong> Lists food-shelf names, addresses, contacts, provider websites and directions for the selected county.</li>
<li><strong>Stakeholder View:</strong> Lets the same dashboard speak differently to data, grant, and planning users.</li>
<li><strong>Methodology & Data Sources:</strong> Explains where the data came from, what is official, and what is estimated.</li>
</ul>
</div>""", unsafe_allow_html=True)

        st.markdown("""<div class="white-box">
<h3>Dashboard Controls</h3>
<ul>
<li><strong>View Mode:</strong> Analyst View, Grant View, and Planning View change how the same county data is explained for different users.</li>
<li><strong>Priority Tier:</strong> Critical, High, Moderate, and Low are based on the Final Priority Score.</li>
<li><strong>County Filter:</strong> Users can select any Minnesota county to review county-specific score, people-scale estimate, and planning context.</li>
<li><strong>Map:</strong> The Minnesota county map shows geographic priority patterns and highlights the selected county.</li>
</ul>
</div>""", unsafe_allow_html=True)

        st.markdown("""<div class="pink-box">
<h3>Stakeholder View Explanation</h3>
<ul>
<li><strong>Analyst View:</strong> For data and business users. It focuses on score comparison, county ranking, priority tier, and map patterns so users can see which counties rank higher and why.</li>
<li><strong>Grant View:</strong> For grant, funding, and donor conversations. It translates scores into people-scale context such as estimated food-insecure residents, food shelf visits, and SNAP estimates so the need is easier to explain.</li>
<li><strong>Planning View:</strong> For outreach, operations, and resource planning. It highlights coverage gap and service-capacity signals so teams can identify counties that may need closer review for support, partners, or outreach.</li>
</ul>
</div>""", unsafe_allow_html=True)

        st.markdown("""<div class="blue-box">
<h3>Data Transparency Note</h3>
<p><strong>Food-shelf listings:</strong> Sourced from The Food Group / Hunger Solutions Find Help directory. Counts describe listings matched to counties using directory coordinates, not capacity or guaranteed availability. No matching records does not mean no services exist.</p>
<p><strong>Official data:</strong> County population values are official US Census 2020 counts.</p>
<p><strong>Planning estimates:</strong> People-level numbers such as estimated food-insecure residents, estimated food shelf visits, SNAP estimates, and coverage gap are planning-level estimates created from population and score-based assumptions.</p>
<p><strong>Professional use:</strong> These estimates are useful for prioritization and discussion, but should be validated with primary source files before formal grant reporting, policy reporting, or funding decisions.</p>
</div>""", unsafe_allow_html=True)

        st.markdown("""<div class="white-box">
<h3>Primary Data Links</h3>
<p>These are the public sources used to support the dashboard logic and methodology.</p>
</div>""", unsafe_allow_html=True)
        for src in DATA_SOURCES:
            st.markdown(f"""<div class="white-box" style="padding:14px 18px;margin-bottom:10px;">
<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap;">
  <div style="max-width:760px;">
    <div style="font-weight:800;font-size:15px;color:#111827;">{src['emoji']} {src['name']}</div>
    <div style="font-size:13px;color:#4b5563;margin:4px 0;">{src['what']}</div>
    <div style="font-size:12px;color:#6b7280;"><strong>Used for:</strong> {src['used_for']} &nbsp; | &nbsp; <strong>Update:</strong> {src['frequency']}</div>
  </div>
  <div style="display:flex;flex-direction:column;gap:6px;">
    <a href="{src['url']}" target="_blank" style="background:#f59e0b;color:white;padding:6px 12px;border-radius:8px;font-size:12px;font-weight:800;text-decoration:none;text-align:center;">Main site</a>
    <a href="{src['county_url']}" target="_blank" style="background:#1d4ed8;color:white;padding:6px 12px;border-radius:8px;font-size:12px;font-weight:800;text-decoration:none;text-align:center;">{src['county_label']}</a>
  </div>
</div>
</div>""", unsafe_allow_html=True)

        st.markdown("""<div class="green-box">
<h3>Project Summary</h3>
<p>I designed Carelio as a decision-support website for county-level food support planning. It combines public datasets, scoring logic, stakeholder views, and map-based analysis to help identify counties that may need closer review for outreach, funding, and resource planning.</p>
</div>""", unsafe_allow_html=True)

    with st.expander("🌱 Our Story"):
        st.markdown("""<div class="white-box">
            <p>Carelio was built to help sponsors, nonprofits, and community organizations better understand where food support may be needed most across Minnesota.</p>
            <p>It was designed to turn county-level analysis into something easier to explore, share, and use for planning meaningful support.</p>
        </div>""", unsafe_allow_html=True)

    with st.expander("💡 What Carelio Means"):
        st.markdown("""<div class="pink-box">
            <p>The name Carelio is inspired by care, community, and action. It reflects support, well-being, and organized efforts to help where the need may be greater.</p>
        </div>""", unsafe_allow_html=True)

    with st.expander("🎯 Why It Is Useful"):
        st.markdown("""<div class="yellow-box">
            <p>Carelio combines food need and health risk to provide a more practical view of community vulnerability.</p>
            <p>This helps organizations and supporters review county-level signals before planning outreach, sponsorship, partnerships, or food support efforts.</p>
        </div>""", unsafe_allow_html=True)

    with st.expander("🛠 How It Can Be Used"):
        st.markdown("""<div class="green-box"><ul>
            <li>Sponsors can review counties that may need greater support attention.</li>
            <li>Nonprofits can use it as a starting point for outreach planning.</li>
            <li>Community groups can compare counties before focusing local efforts.</li>
            <li>Partners can use it to support discussions around food support priorities.</li>
        </ul></div>""", unsafe_allow_html=True)

    with st.expander("📊 How Carelio Scores Work"):
        st.markdown("""<div class="white-box">
            <p><strong>Food Need Score</strong> — derived from county food insecurity rates published annually by
            <a href="https://map.feedingamerica.org/" target="_blank" style="color:#f59e0b;font-weight:700;">Feeding America's Map the Meal Gap</a>.
            The US food insecurity rate was 14.3% in 2023. Note: this source has an approximate 2-year reporting lag.</p>
            <p><strong>Health Risk Score</strong> — based on county-level health, social, and economic indicators from
            <a href="https://www.countyhealthrankings.org/health-data/minnesota/data-and-resources" target="_blank" style="color:#f59e0b;font-weight:700;">County Health Rankings & Roadmaps — Minnesota Health Data</a>.</p>
            <p><strong>Final Priority Score (0–100)</strong> — combines both scores to rank counties by overall relative need.</p>
            <ul>
                <li>Score ≥ 70 → <strong>Critical</strong></li>
                <li>Score 55–69 → <strong>High</strong></li>
                <li>Score 40–54 → <strong>Moderate</strong></li>
                <li>Score &lt; 40 → <strong>Low</strong></li>
            </ul>
            <p><strong>Important:</strong> These are comparative prioritization scores, not direct percentages of people affected.</p>
        </div>""", unsafe_allow_html=True)

    with st.expander("📐 How Every Estimate Is Calculated — Full Explanation"):
        st.markdown("""<div class="white-box">
<h3>Step 1 — County Population</h3>
<p>Source: <a href="https://data.census.gov/table?q=population&g=040XX00US27$0500000" target="_blank" style="color:#f59e0b;font-weight:700;">US Census Bureau 2020 Decennial Census</a><br>
These are <strong>real official counts</strong>, not estimated. Example: Hennepin = 1,281,565 · Traverse = 3,271.</p>
</div>""", unsafe_allow_html=True)
        st.markdown("""<div class="formula-box">population = MN_COUNTY_POPULATION.get(county)</div>""", unsafe_allow_html=True)

        st.markdown("""<div class="white-box">
<h3>Step 2 — Food Insecurity Rate</h3>
<p>Source logic: Statewide MN rate is ~20% (<a href="https://www.2harvest.org/sites/default/files/2025-01/mhh_2024-statewidehungerstudy_0.pdf" target="_blank" style="color:#f59e0b;font-weight:700;">Second Harvest Heartland 2024 Study</a>).
Counties with lower Food Need Scores get a lower rate (~8%), higher scores get a higher rate (~28%). This creates a sliding scale anchored to real statewide data.</p>
</div>""", unsafe_allow_html=True)
        st.markdown("""<div class="formula-box">fi_rate = <span>0.08</span> + (food_score / <span>100</span>) × <span>0.20</span><br># food_score=0 → 8%  |  food_score=50 → 18%  |  food_score=100 → 28%</div>""", unsafe_allow_html=True)

        st.markdown("""<div class="white-box">
<h3>Step 3 — Estimated People Food Insecure</h3>
<p>Population × food insecurity rate. This gives a real-scale number instead of an abstract score.</p>
</div>""", unsafe_allow_html=True)
        st.markdown("""<div class="formula-box">est_people_food_insecure = <span>int</span>(population × fi_rate)</div>""", unsafe_allow_html=True)

        st.markdown("""<div class="white-box">
<h3>Step 4 — Estimated Food Shelf Visits</h3>
<p>Source logic: From <a href="https://www.thefoodgroupmn.org/wp-content/uploads/2025/02/FINAL-Food-Shelf-Visits-2024-Report_22625.pdf" target="_blank" style="color:#f59e0b;font-weight:700;">The Food Group 2024 Food Shelf Visits Report</a>.
Roughly <strong>40%</strong> of food insecure people use food shelves (the rest use SNAP, family, etc.). Those who do visit average <strong>4.5 times per year</strong>.</p>
</div>""", unsafe_allow_html=True)
        st.markdown("""<div class="formula-box">est_visits = <span>int</span>(est_people_fi × <span>0.40</span> × <span>4.5</span>)<br># 40% of food insecure use shelves × 4.5 visits/year each</div>""", unsafe_allow_html=True)

        st.markdown("""<div class="white-box">
<h3>Step 5 — Estimated SNAP Enrollment</h3>
<p>Statewide MN SNAP participation is ~7% of population (<a href="https://dcyf.mn.gov/sites/default/files/2026-04/rf-food-support-cy-2024.xls" target="_blank" style="color:#f59e0b;font-weight:700;">MN DCYF SNAP CY2024 data</a>).
Scaled from 4% (low-need counties) to 11% (high-need counties) based on Food Need Score.</p>
</div>""", unsafe_allow_html=True)
        st.markdown("""<div class="formula-box">snap_rate = <span>0.04</span> + (food_score / <span>100</span>) × <span>0.07</span><br>est_snap = <span>int</span>(population × snap_rate)</div>""", unsafe_allow_html=True)

        st.markdown("""<div class="white-box">
<h3>Step 6 — Legacy Population-Based Planning Proxy</h3>
<p>This older model assumes one food-shelf location per 11,700 residents. It is a hypothetical planning assumption, not an observed county shelf count, service capacity measure or verified service gap.</p>
<p>The new <strong>Food Shelves</strong> section uses sourced directory listings instead. Those counts are kept separate from this formula and do not change county priority scores.</p>
</div>""", unsafe_allow_html=True)
        st.markdown("""<div class="formula-box">est_shelves = <span>max</span>(<span>1</span>, <span>round</span>(population / <span>11700</span>))<br>gap = est_people_food_insecure / est_shelves<br># Compare to statewide median → High / Moderate / Lower gap</div>""", unsafe_allow_html=True)

        st.markdown("""<div class="yellow-box" style="margin-top:10px;">
<h3>⚠️ Important Disclaimer</h3>
<p>All people-level numbers (food insecure, visits, SNAP, gap) are <strong>model-based estimates</strong> derived from the Food Need Score and county populations. They are approximations intended for prioritization and planning — <strong>not official counts</strong>.</p>
<p>For official county-level numbers, use the primary sources listed in the next section below.</p>
</div>""", unsafe_allow_html=True)

    with st.expander("🔗 Get the Real County-Level Data — Direct Download Links"):
        st.markdown("""<div class="blue-box">
<h3>Official sources for actual county-level data</h3>
<p>The estimates in Carelio are model-based. These links take you directly to the real county data for Minnesota:</p>
</div>""", unsafe_allow_html=True)

        for src in DATA_SOURCES:
            st.markdown(f"""<div class="white-box" style="padding:14px 18px;margin-bottom:10px;">
<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;">
  <div>
    <div style="font-weight:700;font-size:15px;color:#111827;">{src['emoji']} {src['name']}</div>
    <div style="font-size:13px;color:#4b5563;margin:4px 0;">{src['what']}</div>
    <div style="font-size:12px;color:#9ca3af;">🕐 {src['frequency']} &nbsp;·&nbsp; Used for: {src['used_for']}</div>
  </div>
  <div style="display:flex;flex-direction:column;gap:6px;flex-shrink:0;">
    <a href="{src['url']}" target="_blank"
       style="background:#f59e0b;color:white;padding:5px 12px;border-radius:8px;font-size:12px;font-weight:700;text-decoration:none;">
       🌐 Main site
    </a>
    <a href="{src['county_url']}" target="_blank"
       style="background:#1d4ed8;color:white;padding:5px 12px;border-radius:8px;font-size:12px;font-weight:700;text-decoration:none;">
       📥 {src['county_label']}
    </a>
  </div>
</div>
</div>""", unsafe_allow_html=True)

    with st.expander("🔍 How To Interpret This In Real Life"):
        st.markdown("""<div class="blue-box">
            <p>Carelio scores are designed for comparison across counties. They do not directly represent an exact percentage of people going without meals.</p>
            <p>They help highlight where relative need may be higher and where additional review or support attention may be warranted first.</p>
            <p>This tool is designed for <strong>prioritization</strong>, not precise measurement.</p>
        </div>""", unsafe_allow_html=True)

    with st.expander("🧮 Score Formula Used"):
        st.markdown("""<div class="yellow-box">
            <p><strong>Final Priority Score</strong> is based on the combined use of Food Need Score and Health Risk Score. This version is intended for prioritization and comparison across counties.</p>
        </div>""", unsafe_allow_html=True)

    a1, a2, a3 = st.columns(3)
    with a1:
        st.markdown("""<div class="action-card-yellow"><h3>Donate support</h3>
            <p>Share interest in donating funds, resources, or food support for higher-need Minnesota counties.</p></div>""", unsafe_allow_html=True)
        st.link_button("Open Donation Form", SUPPORT_FORM_URL, use_container_width=True)
    with a2:
        st.markdown("""<div class="action-card-pink"><h3>Become a sponsor</h3>
            <p>Organizations and businesses can express interest in sponsoring county-level food support efforts.</p></div>""", unsafe_allow_html=True)
        st.link_button("Open Sponsorship Form", SUPPORT_FORM_URL, use_container_width=True)
    with a3:
        st.markdown("""<div class="action-card-orange"><h3>Partner organization</h3>
            <p>Nonprofits and community organizations can connect to discuss outreach, planning, and collaboration.</p></div>""", unsafe_allow_html=True)
        st.link_button("Open Partnership Form", SUPPORT_FORM_URL, use_container_width=True)

    st.markdown('<div class="contact-box">', unsafe_allow_html=True)
    st.markdown('<h3>Contact</h3>', unsafe_allow_html=True)
    st.markdown('<p class="contact-name">Created by: Sruthi Vemavarapu</p>', unsafe_allow_html=True)
    st.markdown('<p>Click any icon below to open the destination directly.</p>', unsafe_allow_html=True)
    icon1, icon2, icon3, icon4 = st.columns(4)
    with icon1: st.markdown(f'<a class="contact-icon-card" href="mailto:{EMAIL_ADDRESS}" target="_blank"><div class="contact-icon">📧</div><div class="contact-icon-label">Email</div></a>', unsafe_allow_html=True)
    with icon2: st.markdown(f'<a class="contact-icon-card" href="{LINKEDIN_URL}" target="_blank"><div class="contact-icon">💼</div><div class="contact-icon-label">LinkedIn</div></a>', unsafe_allow_html=True)
    with icon3: st.markdown(f'<a class="contact-icon-card" href="{GITHUB_URL}" target="_blank"><div class="contact-icon">💻</div><div class="contact-icon-label">GitHub</div></a>', unsafe_allow_html=True)
    with icon4: st.markdown(f'<a class="contact-icon-card" href="{LIVE_URL}" target="_blank"><div class="contact-icon">🌐</div><div class="contact-icon-label">Live App</div></a>', unsafe_allow_html=True)

    st.markdown("<hr style='border:none;border-top:1px solid #d1d5db;margin:18px 0;'>", unsafe_allow_html=True)
    st.markdown('<h3>Update note</h3>', unsafe_allow_html=True)
    st.markdown('<p class="footer-note">Carelio supports planning, prioritization, and outreach using the latest available project dataset.</p>', unsafe_allow_html=True)
    st.markdown('<p class="footer-note">This tool is manually updated and does not refresh in real time.</p>', unsafe_allow_html=True)
    st.markdown('<p class="footer-note"><strong>Current update plan:</strong> Monthly manual data refresh</p>', unsafe_allow_html=True)
    st.markdown('<p class="footer-note"><strong>County-score dataset update:</strong> April 2026</p>', unsafe_allow_html=True)
    st.markdown('<p class="footer-note"><strong>Food-shelf directory snapshot:</strong> September 1, 2026</p>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
# Dashboard page
# ============================================================
elif st.session_state.page == "dashboard":
    render_section_hero(
        "Carelio Dashboard",
        "Interactive county priority view",
        "Review top-priority counties, compare urgency levels, and explore county-level need.",
        header_banner,
    )

    nav1, nav2, nav3, nav4 = st.columns(4)
    with nav1:
        if st.button("← Back", use_container_width=True): st.session_state.page = "menu"; st.rerun()
    with nav2:
        if st.button("⌂ Home", use_container_width=True): st.session_state.started = False; st.session_state.page = "menu"; st.rerun()
    with nav3:
        if st.button("Compare Counties", use_container_width=True): st.session_state.page = "compare"; st.rerun()
    with nav4:
        if st.button("About Me", use_container_width=True): st.session_state.page = "about"; st.rerun()

    # Sidebar
    st.sidebar.markdown("## Filters")
    st.sidebar.markdown("Choose an urgency level to focus the county ranking.")
    urgency_options = ["All"] + sorted(df["Urgency Level"].unique().tolist())
    selected_urgency = st.sidebar.selectbox("Urgency Level", urgency_options)

    filtered_df = df[df["Urgency Level"] == selected_urgency].copy() if selected_urgency != "All" else df.copy()
    filtered_df = filtered_df.sort_values(priority_col, ascending=False).reset_index(drop=True)

    st.sidebar.markdown("Select one county to review details.")
    county_list = filtered_df[county_col].tolist()
    selected_county = st.sidebar.selectbox("Select County", county_list)

    # View Mode
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👁️ View Mode")
    view_mode = st.sidebar.radio(
        "Choose your lens",
        ["Analyst View", "Grant View", "Planning View"],
        index=["Analyst View","Grant View","Planning View"].index(st.session_state.view_mode)
              if st.session_state.view_mode in ["Analyst View","Grant View","Planning View"] else 0,
        help="Analyst View: scores and ranking | Grant View: people-scale funding context | Planning View: coverage and resource planning",
    )
    with st.sidebar.expander("What do these views mean?"):
        st.markdown("""
        <div style="font-size:12px;line-height:1.7;color:#374151;">
        <b>Analyst View</b><br>Shows scores, rankings, and map patterns for data review.<br><br>
        <b>Grant View</b><br>Shows people-level estimates and simple funding context for grants or donor conversations.<br><br>
        <b>Planning View</b><br>Shows coverage gaps and planning signals for outreach and resource decisions.
        </div>
        """, unsafe_allow_html=True)
    st.session_state.view_mode = view_mode

    # Data Sources
    st.sidebar.markdown("---")
    with st.sidebar.expander("📚 Data Sources"):
        for src in DATA_SOURCES:
            st.markdown(f"""<div class="src-row">
<div class="src-name">{src['emoji']} {src['name']}</div>
<div class="src-what">{src['what']}</div>
<div class="src-freq">🕐 {src['frequency']} · {src['used_for']}</div>
<a href="{src['url']}" target="_blank" style="font-size:11px;color:#f59e0b;font-weight:600;">→ Main site</a>
&nbsp;&nbsp;
<a href="{src['county_url']}" target="_blank" style="font-size:11px;color:#1d4ed8;font-weight:600;">→ {src['county_label']}</a>
</div>""", unsafe_allow_html=True)
        st.markdown("""<div style="margin-top:8px;font-size:11px;color:#9ca3af;">
⚠️ People-level figures are model estimates based on county populations
(<a href="https://data.census.gov" target="_blank" style="color:#f59e0b;">US Census 2020</a>)
and statewide rates.</div>""", unsafe_allow_html=True)

    # Historical context with explicit units and source links.
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 Food Support Background")
    st.sidebar.markdown("**2023–2024 · Minnesota and U.S.**")
    st.sidebar.caption("These background facts stay the same when you select a county.")
    st.sidebar.markdown(
        "**Food insecurity** means not always being able to afford enough food. "
        "A **household** is one person or a group living together and sharing food."
    )
    st.sidebar.markdown("""
**🔺 18.4% average increase in visits**

Across Minnesota counties, food-shelf visits increased by an average of **18.4% from 2023 to 2024**. These are visits: one person visiting several times is counted several times.

[Source: The Food Group](https://www.thefoodgroupmn.org/more-minnesotans-visited-food-shelves-in-2024-than-ever-before-whats-behind-the-numbers/)

**👥 1 in 5 Minnesota households**

About **20 out of every 100 households** experienced difficulty affording enough food, according to the statewide study released in January 2025.

[Source: Second Harvest Heartland](https://www.2harvest.org/sites/default/files/2025-01/1.29.25-shh-2025-hunger-study-summit-press-release_final.pdf)

**🏪 487 food shelves tracked in 2024**

The 2024 report covered **487 food shelves participating in The Emergency Food Assistance Program (TEFAP)**. This is the report's coverage, not a complete count of every food-support location today.

[Source: The Food Group](https://www.thefoodgroupmn.org/more-minnesotans-visited-food-shelves-in-2024-than-ever-before-whats-behind-the-numbers/)

**📊 14.3% of U.S. people in 2023**

Around **14 out of every 100 people** in the U.S. lived in food-insecure households in 2023. This measures people; Minnesota's “1 in 5” figure measures households, so the figures are not directly comparable.

[Source: USDA](https://ers.usda.gov/media/9109/err-337.pdf?v=89305)
""")
    st.sidebar.caption(
        "The 487 sites in the historical report and Carelio's directory listings use different dates "
        "and inclusion rules. Their difference does not show how many new food shelves opened."
    )

    # Dashboard body
    county_data    = filtered_df[filtered_df[county_col] == selected_county].iloc[0]
    critical_count = int((filtered_df["Urgency Level"] == "Critical").sum())
    avg_score      = float(filtered_df[priority_col].mean())
    highest_score  = float(filtered_df[priority_col].max())
    top_county     = str(filtered_df.iloc[0][county_col])

    pop        = int(county_data["Population"])
    est_fi     = int(county_data["Est. People Food Insecure"])
    est_visits = int(county_data["Est. Food Shelf Visits 2024"])
    est_snap   = int(county_data["Est. SNAP Enrollment"])
    gap_ratio  = int(county_data["Coverage Gap (people/shelter)"])
    fi_rate    = float(county_data["Est. Food Insecurity Rate (%)"])

    if view_mode == "Analyst View":
        st.markdown('<div class="view-banner v-analyst">📐 <b>Analyst View</b> — shows priority scores, rankings, and map patterns for data review.</div>', unsafe_allow_html=True)
    elif view_mode == "Grant View":
        st.markdown('<div class="view-banner v-fundraiser">💰 <b>Grant View</b> — translates scores into people-level context for grant, funding, and donor conversations.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="view-banner v-policy">🧭 <b>Planning View</b> — highlights coverage gaps and counties that may need closer review for outreach or resource planning.</div>', unsafe_allow_html=True)

    st.markdown('<div class="content-wrap">', unsafe_allow_html=True)

    if filtered_df.empty:
        st.markdown("""<div class="pink-box"><h3>No counties available</h3>
            <p>No counties match the selected urgency level.</p></div>""", unsafe_allow_html=True)
    else:
        render_animated_metrics(len(filtered_df), top_county, highest_score, critical_count)

        top_left, top_right = st.columns([1.05, 1.15])

        with top_left:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown('<h3>Top 10 Current View</h3>', unsafe_allow_html=True)
            st.markdown('<div class="section-caption">These are the top counties inside the current urgency filter view.</div>', unsafe_allow_html=True)

            top10_df = filtered_df[[county_col, food_col, health_col, priority_col, "Urgency Level"]].head(10).copy()
            top10_df.index = range(1, len(top10_df) + 1)
            st.dataframe(top10_df, use_container_width=True)

            chart_df = filtered_df[[county_col, priority_col, "Urgency Level"]].head(10).copy()
            chart = alt.Chart(chart_df).mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8).encode(
                x=alt.X(f"{county_col}:N", sort="-y", title="County"),
                y=alt.Y(f"{priority_col}:Q", title="Final Priority Score"),
                color=alt.Color("Urgency Level:N",
                    scale=alt.Scale(domain=["Critical","High","Moderate","Low"],range=["#ef4444","#f59e0b","#3b82f6","#22c55e"]),
                    legend=alt.Legend(title="Urgency")),
                tooltip=[county_col, priority_col, "Urgency Level"],
            ).properties(height=280)
            st.altair_chart(chart, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with top_right:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            st.markdown('<h3 style="color:#111827;">County Map & Food Shelves</h3>', unsafe_allow_html=True)
            render_county_food_map(
                df, filtered_df, selected_county, selected_urgency,
                food_shelves_df, food_shelves_error,
            )

            st.markdown('<h3 style="color:#111827;margin-bottom:6px;">Selected County Detail</h3>', unsafe_allow_html=True)
            st.markdown(urgency_badge(county_data["Urgency Level"]), unsafe_allow_html=True)
            listing_count = county_listing_count(food_shelves_df, selected_county, food_shelves_error)
            listing_value = "Unavailable" if listing_count is None else (
                "No listings in snapshot" if listing_count == 0 else str(listing_count)
            )
            st.markdown(metric_card("🥫 Food-shelf listings", listing_value), unsafe_allow_html=True)
            st.caption("From the source directory. See names and contact details below.")
            st.markdown("<br>", unsafe_allow_html=True)

            render_triple_gauge(
                float(county_data[food_col]),
                float(county_data[health_col]),
                float(county_data[priority_col]),
                county_data["Urgency Level"],
            )

            st.markdown(metric_card("County", str(county_data[county_col])), unsafe_allow_html=True)

            if view_mode == "Grant View":
                st.markdown(f"""<div class="yellow-box" style="margin-top:10px;">
<h3 style="font-size:17px;">👥 Grant & Funding Context</h3>
<p><b>~{fmt_num(est_fi)}</b> people food insecure ({fi_rate:.1f}% of {fmt_num(pop)})</p>
<p><b>~{fmt_num(est_visits)}</b> estimated food shelf visits / year</p>
<p><b>~{fmt_num(est_snap)}</b> estimated SNAP enrollees</p>
<p style="font-size:11px;color:#9ca3af;margin-top:6px;">Model estimates — cite primary sources in formal documents.
<a href="https://map.feedingamerica.org/county/2021/overall/minnesota" target="_blank" style="color:#f59e0b;">Get real data →</a></p>
</div>""", unsafe_allow_html=True)
            elif view_mode == "Planning View":
                gap_label = "High" if gap_ratio > median_gap * 1.3 else "Moderate" if gap_ratio > median_gap * 0.8 else "Lower"
                st.markdown(f"""<div class="green-box" style="margin-top:10px;">
<h3 style="font-size:17px;">🧭 Planning & Coverage Context</h3>
<p><b>{gap_ratio:,}</b> estimated people per hypothetical food-shelf location</p>
<p>Statewide median: <b>{int(median_gap):,}</b> &nbsp;·&nbsp; Gap level: <b>{gap_label}</b></p>
<p style="font-size:11px;color:#9ca3af;margin-top:6px;">This older population-based model is separate from the directory listings below. It does not measure actual service capacity.
<a href="https://dcyf.mn.gov/emergency-food-assistance-program-tefap" target="_blank" style="color:#f59e0b;">TEFAP site data →</a></p>
</div>""", unsafe_allow_html=True)

            st.markdown('<p class="mini-note" style="margin-top:8px;">Use this panel to review the selected county before making outreach or support decisions.</p>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Food-shelf availability is visible in every stakeholder view.
        with st.container(border=True, key="food_shelves_panel"):
            render_food_shelves(food_shelves_df, selected_county, food_shelves_error)

        # All county ranking + CSV download
        st.markdown('<div class="green-box">', unsafe_allow_html=True)
        col_t, col_dl = st.columns([3,1])
        with col_t:
            st.markdown('<h3 style="color:#111827;margin-bottom:6px;">All County Ranking</h3>', unsafe_allow_html=True)
            st.markdown('<div class="section-caption">Counties ranked by Final Priority Score in the current view.</div>', unsafe_allow_html=True)
        with col_dl:
            export_cols = [county_col,"Urgency Level",food_col,health_col,priority_col,
                           "Population","Est. People Food Insecure","Est. Food Insecurity Rate (%)",
                           "Est. Food Shelf Visits 2024","Est. SNAP Enrollment","Coverage Gap (people/shelter)",
                           "Food Shelf Listings","Food Shelf Data Status","Food Shelf Snapshot"]
            buf = io.BytesIO()
            filtered_df[export_cols].to_csv(buf, index=False)
            st.download_button("⬇️ Download CSV", data=buf.getvalue(),
                               file_name="carelio_mn_data.csv", mime="text/csv")

        display_df = filtered_df[[county_col, food_col, health_col, priority_col, "Urgency Level"]].copy()
        display_df.index = range(1, len(display_df) + 1)
        st.dataframe(display_df, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Insight boxes
        why_title, why_text = why_county_ranked(county_data[food_col], county_data[health_col],
                                                county_data[priority_col], county_data["Urgency Level"])
        b1, b2, b3, b4 = st.columns(4)
        with b1:
            st.markdown(f"""<div class="yellow-box"><h3>What this score means</h3>
                <p>{explain_score(county_data[priority_col])}</p></div>""", unsafe_allow_html=True)
        with b2:
            st.markdown(f"""<div class="blue-box"><h3>{why_title}</h3>
                <p>{why_text}</p></div>""", unsafe_allow_html=True)
        with b3:
            st.markdown(f"""<div class="pink-box"><h3>Why compared with others</h3>
                <p>{compare_county_to_others(county_data, filtered_df)}</p></div>""", unsafe_allow_html=True)
        with b4:
            st.markdown(f"""<div class="white-box"><h3>Average score in current view</h3>
                <p style="font-size:28px;font-weight:700;">{avg_score:.2f}</p>
                <p class="mini-note">This average changes when the urgency filter changes.</p></div>""", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""<div class="white-box"><h3>How dashboard works</h3><ul>
                <li>Scan the top 10 view to identify stronger need quickly.</li>
                <li>Use the Minnesota map to see where the selected urgency group appears.</li>
                <li>Select a county from the sidebar to review more closely.</li>
                <li>Use the ranking table to compare counties side by side.</li>
            </ul></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="white-box"><h3>How priority is calculated</h3>
                <p>{priority_formula_text()}</p>
                <p><strong>Food Need Score</strong> and <strong>Health Risk Score</strong> are used together to support comparison across Minnesota counties.</p>
            </div>""", unsafe_allow_html=True)

        # Data footnote
        st.markdown("""<div style="margin-top:14px;padding:12px 18px;background:rgba(255,255,255,0.75);
border-radius:12px;border:1px solid rgba(220,220,220,0.8);">
<p style="font-size:12px;color:#6b7280;margin:0;line-height:1.8;">
<b>Data sources:</b>
Food Need Score — <a href="https://map.feedingamerica.org/" target="_blank" style="color:#f59e0b;">Feeding America Map the Meal Gap</a> (annual, ~2yr lag) ·
Health Risk Score — <a href="https://www.countyhealthrankings.org/health-data/minnesota/data-and-resources" target="_blank" style="color:#f59e0b;">County Health Rankings & Roadmaps Minnesota Health Data</a> ·
Population — <a href="https://data.census.gov/table?q=population&g=040XX00US27$0500000" target="_blank" style="color:#f59e0b;">US Census 2020 Decennial Census</a> ·
People estimates — model based on <a href="https://www.2harvest.org/sites/default/files/2025-01/mhh_2024-statewidehungerstudy_0.pdf" target="_blank" style="color:#f59e0b;">Second Harvest Heartland 2024 Hunger Study</a> ·
Food shelf visits — <a href="https://www.thefoodgroupmn.org/wp-content/uploads/2025/02/FINAL-Food-Shelf-Visits-2024-Report_22625.pdf" target="_blank" style="color:#f59e0b;">The Food Group + MN DCYF 2024 Report</a> ·
SNAP — <a href="https://dcyf.mn.gov/snap-food-assistance-minnesota" target="_blank" style="color:#f59e0b;">MN DCYF SNAP County Statistics</a>
</p></div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
