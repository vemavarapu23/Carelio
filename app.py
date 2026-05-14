import base64
import io
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import altair as alt
import plotly.graph_objects as go
import requests

st.set_page_config(page_title="Carelio", layout="wide")

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
@st.cache_data
def load_county_geojson():
    url = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
    r = requests.get(url, timeout=30); r.raise_for_status()
    return r.json()

def build_map(full_df, filtered_df, selected_county, selected_urgency):
    geojson = load_county_geojson()
    map_df = full_df.copy()
    map_df["fips"] = map_df["County"].map(MN_COUNTY_FIPS)
    map_df = map_df.dropna(subset=["fips"]).copy()
    color_map = {"Low":"#22c55e","Moderate":"#3b82f6","High":"#f59e0b","Critical":"#ef4444"}
    fig = go.Figure()
    if selected_urgency == "All":
        for urgency, color in color_map.items():
            subset = map_df[map_df["Urgency Level"] == urgency].copy()
            if subset.empty: continue
            fig.add_trace(go.Choropleth(
                geojson=geojson, locations=subset["fips"], z=[1]*len(subset),
                featureidkey="id", colorscale=[[0,color],[1,color]],
                showscale=False, marker_line_color="white", marker_line_width=0.8,
                customdata=subset[["County","Urgency Level","Food Need Score","Health Risk Score","Final Priority Score","Est. People Food Insecure","Population"]],
                hovertemplate="<b>%{customdata[0]}</b><br>Urgency: %{customdata[1]}<br>Priority Score: %{customdata[4]:.1f}<br>Est. People Food Insecure: %{customdata[5]:,}<br>Population: %{customdata[6]:,}<extra></extra>",
                name=urgency,
            ))
    else:
        fig.add_trace(go.Choropleth(
            geojson=geojson, locations=map_df["fips"], z=[1]*len(map_df),
            featureidkey="id", colorscale=[[0,"#d1d5db"],[1,"#d1d5db"]],
            showscale=False, marker_line_color="white", marker_line_width=0.8,
            hoverinfo="skip", name="Other Counties",
        ))
        hdf = filtered_df.copy()
        hdf["fips"] = hdf["County"].map(MN_COUNTY_FIPS)
        hdf = hdf.dropna(subset=["fips"]).copy()
        if not hdf.empty:
            hc = color_map.get(selected_urgency,"#111827")
            fig.add_trace(go.Choropleth(
                geojson=geojson, locations=hdf["fips"], z=[1]*len(hdf),
                featureidkey="id", colorscale=[[0,hc],[1,hc]],
                showscale=False, marker_line_color="white", marker_line_width=1.2,
                customdata=hdf[["County","Urgency Level","Food Need Score","Health Risk Score","Final Priority Score","Est. People Food Insecure","Population"]],
                hovertemplate="<b>%{customdata[0]}</b><br>Urgency: %{customdata[1]}<br>Priority: %{customdata[4]:.1f}<br>Est. People Food Insecure: %{customdata[5]:,}<extra></extra>",
                name=selected_urgency,
            ))
    if selected_county in map_df["County"].values:
        sel = map_df[map_df["County"] == selected_county]
        fig.add_trace(go.Choropleth(
            geojson=geojson, locations=sel["fips"], z=[1], featureidkey="id",
            colorscale=[[0,"rgba(0,0,0,0)"],[1,"rgba(0,0,0,0)"]],
            showscale=False, marker_line_color="black", marker_line_width=3,
            hoverinfo="skip", name="Selected County",
        ))
    fig.update_geos(visible=False, projection_type="mercator",
                    center={"lat":46.3,"lon":-94.2},
                    lataxis_range=[43.4,49.5], lonaxis_range=[-97.5,-89.0])
    fig.update_layout(margin=dict(l=0,r=0,t=0,b=0), height=500,
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="v",yanchor="top",y=0.98,xanchor="left",x=1.01,title="Urgency"))
    return fig

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
        "Open the dashboard for practical county analysis or About Me to understand the story, scoring, and support options.",
        header_banner,
    )
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("⌂ Home", use_container_width=True):
            st.session_state.started = False; st.session_state.page = "menu"; st.rerun()
    with col2:
        if st.button("Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"; st.rerun()
    with col3:
        if st.button("About Me", use_container_width=True):
            st.session_state.page = "about"; st.rerun()

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
<li><strong>County Detail:</strong> Explains why a county is ranked higher or lower.</li>
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
<h3>Step 6 — Coverage Gap</h3>
<p>Minnesota has ~487 TEFAP food shelves serving ~5.7M people = <strong>1 shelter per 11,700 people</strong> statewide.
A county with more people food insecure per estimated shelter has a <strong>higher gap</strong> — meaning need may outpace available services.</p>
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
    st.markdown('<p class="footer-note"><strong>Last updated:</strong> April 2026</p>', unsafe_allow_html=True)
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

    nav1, nav2, nav3 = st.columns(3)
    with nav1:
        if st.button("← Back", use_container_width=True): st.session_state.page = "menu"; st.rerun()
    with nav2:
        if st.button("⌂ Home", use_container_width=True): st.session_state.started = False; st.session_state.page = "menu"; st.rerun()
    with nav3:
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

    # MN 2024 Context
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 MN 2024 Context")
    st.sidebar.markdown("""<div style="font-size:13px;line-height:1.8;color:#374151;">
🔺 <b>18.4%</b> avg increase in food shelf visits 2024<br>
👥 <b>1 in 5</b> MN households food insecure<br>
🏪 <b>487</b> TEFAP food shelves statewide<br>
📊 <b>14.3%</b> US food insecurity rate (2023)<br>
<i style="font-size:11px;color:#9ca3af;">Sources: Feeding America · The Food Group · Second Harvest Heartland</i>
</div>""", unsafe_allow_html=True)

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
            st.markdown('<h3>Minnesota County Map</h3>', unsafe_allow_html=True)
            st.markdown('<div class="section-caption">Colors reflect urgency. Black border = selected county. Hover to see population & people food insecure.</div>', unsafe_allow_html=True)

            fig = build_map(df, filtered_df, selected_county, selected_urgency)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown('<h3 style="color:#111827;margin-bottom:6px;">Selected County Detail</h3>', unsafe_allow_html=True)
            st.markdown(urgency_badge(county_data["Urgency Level"]), unsafe_allow_html=True)
            st.markdown(coverage_gap_badge(gap_ratio, median_gap), unsafe_allow_html=True)
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
<p><b>{gap_ratio:,}</b> people per estimated food shelter</p>
<p>Statewide median: <b>{int(median_gap):,}</b> &nbsp;·&nbsp; Gap level: <b>{gap_label}</b></p>
<p style="font-size:11px;color:#9ca3af;margin-top:6px;">Shelter count is a proxy.
<a href="https://dcyf.mn.gov/emergency-food-assistance-program-tefap" target="_blank" style="color:#f59e0b;">TEFAP site data →</a></p>
</div>""", unsafe_allow_html=True)

            st.markdown('<p class="mini-note" style="margin-top:8px;">Use this panel to review the selected county before making outreach or support decisions.</p>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # All county ranking + CSV download
        st.markdown('<div class="green-box">', unsafe_allow_html=True)
        col_t, col_dl = st.columns([3,1])
        with col_t:
            st.markdown('<h3 style="color:#111827;margin-bottom:6px;">All County Ranking</h3>', unsafe_allow_html=True)
            st.markdown('<div class="section-caption">Counties ranked by Final Priority Score in the current view.</div>', unsafe_allow_html=True)
        with col_dl:
            export_cols = [county_col,"Urgency Level",food_col,health_col,priority_col,
                           "Population","Est. People Food Insecure","Est. Food Insecurity Rate (%)",
                           "Est. Food Shelf Visits 2024","Est. SNAP Enrollment","Coverage Gap (people/shelter)"]
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
