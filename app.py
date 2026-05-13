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
# County Populations — US Census Bureau, 2020 Decennial Census
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
# Data Sources
# ============================================================
DATA_SOURCES = [
    {
        "emoji":"🟩","name":"Feeding America — Map the Meal Gap",
        "what":"County food insecurity rates & food budget shortfall. US rate: 14.3% in 2023.",
        "frequency":"Annual (~2-year reporting lag)",
        "url":"https://map.feedingamerica.org/",
        "used_for":"Food Need Score base",
    },
    {
        "emoji":"🟦","name":"MN DCYF — SNAP County Statistics",
        "what":"Monthly county SNAP cases, persons enrolled, benefit amounts. CY2024 Excel available.",
        "frequency":"Monthly",
        "url":"https://dcyf.mn.gov/snap-food-assistance-minnesota",
        "used_for":"SNAP enrollment context",
    },
    {
        "emoji":"🟪","name":"The Food Group + MN DCYF — Food Shelf Visits",
        "what":"Annual food shelf visit counts across 487 TEFAP-participating MN sites. 2024: 18.4% avg increase.",
        "frequency":"Annual (2024 report: Feb 2025)",
        "url":"https://www.thefoodgroupmn.org",
        "used_for":"Food shelf utilization context",
    },
    {
        "emoji":"🟧","name":"Second Harvest Heartland — Statewide Hunger Study",
        "what":"Household food insecurity survey with Wilder Research. 1 in 5 MN households food insecure (2024).",
        "frequency":"Annual (Jan 2025)",
        "url":"https://www.2harvest.org/about-us/make-hunger-history",
        "used_for":"Statewide benchmarks",
    },
    {
        "emoji":"⬜","name":"US Census Bureau — ACS 5-Year Estimates",
        "what":"County population, poverty rates, demographics.",
        "frequency":"Annual",
        "url":"https://www.census.gov/programs-surveys/acs",
        "used_for":"Health Risk Score, population",
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
# Helpers — original (unchanged)
# ============================================================
def get_base64_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

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

def urgency_badge(urgency: str) -> str:
    styles = {
        "Critical": ("#ffe3e3","#b00020","pulse-critical"),
        "High":     ("#fff1d6","#b45309","pulse-high"),
        "Moderate": ("#dbeafe","#1d4ed8","pulse-moderate"),
        "Low":      ("#dcfce7","#15803d","pulse-low"),
    }
    bg, fg, cls = styles.get(urgency, ("#f3f4f6","#111827",""))
    return f'<div class="urgency-badge badge-pop {cls}" style="background:{bg};color:{fg};">Urgency Level: {urgency}</div>'

def metric_card(label: str, value: str) -> str:
    return f"""<div class="metric-card glass-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>"""

def explain_score(score):
    if score >= 70: return "High priority — this county shows relatively higher food and health vulnerability compared with others in the dataset."
    elif score >= 55: return "Moderate-high priority — this county may deserve targeted review and stronger support attention."
    elif score >= 40: return "Moderate priority — some level of need is present and may benefit from additional review."
    return "Lower priority — comparatively lower need based on the current dataset."

def why_county_ranked(food_score, health_score, priority_score, urgency):
    if urgency == "Critical":
        title = "Why this county is critical"
        if food_score >= 70 and health_score >= 70:
            text = "Both food need and health risk are very high compared with many other counties. The combined effect pushes this county into the highest urgency group."
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
            text = "Food need shows some concern, but the total combined risk is not high enough for a higher urgency group."
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
# NEW Helpers — feedback improvements
# ============================================================
def compute_enriched(row):
    county = row["County"]
    pop = MN_COUNTY_POPULATION.get(county, 0)
    food_score = float(row["Food Need Score"])
    fi_rate = 0.08 + (food_score / 100) * 0.20
    est_fi = int(pop * fi_rate)
    est_visits = int(est_fi * 0.40 * 4.5)
    snap_rate = 0.04 + (food_score / 100) * 0.07
    est_snap = int(pop * snap_rate)
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
    r = requests.get(url, timeout=30)
    r.raise_for_status()
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
        highlight_df = filtered_df.copy()
        highlight_df["fips"] = highlight_df["County"].map(MN_COUNTY_FIPS)
        highlight_df = highlight_df.dropna(subset=["fips"]).copy()
        if not highlight_df.empty:
            hc = color_map.get(selected_urgency,"#111827")
            fig.add_trace(go.Choropleth(
                geojson=geojson, locations=highlight_df["fips"], z=[1]*len(highlight_df),
                featureidkey="id", colorscale=[[0,hc],[1,hc]],
                showscale=False, marker_line_color="white", marker_line_width=1.2,
                customdata=highlight_df[["County","Urgency Level","Food Need Score","Health Risk Score","Final Priority Score","Est. People Food Insecure","Population"]],
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
# Animated Components
# ============================================================
def render_hero_animated(b64):
    html = f"""
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}body{{background:transparent;overflow:hidden;}}
.hero{{position:relative;min-height:590px;display:flex;align-items:center;justify-content:center;
  text-align:center;border-radius:34px;overflow:hidden;
  background:linear-gradient(rgba(0,0,0,0.42),rgba(0,0,0,0.58)),url('data:image/avif;base64,{b64}');
  background-size:cover;background-position:center;box-shadow:0 24px 60px rgba(0,0,0,0.25);
  animation:heroRise 0.9s ease-out both;}}
@keyframes heroRise{{from{{opacity:0;transform:translateY(24px) scale(0.98)}}to{{opacity:1;transform:translateY(0) scale(1)}}}}
.hero::before{{content:"";position:absolute;inset:0;
  background:linear-gradient(120deg,rgba(255,255,255,0.06),transparent,rgba(255,255,255,0.08));
  animation:shim 8s linear infinite;pointer-events:none;}}
@keyframes shim{{0%{{transform:translateX(-60%)}}100%{{transform:translateX(60%)}}}}
.p{{position:absolute;bottom:-60px;font-size:1.75rem;opacity:0;animation:floatUp linear infinite;pointer-events:none;z-index:1;}}
@keyframes floatUp{{0%{{transform:translateY(0) rotate(0deg) scale(0.8);opacity:0}}8%{{opacity:0.65}}85%{{opacity:0.3}}100%{{transform:translateY(-680px) rotate(360deg) scale(1.2);opacity:0}}}}
.spark{{position:absolute;border-radius:50%;background:rgba(255,255,255,0.75);animation:sparkle ease-in-out infinite;pointer-events:none;}}
@keyframes sparkle{{0%,100%{{opacity:0;transform:scale(0)}}50%{{opacity:1;transform:scale(1)}}}}
.glow-border{{position:absolute;inset:0;border-radius:34px;pointer-events:none;z-index:3;
  animation:glowPulse 4s ease-in-out infinite;}}
@keyframes glowPulse{{0%,100%{{box-shadow:inset 0 0 0 2px rgba(255,200,80,0.15),0 0 60px rgba(255,160,40,0.08)}}50%{{box-shadow:inset 0 0 0 2px rgba(255,200,80,0.38),0 0 100px rgba(255,160,40,0.22)}}}}
.inner{{position:relative;z-index:2;max-width:900px;padding:24px;}}
.title{{color:#fff;font-size:90px;font-weight:900;letter-spacing:1px;margin-bottom:12px;line-height:1;
  text-shadow:0 8px 32px rgba(0,0,0,0.28);animation:titleDrop 1s cubic-bezier(0.34,1.56,0.64,1) both;}}
@keyframes titleDrop{{from{{opacity:0;transform:translateY(-30px) scale(0.88)}}to{{opacity:1;transform:translateY(0) scale(1)}}}}
.subtitle{{color:#fffaf2;font-size:28px;font-weight:800;margin-bottom:14px;line-height:1.4;
  overflow:hidden;white-space:nowrap;border-right:3px solid rgba(255,255,255,0.8);
  width:0;margin-left:auto;margin-right:auto;
  animation:typing 2.2s steps(42,end) 0.8s both,blink 0.75s step-end 0.8s infinite;}}
@keyframes typing{{from{{width:0}}to{{width:100%}}}}
@keyframes blink{{50%{{border-color:transparent}}}}
.bold{{color:#fff;font-size:20px;font-weight:800;margin-bottom:16px;animation:fadeUp 0.8s ease-out 2.8s both;}}
.small{{color:#fffaf5;font-size:17px;line-height:1.75;max-width:720px;margin:0 auto;animation:fadeUp 0.8s ease-out 3.1s both;}}
@keyframes fadeUp{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:translateY(0)}}}}
.wave-wrap{{position:absolute;bottom:-2px;left:0;right:0;height:50px;z-index:2;overflow:hidden;}}
.wave{{fill:rgba(255,255,255,0.07);animation:waveMove 5s ease-in-out infinite;transform-origin:center;}}
@keyframes waveMove{{0%,100%{{transform:scaleX(1) translateX(0)}}50%{{transform:scaleX(1.08) translateX(-2%)}}}}
</style>
<div class="hero">
  <div class="p" style="left:3%;animation-duration:9s;animation-delay:0s;">🌽</div>
  <div class="p" style="left:10%;animation-duration:11s;animation-delay:1.4s;">🥕</div>
  <div class="p" style="left:18%;animation-duration:8s;animation-delay:2.9s;">🍎</div>
  <div class="p" style="left:27%;animation-duration:10s;animation-delay:0.7s;">🥦</div>
  <div class="p" style="left:37%;animation-duration:12s;animation-delay:2.2s;">🌾</div>
  <div class="p" style="left:50%;animation-duration:9.5s;animation-delay:4s;">🥗</div>
  <div class="p" style="left:61%;animation-duration:8.5s;animation-delay:1.1s;">🍊</div>
  <div class="p" style="left:71%;animation-duration:10.5s;animation-delay:2.7s;">🫐</div>
  <div class="p" style="left:80%;animation-duration:9s;animation-delay:0.4s;">🥬</div>
  <div class="p" style="left:89%;animation-duration:11.5s;animation-delay:3.4s;">🍇</div>
  <div class="p" style="left:95%;animation-duration:8s;animation-delay:1.8s;">🌽</div>
  <div class="spark" style="width:4px;height:4px;top:18%;left:14%;animation-duration:3s;animation-delay:0s;"></div>
  <div class="spark" style="width:3px;height:3px;top:33%;left:77%;animation-duration:2.5s;animation-delay:0.8s;"></div>
  <div class="spark" style="width:5px;height:5px;top:58%;left:44%;animation-duration:3.5s;animation-delay:1.4s;"></div>
  <div class="spark" style="width:3px;height:3px;top:24%;left:59%;animation-duration:2.8s;animation-delay:0.4s;"></div>
  <div class="spark" style="width:4px;height:4px;top:68%;left:21%;animation-duration:3.2s;animation-delay:2s;"></div>
  <div class="spark" style="width:3px;height:3px;top:43%;left:87%;animation-duration:2.6s;animation-delay:1s;"></div>
  <div class="inner">
    <div class="title">Carelio</div>
    <div class="subtitle">Minnesota food support prioritization</div>
    <div class="bold">See which counties may need food support attention most.</div>
    <div class="small">Explore county rankings, compare urgency levels, and review an interactive experience built to support sponsors, nonprofits, and community organizations across Minnesota.</div>
  </div>
  <div class="glow-border"></div>
  <div class="wave-wrap">
    <svg viewBox="0 0 1200 50" preserveAspectRatio="none" height="50" width="100%">
      <path class="wave" d="M0,30 C200,55 400,5 600,30 C800,55 1000,5 1200,30 L1200,50 L0,50 Z"/>
    </svg>
  </div>
</div>"""
    components.html(html, height=610, scrolling=False)


def render_section_hero(title, tagline, subnote, b64):
    html = f"""
<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}
body{{background:transparent;overflow:hidden;}}
.sh{{position:relative;overflow:hidden;
  background:linear-gradient(rgba(0,0,0,0.44),rgba(0,0,0,0.52)),url('data:image/avif;base64,{b64}');
  background-size:cover;background-position:center;border-radius:30px;min-height:200px;
  display:flex;align-items:center;justify-content:center;text-align:center;padding:32px;
  box-shadow:0 16px 36px rgba(0,0,0,0.18);animation:rise 0.7s ease-out both;}}
@keyframes rise{{from{{opacity:0;transform:translateY(18px) scale(0.98)}}to{{opacity:1;transform:translateY(0) scale(1)}}}}
.sh::before{{content:"";position:absolute;inset:0;
  background:linear-gradient(120deg,rgba(255,255,255,0.07),transparent,rgba(255,255,255,0.09));
  animation:shim 8s linear infinite;pointer-events:none;}}
@keyframes shim{{0%{{transform:translateX(-60%)}}100%{{transform:translateX(60%)}}}}
.mp{{position:absolute;font-size:1.2rem;opacity:0;animation:mpf linear infinite;pointer-events:none;}}
@keyframes mpf{{0%{{transform:translateY(0);opacity:0}}15%{{opacity:0.45}}85%{{opacity:0.15}}100%{{transform:translateY(-260px);opacity:0}}}}
.inner{{position:relative;z-index:2;}}
h1{{color:white;font-size:58px;font-weight:900;margin:0 0 8px;animation:pop 0.8s cubic-bezier(0.34,1.56,0.64,1) 0.1s both;}}
@keyframes pop{{from{{opacity:0;transform:scale(0.88)}}to{{opacity:1;transform:scale(1)}}}}
.tl{{color:#fffaf2;font-size:19px;font-weight:700;margin:6px 0;animation:fu 0.6s ease-out 0.4s both;}}
.sn{{color:#fff8ef;font-size:15px;margin:10px 0 0;line-height:1.65;font-weight:500;animation:fu 0.6s ease-out 0.6s both;}}
@keyframes fu{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:translateY(0)}}}}
</style>
<div class="sh">
  <div class="mp" style="left:5%;bottom:-20px;animation-duration:7s;animation-delay:0s;">🌽</div>
  <div class="mp" style="left:88%;bottom:-20px;animation-duration:9s;animation-delay:1.5s;">🥕</div>
  <div class="mp" style="left:50%;bottom:-20px;animation-duration:8s;animation-delay:3s;">🍎</div>
  <div class="inner">
    <h1>{title}</h1>
    <div class="tl">{tagline}</div>
    <div class="sn">{subnote}</div>
  </div>
</div>"""
    components.html(html, height=220, scrolling=False)


def render_animated_metrics(n, top_county, highest, critical):
    html = f"""
<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}
body{{background:transparent;}}
.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:2px;}}
.card{{background:linear-gradient(135deg,#fff,#fff9f2);border:1px solid rgba(243,217,164,0.92);
  border-radius:18px;padding:18px;box-shadow:0 6px 14px rgba(255,138,0,0.10);
  position:relative;overflow:hidden;opacity:0;transform:translateY(20px) scale(0.95);
  animation:cardIn 0.55s cubic-bezier(0.34,1.56,0.64,1) forwards;
  cursor:default;transition:transform 0.3s ease,box-shadow 0.3s ease;}}
.card:hover{{transform:translateY(-7px) scale(1.04);box-shadow:0 18px 32px rgba(255,138,0,0.18);}}
.card:nth-child(1){{animation-delay:0.05s;}}.card:nth-child(2){{animation-delay:0.15s;}}
.card:nth-child(3){{animation-delay:0.25s;}}.card:nth-child(4){{animation-delay:0.35s;}}
.card::before{{content:"";position:absolute;top:0;left:-120%;width:100%;height:100%;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,0.42),transparent);animation:shine 4.5s ease infinite;}}
.card:nth-child(2)::before{{animation-delay:1s;}}.card:nth-child(3)::before{{animation-delay:2s;}}.card:nth-child(4)::before{{animation-delay:3s;}}
@keyframes shine{{0%{{left:-120%}}28%{{left:120%}}100%{{left:120%}}}}
@keyframes cardIn{{to{{opacity:1;transform:translateY(0) scale(1);}}}}
.lbl{{color:#6b7280;font-size:13px;margin-bottom:6px;}}
.val{{color:#111827;font-size:26px;font-weight:700;line-height:1.2;}}
.dot{{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:7px;vertical-align:middle;
  background:#ef4444;animation:dotPulse 1.8s ease-in-out infinite;}}
@keyframes dotPulse{{0%,100%{{box-shadow:0 0 0 0 rgba(239,68,68,0.55);}}50%{{box-shadow:0 0 0 9px rgba(239,68,68,0);}}}}
</style>
<div class="grid">
  <div class="card"><div class="lbl">Counties in current view</div><div class="val" id="v1">0</div></div>
  <div class="card"><div class="lbl">Top county</div><div class="val">{top_county}</div></div>
  <div class="card"><div class="lbl">Highest score</div><div class="val" id="v3">0.00</div></div>
  <div class="card"><div class="lbl">Critical counties</div><div class="val"><span class="dot"></span><span id="v4">0</span></div></div>
</div>
<script>
function countUp(id,target,dur,isFloat){{
  const el=document.getElementById(id);if(!el)return;
  const s=performance.now();
  (function step(now){{
    const p=Math.min((now-s)/dur,1),e=1-Math.pow(1-p,3);
    el.textContent=isFloat?(e*target).toFixed(2):Math.floor(e*target);
    if(p<1)requestAnimationFrame(step);else el.textContent=isFloat?target.toFixed(2):target;
  }})(performance.now());
}}
setTimeout(()=>{{countUp('v1',{n},900,false);countUp('v3',{highest},1400,true);countUp('v4',{critical},800,false);}},400);
</script>"""
    components.html(html, height=108, scrolling=False)


def render_score_gauge(food, health, priority, urgency):
    gmap={"Critical":"#ef4444","High":"#f59e0b","Moderate":"#3b82f6","Low":"#22c55e"}
    glw={"Critical":"rgba(239,68,68,0.4)","High":"rgba(245,158,11,0.4)","Moderate":"rgba(59,130,246,0.35)","Low":"rgba(34,197,94,0.3)"}
    c=gmap.get(urgency,"#6b7280"); g=glw.get(urgency,"transparent")
    html = f"""
<style>
*{{box-sizing:border-box;margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;}}
body{{background:transparent;}}
.wrap{{display:flex;align-items:center;gap:22px;padding:4px 0;animation:fi 0.6s ease-out both;}}
@keyframes fi{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:translateY(0)}}}}
.bars{{flex:1;}}.brow{{margin-bottom:14px;}}
.blbl{{display:flex;justify-content:space-between;font-size:13px;color:#6b7280;margin-bottom:5px;}}
.blbl span:last-child{{font-weight:700;color:#111827;}}
.track{{background:#f3f4f6;border-radius:8px;height:10px;overflow:hidden;}}
.fill{{height:100%;border-radius:8px;width:0%;transition:width 1.4s cubic-bezier(0.34,1.56,0.64,1);}}
.f{{background:linear-gradient(90deg,#f97316,#fbbf24);}}.h{{background:linear-gradient(90deg,#8b5cf6,#c084fc);}}
</style>
<div class="wrap">
  <svg width="175" height="120" viewBox="0 0 175 120" style="flex-shrink:0;">
    <defs><filter id="gf"><feGaussianBlur stdDeviation="3"/></filter></defs>
    <path d="M 18 100 A 68 68 0 0 1 157 100" fill="none" stroke="#e5e7eb" stroke-width="14" stroke-linecap="round"/>
    <path d="M 18 100 A 68 68 0 0 1 157 100" fill="none" stroke="{c}" stroke-width="20" stroke-linecap="round"
          stroke-dasharray="0 214" id="ag" opacity="0.25" style="filter:url(#gf);transition:stroke-dasharray 1.5s ease-out;"/>
    <path d="M 18 100 A 68 68 0 0 1 157 100" fill="none" stroke="{c}" stroke-width="13" stroke-linecap="round"
          stroke-dasharray="0 214" id="am" style="transition:stroke-dasharray 1.5s cubic-bezier(0.34,1.2,0.64,1);"/>
    <text id="sn" x="87" y="80" text-anchor="middle" font-size="25" font-weight="800" fill="#111827">0</text>
    <text x="87" y="100" text-anchor="middle" font-size="11" fill="#9ca3af">Priority Score</text>
    <text x="87" y="116" text-anchor="middle" font-size="11" font-weight="700" fill="{c}">{urgency}</text>
  </svg>
  <div class="bars">
    <div class="brow"><div class="blbl"><span>🍽 Food Need</span><span id="fv">0</span></div>
      <div class="track"><div class="fill f" id="bf"></div></div></div>
    <div class="brow"><div class="blbl"><span>🏥 Health Risk</span><span id="hv">0</span></div>
      <div class="track"><div class="fill h" id="bh"></div></div></div>
  </div>
</div>
<script>
const ARC=213.6;
setTimeout(()=>{{
  const fill=({priority}/100)*ARC;
  document.getElementById('am').setAttribute('stroke-dasharray',fill+' '+ARC);
  document.getElementById('ag').setAttribute('stroke-dasharray',fill+' '+ARC);
  const sEl=document.getElementById('sn'),dur=1500,s0=performance.now(),tgt={priority};
  (function t(now){{const p=Math.min((now-s0)/dur,1),e=1-Math.pow(1-p,3);
    sEl.textContent=(e*tgt).toFixed(1);if(p<1)requestAnimationFrame(t);else sEl.textContent=tgt.toFixed(1);}})
  (performance.now());
  document.getElementById('bf').style.width='{food}%';
  document.getElementById('bh').style.width='{health}%';
  [['fv',{food}],['hv',{health}]].forEach(([id,tgt])=>{{
    const el=document.getElementById(id),s1=performance.now();
    (function t(now){{const p=Math.min((now-s1)/1400,1),e=1-Math.pow(1-p,3);
      el.textContent=(e*tgt).toFixed(1);if(p<1)requestAnimationFrame(t);else el.textContent=tgt.toFixed(1);}})
    (performance.now());
  }});
}},280);
</script>"""
    components.html(html, height=145, scrolling=False)

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
  background:linear-gradient(rgba(255,255,255,0.74),rgba(255,255,255,0.84)),
             url("data:image/jpg;base64,{page_bg}");
  background-size:cover;background-position:center;background-attachment:fixed;
}}
.block-container{{padding-top:1rem;padding-bottom:2rem;max-width:1280px;animation:pageFade 0.7s ease-out;}}
section[data-testid="stSidebar"]{{
  background:rgba(255,247,236,0.97);border-right:2px solid rgba(240,190,95,0.45);
  backdrop-filter:blur(10px);animation:sidebarIn 0.6s ease-out both;
}}
@keyframes sidebarIn{{from{{opacity:0;transform:translateX(-18px)}}to{{opacity:1;transform:translateX(0)}}}}
section[data-testid="stSidebar"] *{{color:#111827 !important;}}

div.stButton > button:first-child{{
  background:linear-gradient(135deg,#f59e0b,#f97316) !important;color:white !important;
  border:none !important;border-radius:999px !important;padding:0.9rem 2.3rem !important;
  font-size:1.02rem !important;font-weight:800 !important;
  box-shadow:0 14px 30px rgba(249,115,22,0.28) !important;
  transition:transform 0.25s cubic-bezier(0.34,1.56,0.64,1),box-shadow 0.25s ease !important;
}}
div.stButton > button:first-child:hover{{transform:translateY(-3px) scale(1.04) !important;box-shadow:0 20px 36px rgba(249,115,22,0.36) !important;}}
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
  transform:translateY(-5px);box-shadow:0 18px 32px rgba(0,0,0,0.12);
}}
.pink-box{{background:rgba(255,233,243,0.97);border:2px solid rgba(242,167,200,0.88);animation-delay:.05s;}}
.yellow-box{{background:rgba(255,245,196,0.97);border:2px solid rgba(244,201,93,0.88);animation-delay:.10s;}}
.white-box{{background:rgba(255,255,255,0.98);border:1px solid rgba(220,220,220,0.95);animation-delay:.15s;}}
.green-box{{background:rgba(232,247,236,0.98);border:1px solid rgba(144,196,157,0.95);animation-delay:.20s;}}
.blue-box{{background:rgba(232,244,255,0.98);border:1px solid rgba(147,197,253,0.95);animation-delay:.25s;}}
.chart-card{{background:rgba(255,255,255,0.98);border:1px solid rgba(243,217,164,0.90);animation-delay:.05s;}}
.contact-box{{background:rgba(255,255,255,0.98);border:2px solid rgba(234,215,164,0.92);padding:22px;box-shadow:0 8px 18px rgba(0,0,0,0.08);animation-delay:.10s;}}

.pink-box h3,.yellow-box h3,.white-box h3,.green-box h3,.blue-box h3,.chart-card h3{{color:#111827 !important;font-size:24px !important;margin:0 0 10px 0 !important;font-weight:700 !important;}}
.contact-box h3{{color:#111827 !important;font-size:24px !important;margin:0 0 10px 0 !important;font-weight:800 !important;}}
.pink-box p,.yellow-box p,.white-box p,.green-box p,.blue-box p,.chart-card p,
.pink-box li,.yellow-box li,.white-box li,.green-box li,.blue-box li{{color:#111827 !important;font-size:16px !important;line-height:1.7 !important;margin-bottom:8px !important;}}
.contact-box p{{color:#111827 !important;font-size:16px !important;line-height:1.7 !important;margin-bottom:8px !important;font-weight:700 !important;}}
.pink-box ul,.yellow-box ul,.white-box ul,.green-box ul,.blue-box ul{{margin:8px 0 0 0 !important;padding-left:22px !important;}}

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
.metric-card:hover{{transform:perspective(900px) rotateX(6deg) rotateY(-6deg) translateY(-8px) scale(1.04);box-shadow:0 22px 36px rgba(0,0,0,0.16);}}
.metric-card:active{{transform:scale(0.97);}}
.metric-label{{color:#6b7280 !important;font-size:15px !important;margin-bottom:6px !important;}}
.metric-value{{color:#111827 !important;font-size:28px !important;font-weight:700 !important;line-height:1.2 !important;}}

.urgency-badge{{padding:10px 16px;border-radius:12px;font-weight:700;display:inline-block;margin-top:8px;font-size:15px;}}
.pulse-critical{{animation:pCrit 1.8s cubic-bezier(0.215,0.61,0.355,1) infinite;}}
.pulse-high{{animation:pHigh 2.2s cubic-bezier(0.215,0.61,0.355,1) infinite;}}
.pulse-moderate{{animation:pMod 2.5s cubic-bezier(0.215,0.61,0.355,1) infinite;}}
.pulse-low{{animation:pLow 3s ease-in-out infinite;}}
@keyframes pCrit{{0%,100%{{box-shadow:0 0 0 0 rgba(176,0,32,0.5),0 4px 12px rgba(176,0,32,0.20)}}50%{{box-shadow:0 0 0 10px rgba(176,0,32,0),0 4px 18px rgba(176,0,32,0.30)}}}}
@keyframes pHigh{{0%,100%{{box-shadow:0 0 0 0 rgba(180,83,9,0.4),0 4px 10px rgba(180,83,9,0.15)}}50%{{box-shadow:0 0 0 8px rgba(180,83,9,0),0 4px 16px rgba(180,83,9,0.22)}}}}
@keyframes pMod{{0%,100%{{box-shadow:0 0 0 0 rgba(29,78,216,0.35)}}50%{{box-shadow:0 0 0 7px rgba(29,78,216,0)}}}}
@keyframes pLow{{0%,100%{{box-shadow:0 0 0 0 rgba(21,128,61,0.25)}}50%{{box-shadow:0 0 0 6px rgba(21,128,61,0)}}}}

.action-card-yellow,.action-card-pink,.action-card-orange{{
  border-radius:22px;padding:18px;min-height:180px;box-shadow:0 6px 14px rgba(0,0,0,0.05);
  animation:slideUp 0.6s ease-out both;transition:transform 0.3s cubic-bezier(0.34,1.56,0.64,1),box-shadow 0.3s ease;
  position:relative;overflow:hidden;
}}
.action-card-yellow::after,.action-card-pink::after,.action-card-orange::after{{
  content:"";position:absolute;inset:auto -30% -80% auto;width:180px;height:180px;
  border-radius:50%;background:rgba(255,255,255,0.18);filter:blur(8px);pointer-events:none;
}}
.action-card-yellow:hover,.action-card-pink:hover,.action-card-orange:hover{{transform:translateY(-8px) scale(1.02);box-shadow:0 18px 32px rgba(0,0,0,0.12);}}
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

/* View mode banner */
.view-banner{{padding:10px 16px;border-radius:12px;margin-bottom:14px;font-size:14px;font-weight:600;animation:fadeInSoft 0.5s ease-out;}}
.v-analyst{{background:#eff6ff;border:1px solid #bfdbfe;color:#1e40af;}}
.v-fundraiser{{background:#fef3c7;border:1px solid #fcd34d;color:#92400e;}}
.v-policy{{background:#f0fdf4;border:1px solid #86efac;color:#166534;}}

/* Data source rows in sidebar */
.src-row{{padding:9px 0;border-bottom:1px solid rgba(0,0,0,0.06);}}
.src-row:last-child{{border-bottom:none;}}
.src-name{{font-weight:700;font-size:13px;color:#111827 !important;}}
.src-what{{font-size:12px;color:#4b5563 !important;margin:2px 0;}}
.src-freq{{font-size:11px;color:#9ca3af !important;}}

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
.stSelectbox div[data-baseweb="select"] span,.stSelectbox div[data-baseweb="select"] input,.stSelectbox div[data-baseweb="select"] svg{{color:#111827 !important;fill:#111827 !important;opacity:1 !important;}}
div[data-baseweb="popover"] *{{color:#111827 !important;}}
div[data-baseweb="popover"] ul,div[data-baseweb="popover"] li,div[data-baseweb="popover"] div[role="option"]{{background:#fff !important;color:#111827 !important;}}
div[data-baseweb="popover"] div[aria-selected="true"]{{background:#fef3c7 !important;color:#111827 !important;}}
div[data-baseweb="popover"] div[role="option"]:hover{{background:#fff7dd !important;}}

.stExpander{{background:rgba(255,255,255,0.88) !important;border-radius:18px !important;
  border:1px solid rgba(226,232,240,0.95) !important;margin-bottom:12px !important;
  overflow:hidden !important;box-shadow:0 8px 18px rgba(0,0,0,0.04) !important;
  transition:box-shadow 0.3s ease !important;}}
.stExpander:hover{{box-shadow:0 12px 24px rgba(0,0,0,0.08) !important;}}
.stExpander summary{{font-weight:800 !important;color:#111827 !important;font-size:17px !important;}}

@keyframes pageFade{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes fadeInSoft{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes slideUp{{from{{opacity:0;transform:translateY(22px) scale(0.96)}}to{{opacity:1;transform:translateY(0) scale(1)}}}}
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
if "view_mode" not in st.session_state: st.session_state.view_mode = "Analyst"

# ============================================================
# Landing page  — same as original, now animated
# ============================================================
if not st.session_state.started:
    render_hero_animated(header_banner)
    _, col_c, _ = st.columns([1,1,1])
    with col_c:
        if st.button("🌽  Let's Start", use_container_width=True):
            st.session_state.started = True
            st.session_state.page = "menu"
            st.rerun()

# ============================================================
# Menu page  — same as original, now animated banner
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
# About page  — same content, now animated banner + updated scores section
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
            <p><strong>Food Need Score</strong> — derived from county-level food insecurity rates published by <a href="https://map.feedingamerica.org/" target="_blank" style="color:#f59e0b;font-weight:700;">Feeding America's Map the Meal Gap</a> (annual data, ~2-year reporting lag). The US food insecurity rate was 14.3% in 2023.</p>
            <p><strong>Health Risk Score</strong> — based on poverty rates, unemployment, and socioeconomic indicators from the US Census Bureau ACS 5-Year Estimates.</p>
            <p><strong>Final Priority Score</strong> — combines both scores (0–100 scale) to rank counties by overall relative need.</p>
            <ul>
                <li>Score ≥ 70 → <strong>Critical</strong></li>
                <li>Score 55–69 → <strong>High</strong></li>
                <li>Score 40–54 → <strong>Moderate</strong></li>
                <li>Score &lt; 40 → <strong>Low</strong></li>
            </ul>
            <p><strong>People-level figures</strong> (est. people food insecure, food shelf visits, SNAP) are model estimates based on county populations (2020 Census) and statewide rates from the Second Harvest Heartland 2024 Statewide Hunger Study. These are approximations for planning purposes — not official counts.</p>
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
            <p>Share interest in donating funds, resources, or food support for higher-need Minnesota counties.</p>
        </div>""", unsafe_allow_html=True)
        st.link_button("Open Donation Form", SUPPORT_FORM_URL, use_container_width=True)
    with a2:
        st.markdown("""<div class="action-card-pink"><h3>Become a sponsor</h3>
            <p>Organizations and businesses can express interest in sponsoring county-level food support efforts.</p>
        </div>""", unsafe_allow_html=True)
        st.link_button("Open Sponsorship Form", SUPPORT_FORM_URL, use_container_width=True)
    with a3:
        st.markdown("""<div class="action-card-orange"><h3>Partner organization</h3>
            <p>Nonprofits and community organizations can connect to discuss outreach, planning, and collaboration.</p>
        </div>""", unsafe_allow_html=True)
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
# Dashboard page  — same layout + animations + feedback layer
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

    # ── Sidebar ──
    st.sidebar.markdown("## Filters")
    st.sidebar.markdown("Choose an urgency level to focus the county ranking.")
    urgency_options = ["All"] + sorted(df["Urgency Level"].unique().tolist())
    selected_urgency = st.sidebar.selectbox("Urgency Level", urgency_options)

    filtered_df = df[df["Urgency Level"] == selected_urgency].copy() if selected_urgency != "All" else df.copy()
    filtered_df = filtered_df.sort_values(priority_col, ascending=False).reset_index(drop=True)

    st.sidebar.markdown("Select one county to review details.")
    county_list = filtered_df[county_col].tolist()
    selected_county = st.sidebar.selectbox("Select County", county_list)

    # ── View Mode ──
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👁️ View Mode")
    view_mode = st.sidebar.radio(
        "Choose your lens",
        ["Analyst", "Fundraiser / Grants", "Policy Maker"],
        index=["Analyst","Fundraiser / Grants","Policy Maker"].index(st.session_state.view_mode)
              if st.session_state.view_mode in ["Analyst","Fundraiser / Grants","Policy Maker"] else 0,
        help="Analyst: scores & rates | Fundraiser: people & scale | Policy: coverage gaps",
    )
    st.session_state.view_mode = view_mode

    # ── Data Sources ──
    st.sidebar.markdown("---")
    with st.sidebar.expander("📚 Data Sources"):
        for src in DATA_SOURCES:
            st.markdown(f"""<div class="src-row">
<div class="src-name">{src['emoji']} {src['name']}</div>
<div class="src-what">{src['what']}</div>
<div class="src-freq">🕐 {src['frequency']} · Used for: {src['used_for']}</div>
<a href="{src['url']}" target="_blank" style="font-size:12px;color:#f59e0b;font-weight:600;">→ View source</a>
</div>""", unsafe_allow_html=True)
        st.markdown("""<div style="margin-top:8px;font-size:11px;color:#9ca3af;">
⚠️ People-level figures are model estimates based on county populations (2020 Census) and statewide food insecurity rates.</div>""",
            unsafe_allow_html=True)

    # ── MN 2024 Context ──
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 MN 2024 Context")
    st.sidebar.markdown("""<div style="font-size:13px;line-height:1.7;color:#374151;">
🔺 <b>18.4%</b> avg increase in food shelf visits in 2024<br>
👥 <b>1 in 5</b> MN households food insecure<br>
🏪 <b>487</b> TEFAP food shelves statewide<br>
📊 <b>14.3%</b> US food insecurity rate (2023)<br>
<i style="font-size:11px;color:#9ca3af;">Sources: Feeding America, The Food Group, Second Harvest Heartland</i>
</div>""", unsafe_allow_html=True)

    # ── Dashboard body ──
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

    # View mode banner
    if view_mode == "Analyst":
        st.markdown('<div class="view-banner v-analyst">📐 <b>Analyst view</b> — showing priority scores and rates.</div>', unsafe_allow_html=True)
    elif view_mode == "Fundraiser / Grants":
        st.markdown('<div class="view-banner v-fundraiser">💰 <b>Fundraiser / Grants view</b> — showing estimated people affected and food shelf visit scale. Ideal for grant writing.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="view-banner v-policy">🏛️ <b>Policy Maker view</b> — showing coverage gaps where need may outpace service capacity.</div>', unsafe_allow_html=True)

    st.markdown('<div class="content-wrap">', unsafe_allow_html=True)

    if filtered_df.empty:
        st.markdown("""<div class="pink-box"><h3>No counties available</h3>
            <p>No counties match the selected urgency level.</p></div>""", unsafe_allow_html=True)
    else:
        # Animated count-up metric cards
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
            st.markdown('<div class="section-caption">Map colors change with urgency level. The selected county is highlighted with a black border. Hover to see population and people food insecure.</div>', unsafe_allow_html=True)

            fig = build_map(df, filtered_df, selected_county, selected_urgency)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown('<h3 style="color:#111827;margin-bottom:6px;">Selected County Detail</h3>', unsafe_allow_html=True)
            st.markdown(urgency_badge(county_data["Urgency Level"]), unsafe_allow_html=True)
            st.markdown(coverage_gap_badge(gap_ratio, median_gap), unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            # Animated score gauge (replaces 3 static metric cards)
            render_score_gauge(
                float(county_data[food_col]),
                float(county_data[health_col]),
                float(county_data[priority_col]),
                county_data["Urgency Level"],
            )
            st.markdown(metric_card("County", str(county_data[county_col])), unsafe_allow_html=True)

            # View-mode specific people cards
            if view_mode == "Fundraiser / Grants":
                st.markdown(f"""<div class="yellow-box" style="margin-top:10px;">
<h3 style="font-size:18px;">👥 People & Scale</h3>
<p><b>~{fmt_num(est_fi)}</b> people food insecure ({fi_rate:.1f}% of {fmt_num(pop)})</p>
<p><b>~{fmt_num(est_visits)}</b> est. food shelf visits/year</p>
<p><b>~{fmt_num(est_snap)}</b> est. SNAP enrollees</p>
<p style="font-size:12px;color:#9ca3af;margin-top:6px;">Model estimates — cite primary sources in formal documents.</p>
</div>""", unsafe_allow_html=True)
            elif view_mode == "Policy Maker":
                gap_label = "High" if gap_ratio > median_gap * 1.3 else "Moderate" if gap_ratio > median_gap * 0.8 else "Lower"
                st.markdown(f"""<div class="green-box" style="margin-top:10px;">
<h3 style="font-size:18px;">🏛️ Coverage Gap</h3>
<p><b>{gap_ratio:,}</b> people per est. food shelter</p>
<p>Statewide median: <b>{int(median_gap):,}</b></p>
<p>Gap level: <b>{gap_label}</b></p>
<p style="font-size:12px;color:#9ca3af;margin-top:6px;">Shelter count is a proxy — contact MN DCYF for actual TEFAP site data.</p>
</div>""", unsafe_allow_html=True)

            st.markdown('<p class="mini-note" style="margin-top:8px;">Use this panel to review the selected county before making outreach or support decisions.</p>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # All county ranking + CSV download
        st.markdown('<div class="green-box">', unsafe_allow_html=True)
        col_title, col_dl = st.columns([3,1])
        with col_title:
            st.markdown('<h3 style="color:#111827;margin-bottom:6px;">All County Ranking</h3>', unsafe_allow_html=True)
            st.markdown('<div class="section-caption">Counties ranked by Final Priority Score in the current view.</div>', unsafe_allow_html=True)
        with col_dl:
            export_cols = [county_col, "Urgency Level", food_col, health_col, priority_col,
                           "Population","Est. People Food Insecure","Est. Food Insecurity Rate (%)",
                           "Est. Food Shelf Visits 2024","Est. SNAP Enrollment","Coverage Gap (people/shelter)"]
            csv_buf = io.BytesIO()
            filtered_df[export_cols].to_csv(csv_buf, index=False)
            st.download_button("⬇️ Download CSV", data=csv_buf.getvalue(),
                               file_name="carelio_mn_data.csv", mime="text/csv")

        display_df = filtered_df[[county_col, food_col, health_col, priority_col, "Urgency Level"]].copy()
        display_df.index = range(1, len(display_df) + 1)
        st.dataframe(display_df, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Insight boxes — same as original
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
        st.markdown("""<div style="margin-top:14px;padding:12px 16px;background:rgba(255,255,255,0.7);
border-radius:12px;border:1px solid rgba(220,220,220,0.8);">
<p style="font-size:12px;color:#6b7280;margin:0;">
<b>Data sources:</b>
Food Need Score — <a href="https://map.feedingamerica.org/" target="_blank" style="color:#f59e0b;">Feeding America Map the Meal Gap</a> (annual, ~2yr lag) ·
Health Risk Score — US Census ACS 5-Year Estimates ·
Population — US Census 2020 ·
People estimates — model based on <a href="https://www.2harvest.org/about-us/make-hunger-history" target="_blank" style="color:#f59e0b;">Second Harvest Heartland 2024 Statewide Hunger Study</a> ·
Food shelf visits context — <a href="https://www.thefoodgroupmn.org" target="_blank" style="color:#f59e0b;">The Food Group + MN DCYF 2024 Report</a> ·
SNAP context — <a href="https://dcyf.mn.gov/snap-food-assistance-minnesota" target="_blank" style="color:#f59e0b;">MN DCYF SNAP County Statistics</a>
</p></div>""", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
