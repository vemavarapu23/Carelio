import base64
import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(
    page_title="Carelio | Minnesota Food Support Prioritization",
    page_icon="🍎",
    layout="wide"
)
st.title("Carelio")

st.markdown("""
Carelio is a Minnesota food support prioritization website built using public data.
It highlights counties that may need more attention for food support planning and outreach.
""")
# -----------------------------
# Links
# -----------------------------
SUPPORT_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfbSl0GJBjDDwKk2aMnV_-EHehBS6BmJjRyES5pE6lPMp92pQ/viewform?usp=publish-editor"
EMAIL_ADDRESS = "sruthivemavarapus@outlook.com"
LINKEDIN_URL = "https://www.linkedin.com/in/sruthi-vemavarapu-0b614b198"
GITHUB_URL = "https://github.com/vemavarapu23/Carelio"
LIVE_URL = "https://carelio-mn.streamlit.app/"

# -----------------------------
# Helpers
# -----------------------------
def get_base64_image(image_path: str) -> str:
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

@st.cache_data
def load_data():
    df = pd.read_csv("mn_food_access_data.csv")
    df.columns = [col.strip() for col in df.columns]
    return df

def urgency_label(score):
    if score >= 70:
        return "Critical"
    elif score >= 55:
        return "High"
    elif score >= 40:
        return "Moderate"
    return "Low"

def urgency_badge(urgency: str) -> str:
    styles = {
        "Critical": ("#ffe3e3", "#b00020"),
        "High": ("#fff1d6", "#b45309"),
        "Moderate": ("#dbeafe", "#1d4ed8"),
        "Low": ("#dcfce7", "#15803d"),
    }
    bg, fg = styles.get(urgency, ("#f3f4f6", "#111827"))
    return f"""
    <div class="urgency-badge badge-pop" style="background:{bg}; color:{fg};">
        Urgency Level: {urgency}
    </div>
    """

def metric_card(label: str, value: str) -> str:
    return f"""
    <div class="metric-card glass-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
    </div>
    """

def explain_score(score):
    if score >= 70:
        return "High priority — this county shows relatively higher food and health vulnerability compared with others in the dataset."
    elif score >= 55:
        return "Moderate-high priority — this county may deserve targeted review and stronger support attention."
    elif score >= 40:
        return "Moderate priority — some level of need is present and may benefit from additional review."
    return "Lower priority — comparatively lower need based on the current dataset."

def why_county_ranked(food_score, health_score, priority_score, urgency):
    if urgency == "Critical":
        title = "Why this county is critical"
        if food_score >= 70 and health_score >= 70:
            text = "This county is critical because both food need and health risk are very high compared with many other counties in the dataset. Since both indicators are strongly elevated, the final priority score also becomes very high."
        elif food_score >= 70:
            text = "This county is critical mainly because food need is especially high. That strong food access concern pushes the county into the highest urgency group."
        elif health_score >= 70:
            text = "This county is critical mainly because health risk is especially high. That added vulnerability raises the county into the highest urgency level."
        else:
            text = "This county is critical because the combined effect of food need and health risk produces one of the strongest priority signals in the dataset."

    elif urgency == "High":
        title = "Why this county is high"
        if food_score >= 55 and health_score >= 55:
            text = "This county is high because both food need and health risk are elevated. While not at the most extreme level, the combined scores still show strong need compared with many counties."
        elif food_score >= 55:
            text = "This county is high mainly because food need is elevated and contributes strongly to the final priority score."
        elif health_score >= 55:
            text = "This county is high mainly because health risk is elevated and increases the county’s overall vulnerability."
        else:
            text = "This county is high because its combined score remains above many other counties in the dataset."

    elif urgency == "Moderate":
        title = "Why this county is moderate"
        if food_score >= 40 and health_score >= 40:
            text = "This county is moderate because both food need and health risk are in the middle range. The county shows noticeable need, but not at the level of the higher-priority counties."
        elif food_score >= 40:
            text = "This county is moderate mainly because food need shows some concern, but the total combined risk is not high enough to place it in a higher urgency group."
        elif health_score >= 40:
            text = "This county is moderate mainly because health risk shows some concern, but the overall combined score stays in the middle range."
        else:
            text = "This county is moderate because the combined result of the indicators falls in the middle range compared with the rest of the dataset."

    else:
        title = "Why this county is low"
        if food_score < 40 and health_score < 40:
            text = "This county is low because both food need and health risk are comparatively lower than counties with greater concern. Since both indicators are lower, the final priority score is also lower."
        elif food_score < 40:
            text = "This county is low because food need is comparatively lower, which keeps the overall priority level lower."
        elif health_score < 40:
            text = "This county is low because health risk is comparatively lower, which keeps the county in the low urgency group."
        else:
            text = "This county is low because the combined score is lower than many other counties in the dataset."

    return title, text

# -----------------------------
# Images
# -----------------------------
header_banner = get_base64_image("header_banner.avif")
page_bg = get_base64_image("page_bg.jpg")

# -----------------------------
# CSS
# -----------------------------
st.markdown(
    f"""
<style>
    html {{
        scroll-behavior: smooth;
    }}

    .stApp {{
        background:
            linear-gradient(rgba(255,255,255,0.74), rgba(255,255,255,0.84)),
            url("data:image/jpg;base64,{page_bg}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    .block-container {{
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1280px;
        animation: pageFade 0.8s ease-out;
    }}

    section[data-testid="stSidebar"] {{
        background: rgba(255, 247, 236, 0.97);
        border-right: 2px solid rgba(240, 190, 95, 0.45);
        backdrop-filter: blur(10px);
    }}

    section[data-testid="stSidebar"] * {{
        color: #111827 !important;
    }}

    .hero-screen {{
        position: relative;
        min-height: 78vh;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 28px;
        border-radius: 34px;
        overflow: hidden;
        background:
            linear-gradient(rgba(0,0,0,0.40), rgba(0,0,0,0.54)),
            url("data:image/avif;base64,{header_banner}");
        background-size: cover;
        background-position: center;
        box-shadow: 0 24px 50px rgba(0,0,0,0.20);
        animation: heroRise 1s ease-out;
    }}

    .hero-screen::before {{
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(120deg, rgba(255,255,255,0.08), rgba(255,255,255,0.00), rgba(255,255,255,0.10));
        animation: shimmer 8s linear infinite;
        pointer-events: none;
    }}

    .hero-inner {{
        position: relative;
        z-index: 2;
        max-width: 960px;
        animation: fadeInSoft 1s ease-out;
    }}

    .hero-title {{
        color: #ffffff !important;
        font-size: 100px !important;
        font-weight: 900 !important;
        letter-spacing: 0.8px !important;
        margin-bottom: 10px !important;
        animation: softPulse 4s ease-in-out infinite;
        text-shadow: 0 8px 24px rgba(0,0,0,0.25);
    }}

    .hero-subtitle {{
        color: #fffaf2 !important;
        font-size: 31px !important;
        font-weight: 800 !important;
        line-height: 1.4 !important;
        margin-bottom: 12px !important;
    }}

    .hero-bold {{
        color: #ffffff !important;
        font-size: 22px !important;
        font-weight: 800 !important;
        margin-top: 8px !important;
        margin-bottom: 18px !important;
    }}

    .hero-small {{
        color: #fffaf5 !important;
        font-size: 18px !important;
        line-height: 1.8 !important;
        max-width: 780px;
        margin: 0 auto 28px auto !important;
    }}

    .section-hero {{
        position: relative;
        overflow: hidden;
        background:
            linear-gradient(rgba(0,0,0,0.42), rgba(0,0,0,0.50)),
            url("data:image/avif;base64,{header_banner}");
        background-size: cover;
        background-position: center;
        border-radius: 30px;
        min-height: 235px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 34px;
        margin-bottom: 18px;
        box-shadow: 0 16px 36px rgba(0,0,0,0.18);
        animation: heroRise 0.9s ease-out;
    }}

    .section-hero::before {{
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(120deg, rgba(255,255,255,0.06), rgba(255,255,255,0.00), rgba(255,255,255,0.08));
        animation: shimmer 8s linear infinite;
        pointer-events: none;
    }}

    .section-hero-inner {{
        position: relative;
        z-index: 2;
    }}

    .section-hero h1 {{
        color: white !important;
        font-size: 68px !important;
        margin: 0 0 8px 0 !important;
        font-weight: 900 !important;
        letter-spacing: 0.5px !important;
        animation: softPulse 3.8s ease-in-out infinite;
    }}

    .section-hero .tagline {{
        color: #fffaf2 !important;
        font-size: 22px !important;
        margin: 6px 0 !important;
        font-weight: 700 !important;
        line-height: 1.4 !important;
    }}

    .section-hero .subnote {{
        color: #fff8ef !important;
        font-size: 17px !important;
        margin: 12px 0 0 0 !important;
        line-height: 1.65 !important;
        font-weight: 500 !important;
    }}

    div.stButton > button:first-child {{
        background: linear-gradient(135deg, #f59e0b, #f97316) !important;
        color: white !important;
        border: none !important;
        border-radius: 999px !important;
        padding: 0.9rem 2.3rem !important;
        font-size: 1.02rem !important;
        font-weight: 800 !important;
        box-shadow: 0 14px 30px rgba(249, 115, 22, 0.28) !important;
        transition: transform 0.25s ease, box-shadow 0.25s ease !important;
    }}

    div.stButton > button:first-child:hover {{
        transform: translateY(-3px) scale(1.03) !important;
        box-shadow: 0 18px 34px rgba(249, 115, 22, 0.34) !important;
    }}

    div.stButton > button:first-child:active {{
        animation: clickPop 0.22s ease;
    }}

    .content-wrap {{
        background: rgba(255,255,255,0.72);
        border-radius: 30px;
        padding: 24px;
        backdrop-filter: blur(9px);
        box-shadow: 0 12px 28px rgba(0,0,0,0.08);
        animation: fadeInSoft 0.8s ease-out;
    }}

    .glass-card {{
        backdrop-filter: blur(6px);
    }}

    .pink-box, .yellow-box, .white-box, .green-box, .blue-box, .contact-box, .chart-card {{
        border-radius: 22px;
        padding: 20px;
        margin-bottom: 18px;
        box-shadow: 0 6px 14px rgba(0,0,0,0.06);
        color: #111827 !important;
        animation: fadeInSoft 0.75s ease-out;
        transition: transform 0.28s ease, box-shadow 0.28s ease;
    }}

    .pink-box:hover, .yellow-box:hover, .white-box:hover, .green-box:hover, .blue-box:hover,
    .contact-box:hover, .chart-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 14px 28px rgba(0,0,0,0.10);
    }}

    .pink-box {{
        background: rgba(255, 233, 243, 0.97);
        border: 2px solid rgba(242, 167, 200, 0.88);
    }}

    .yellow-box {{
        background: rgba(255, 245, 196, 0.97);
        border: 2px solid rgba(244, 201, 93, 0.88);
    }}

    .white-box {{
        background: rgba(255,255,255,0.98);
        border: 1px solid rgba(220, 220, 220, 0.95);
    }}

    .green-box {{
        background: rgba(232, 247, 236, 0.98);
        border: 1px solid rgba(144, 196, 157, 0.95);
    }}

    .blue-box {{
        background: rgba(232, 244, 255, 0.98);
        border: 1px solid rgba(147, 197, 253, 0.95);
    }}

    .chart-card {{
        background: rgba(255,255,255,0.98);
        border: 1px solid rgba(243, 217, 164, 0.90);
    }}

    .contact-box {{
        background: rgba(255,255,255,0.98);
        border: 2px solid rgba(234, 215, 164, 0.92);
        padding: 22px;
        box-shadow: 0 8px 18px rgba(0,0,0,0.08);
    }}

    .pink-box h3, .yellow-box h3, .white-box h3, .green-box h3, .blue-box h3, .chart-card h3 {{
        color: #111827 !important;
        font-size: 24px !important;
        margin: 0 0 10px 0 !important;
        font-weight: 700 !important;
    }}

    .contact-box h3 {{
        color: #111827 !important;
        font-size: 24px !important;
        margin: 0 0 10px 0 !important;
        font-weight: 800 !important;
    }}

    .pink-box p, .yellow-box p, .white-box p, .green-box p, .blue-box p, .chart-card p,
    .pink-box li, .yellow-box li, .white-box li, .green-box li, .blue-box li {{
        color: #111827 !important;
        font-size: 16px !important;
        line-height: 1.7 !important;
        margin-bottom: 8px !important;
    }}

    .contact-box p {{
        color: #111827 !important;
        font-size: 16px !important;
        line-height: 1.7 !important;
        margin-bottom: 8px !important;
        font-weight: 700 !important;
    }}

    .pink-box ul, .yellow-box ul, .white-box ul, .green-box ul, .blue-box ul {{
        margin: 8px 0 0 0 !important;
        padding-left: 22px !important;
    }}

    .metric-card {{
        background: linear-gradient(135deg, rgba(255,255,255,0.99), rgba(255,249,242,0.98));
        border: 1px solid rgba(243, 217, 164, 0.92);
        padding: 18px;
        border-radius: 18px;
        box-shadow: 0 6px 14px rgba(255, 138, 0, 0.10);
        margin-bottom: 8px;
        animation: fadeInSoft 0.7s ease-out;
        transition: transform 0.35s ease, box-shadow 0.35s ease;
        transform-style: preserve-3d;
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }}

    .metric-card::before {{
        content: "";
        position: absolute;
        top: 0;
        left: -120%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.35), transparent);
        animation: shine 4.8s infinite;
    }}

    .metric-card:hover {{
        transform: perspective(900px) rotateX(6deg) rotateY(-6deg) translateY(-8px) scale(1.03);
        box-shadow: 0 20px 34px rgba(0,0,0,0.15);
    }}

    .metric-card:active {{
        animation: clickPop 0.2s ease;
    }}

    .metric-label {{
        color: #6b7280 !important;
        font-size: 15px !important;
        margin-bottom: 6px !important;
    }}

    .metric-value {{
        color: #111827 !important;
        font-size: 28px !important;
        font-weight: 700 !important;
        line-height: 1.2 !important;
    }}

    .action-card-yellow, .action-card-pink, .action-card-orange {{
        border-radius: 22px;
        padding: 18px;
        min-height: 180px;
        box-shadow: 0 6px 14px rgba(0,0,0,0.05);
        animation: fadeInSoft 0.8s ease-out;
        transition: transform 0.28s ease, box-shadow 0.28s ease;
        position: relative;
        overflow: hidden;
    }}

    .action-card-yellow::after, .action-card-pink::after, .action-card-orange::after {{
        content: "";
        position: absolute;
        inset: auto -30% -80% auto;
        width: 180px;
        height: 180px;
        border-radius: 50%;
        background: rgba(255,255,255,0.18);
        filter: blur(8px);
        pointer-events: none;
    }}

    .action-card-yellow:hover, .action-card-pink:hover, .action-card-orange:hover {{
        transform: translateY(-6px) scale(1.01);
        box-shadow: 0 14px 28px rgba(0,0,0,0.10);
    }}

    .action-card-yellow {{
        background: linear-gradient(135deg, rgba(255, 247, 196, 0.98), rgba(255, 238, 172, 0.94));
        border: 1px solid rgba(244, 201, 93, 0.95);
    }}

    .action-card-pink {{
        background: linear-gradient(135deg, rgba(255, 236, 245, 0.98), rgba(255, 220, 238, 0.94));
        border: 1px solid rgba(242, 167, 200, 0.95);
    }}

    .action-card-orange {{
        background: linear-gradient(135deg, rgba(255, 238, 220, 0.98), rgba(255, 224, 187, 0.94));
        border: 1px solid rgba(245, 158, 11, 0.95);
    }}

    .action-card-yellow h3,
    .action-card-pink h3,
    .action-card-orange h3 {{
        color: #5b21b6 !important;
        font-size: 22px !important;
        margin: 0 0 8px 0 !important;
    }}

    .action-card-yellow p,
    .action-card-pink p,
    .action-card-orange p {{
        color: #111827 !important;
        font-size: 16px !important;
        line-height: 1.6 !important;
        margin: 0 !important;
    }}

    .section-caption {{
        color: #4b5563 !important;
        font-size: 15px !important;
        margin-top: -2px !important;
        margin-bottom: 10px !important;
    }}

    .mini-note {{
        color: #111827 !important;
        font-size: 15px !important;
        line-height: 1.65 !important;
    }}

    .footer-note {{
        font-size: 13px !important;
        color: #111827 !important;
        font-weight: 700 !important;
        line-height: 1.7 !important;
        animation: fadeInSoft 0.9s ease-out;
    }}

    .contact-name {{
        color: #111827 !important;
        font-size: 16px !important;
        font-weight: 800 !important;
        margin-bottom: 12px !important;
    }}

    .contact-icon-card {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        padding: 12px 16px;
        border-radius: 16px;
        background: rgba(255,255,255,0.98);
        border: 1px solid rgba(226, 232, 240, 0.95);
        text-decoration: none !important;
        transition: transform 0.24s ease, box-shadow 0.24s ease;
        box-shadow: 0 6px 14px rgba(0,0,0,0.05);
        animation: popIn 0.5s ease-out;
    }}

    .contact-icon-card:hover {{
        transform: translateY(-4px) scale(1.04);
        box-shadow: 0 12px 22px rgba(0,0,0,0.10);
    }}

    .contact-icon {{
        font-size: 22px;
        line-height: 1;
    }}

    .contact-icon-label {{
        color: #111827 !important;
        font-size: 15px !important;
        font-weight: 800 !important;
    }}

    .urgency-badge {{
        padding: 10px 14px;
        border-radius: 12px;
        font-weight: 700;
        display: inline-block;
        margin-top: 8px;
    }}

    .stExpander {{
        background: rgba(255,255,255,0.88) !important;
        border-radius: 18px !important;
        border: 1px solid rgba(226, 232, 240, 0.95) !important;
        margin-bottom: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 8px 18px rgba(0,0,0,0.04) !important;
    }}

    .stExpander details {{
        background: transparent !important;
    }}

    .stExpander summary {{
        font-weight: 800 !important;
        color: #111827 !important;
        font-size: 17px !important;
    }}

    .stSelectbox label,
    .stMultiSelect label {{
        color: #111827 !important;
        font-weight: 600 !important;
    }}

    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {{
        background: rgba(255,255,255,0.995) !important;
        color: #111827 !important;
        border-radius: 14px !important;
        border: 1px solid rgba(244, 201, 93, 0.95) !important;
        min-height: 48px !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.04) !important;
        transition: all 0.25s ease !important;
    }}

    .stSelectbox div[data-baseweb="select"] > div:hover,
    .stMultiSelect div[data-baseweb="select"] > div:hover {{
        border: 1px solid rgba(245, 158, 11, 0.95) !important;
        box-shadow: 0 8px 18px rgba(245, 158, 11, 0.12) !important;
    }}

    .stSelectbox div[data-baseweb="select"] span,
    .stSelectbox div[data-baseweb="select"] input,
    .stSelectbox div[data-baseweb="select"] svg,
    .stMultiSelect div[data-baseweb="select"] span,
    .stMultiSelect div[data-baseweb="select"] input,
    .stMultiSelect div[data-baseweb="select"] svg {{
        color: #111827 !important;
        fill: #111827 !important;
        opacity: 1 !important;
    }}

    div[data-baseweb="popover"] * {{
        color: #111827 !important;
    }}

    div[data-baseweb="popover"] ul,
    div[data-baseweb="popover"] li,
    div[data-baseweb="popover"] div[role="option"] {{
        background: #ffffff !important;
        color: #111827 !important;
    }}

    div[data-baseweb="popover"] div[aria-selected="true"] {{
        background: #fef3c7 !important;
        color: #111827 !important;
    }}

    div[data-baseweb="popover"] div[role="option"]:hover {{
        background: #fff7dd !important;
    }}

    @keyframes pageFade {{
        from {{ opacity: 0; }}
        to {{ opacity: 1; }}
    }}

    @keyframes fadeInSoft {{
        from {{
            opacity: 0;
            transform: translateY(14px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}

    @keyframes popIn {{
        0% {{
            opacity: 0;
            transform: scale(0.92);
        }}
        60% {{
            opacity: 1;
            transform: scale(1.05);
        }}
        100% {{
            opacity: 1;
            transform: scale(1);
        }}
    }}

    @keyframes clickPop {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(0.96); }}
        100% {{ transform: scale(1); }}
    }}

    @keyframes heroRise {{
        0% {{
            opacity: 0;
            transform: translateY(28px) scale(0.98);
        }}
        100% {{
            opacity: 1;
            transform: translateY(0) scale(1);
        }}
    }}

    @keyframes softPulse {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(1.025); }}
        100% {{ transform: scale(1); }}
    }}

    @keyframes shimmer {{
        0% {{ transform: translateX(-40%); }}
        100% {{ transform: translateX(40%); }}
    }}

    @keyframes shine {{
        0% {{ left: -120%; }}
        30% {{ left: 120%; }}
        100% {{ left: 120%; }}
    }}

    .badge-pop {{
        animation: popIn 0.45s ease-out;
    }}
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# Data
# -----------------------------
df = load_data()
county_col = "County"
food_col = "Food Need Score"
health_col = "Health Risk Score"
priority_col = "Final Priority Score"

for col in [food_col, health_col, priority_col]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=[county_col, food_col, health_col, priority_col]).copy()
df["Urgency Level"] = df[priority_col].apply(urgency_label)
df = df.sort_values(priority_col, ascending=False).reset_index(drop=True)

# -----------------------------
# Session state
# -----------------------------
if "started" not in st.session_state:
    st.session_state.started = False
if "page" not in st.session_state:
    st.session_state.page = "menu"

# -----------------------------
# Landing page
# -----------------------------
if not st.session_state.started:
    st.markdown(
        """
        <div class="hero-screen">
            <div class="hero-inner">
                <div class="hero-title">Carelio</div>
                <div class="hero-subtitle">Minnesota food support prioritization website</div>
                <div class="hero-bold">See which counties may need food support attention most.</div>
                <div class="hero-small">
                    Explore county rankings, compare urgency levels, and review an interactive experience
                    built to support sponsors, nonprofits, and community organizations across Minnesota.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Let's Start"):
        st.session_state.started = True
        st.session_state.page = "menu"
        st.rerun()

# -----------------------------
# Menu page
# -----------------------------
elif st.session_state.page == "menu":
    st.markdown(
        """
        <div class="section-hero">
            <div class="section-hero-inner">
                <h1>Welcome to Carelio</h1>
                <p class="tagline">Choose how you want to explore the project</p>
                <p class="subnote">Open the dashboard for practical county analysis or open About Me to understand the story, purpose, scoring, and support options.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("⌂ Home", use_container_width=True):
            st.session_state.started = False
            st.session_state.page = "menu"
            st.rerun()

    with col2:
        if st.button("Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()

    with col3:
        if st.button("About Me", use_container_width=True):
            st.session_state.page = "about"
            st.rerun()

# -----------------------------
# About page
# -----------------------------
elif st.session_state.page == "about":
    st.markdown(
        """
        <div class="section-hero">
            <div class="section-hero-inner">
                <h1>About Carelio</h1>
                <p class="tagline">Why it was created and how the scores should be understood</p>
                <p class="subnote">A practical tool built to help identify where food support may deserve closer attention across Minnesota.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav1, nav2, nav3 = st.columns(3)
    with nav1:
        if st.button("← Back", use_container_width=True):
            st.session_state.page = "menu"
            st.rerun()
    with nav2:
        if st.button("⌂ Home", use_container_width=True):
            st.session_state.started = False
            st.session_state.page = "menu"
            st.rerun()
    with nav3:
        if st.button("Open Dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()

    st.markdown('<div class="content-wrap">', unsafe_allow_html=True)

    with st.expander("Our Story"):
        st.markdown(
            """
            <div class="white-box">
                <p>Carelio was built to help sponsors, nonprofits, and community organizations better understand where food support may be needed most across Minnesota.</p>
                <p>It was designed to turn county-level analysis into something easier to explore, share, and use for planning meaningful support.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("What Carelio Means"):
        st.markdown(
            """
            <div class="pink-box">
                <p>The name Carelio is inspired by care, community, and action. It reflects support, well-being, and organized efforts to help where the need may be greater.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("Why It Is Useful"):
        st.markdown(
            """
            <div class="yellow-box">
                <p>Carelio combines food need and health risk to provide a more practical view of community vulnerability.</p>
                <p>This helps organizations and supporters review county-level signals before planning outreach, sponsorship, partnerships, or food support efforts.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("How It Can Be Used"):
        st.markdown(
            """
            <div class="green-box">
                <ul>
                    <li>Sponsors can review counties that may need greater support attention.</li>
                    <li>Nonprofits can use it as a starting point for outreach planning.</li>
                    <li>Community groups can compare counties before focusing local efforts.</li>
                    <li>Partners can use it to support discussions around food support priorities.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("How Carelio Scores Work"):
        st.markdown(
            """
            <div class="white-box">
                <p><strong>Food Need Score:</strong> Represents relative food access challenges across counties based on the available dataset indicators.</p>
                <p><strong>Health Risk Score:</strong> Represents relative health-related vulnerability factors that may affect food security.</p>
                <p><strong>Final Priority Score:</strong> A combined score used to rank counties based on overall relative need.</p>
                <ul>
                    <li>Higher score → relatively higher priority</li>
                    <li>Lower score → relatively lower priority</li>
                </ul>
                <p><strong>Important:</strong> These are comparative prioritization scores, not direct percentages of people affected.</p>
                <p><strong>Data source:</strong> This data was taken from the Minnesota public health website.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("How To Interpret This In Real Life"):
        st.markdown(
            """
            <div class="blue-box">
                <p>Carelio scores are designed for comparison across counties.</p>
                <p>They do not directly represent an exact percentage of people going without meals. Instead, they help highlight where relative need may be higher and where additional review or support attention may be warranted first.</p>
                <p>This tool is designed for prioritization, not precise measurement.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("Score Formula Used"):
        st.markdown(
            """
            <div class="yellow-box">
                <p><strong>Final Priority Score</strong> is based on the combined use of Food Need Score and Health Risk Score.</p>
                <p>This version is intended for prioritization and comparison across counties.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    a1, a2, a3 = st.columns(3)

    with a1:
        st.markdown(
            """
            <div class="action-card-yellow">
                <h3>Donate support</h3>
                <p>Share interest in donating funds, resources, or food support for higher-need Minnesota counties.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.link_button("Open Donation Form", SUPPORT_FORM_URL, use_container_width=True)

    with a2:
        st.markdown(
            """
            <div class="action-card-pink">
                <h3>Become a sponsor</h3>
                <p>Organizations and businesses can express interest in sponsoring county-level food support efforts.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.link_button("Open Sponsorship Form", SUPPORT_FORM_URL, use_container_width=True)

    with a3:
        st.markdown(
            """
            <div class="action-card-orange">
                <h3>Partner organization</h3>
                <p>Nonprofits and community organizations can connect to discuss outreach, planning, and collaboration.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.link_button("Open Partnership Form", SUPPORT_FORM_URL, use_container_width=True)

    st.markdown('<div class="contact-box">', unsafe_allow_html=True)
    st.markdown('<h3>Contact</h3>', unsafe_allow_html=True)
    st.markdown('<p class="contact-name">Created by: Sruthi Vemavarapu</p>', unsafe_allow_html=True)
    st.markdown('<p>Click any icon below to open the destination directly.</p>', unsafe_allow_html=True)

    icon1, icon2, icon3, icon4 = st.columns(4)
    with icon1:
        st.markdown(
            f'''
            <a class="contact-icon-card" href="mailto:{EMAIL_ADDRESS}" target="_blank">
                <div class="contact-icon">📧</div>
                <div class="contact-icon-label">Email</div>
            </a>
            ''',
            unsafe_allow_html=True
        )
    with icon2:
        st.markdown(
            f'''
            <a class="contact-icon-card" href="{LINKEDIN_URL}" target="_blank">
                <div class="contact-icon">💼</div>
                <div class="contact-icon-label">LinkedIn</div>
            </a>
            ''',
            unsafe_allow_html=True
        )
    with icon3:
        st.markdown(
            f'''
            <a class="contact-icon-card" href="{GITHUB_URL}" target="_blank">
                <div class="contact-icon">💻</div>
                <div class="contact-icon-label">GitHub</div>
            </a>
            ''',
            unsafe_allow_html=True
        )
    with icon4:
        st.markdown(
            f'''
            <a class="contact-icon-card" href="{LIVE_URL}" target="_blank">
                <div class="contact-icon">🌐</div>
                <div class="contact-icon-label">Live App</div>
            </a>
            ''',
            unsafe_allow_html=True
        )

    st.markdown("<hr style='border: none; border-top: 1px solid #d1d5db; margin: 18px 0;'>", unsafe_allow_html=True)
    st.markdown('<h3>Update note</h3>', unsafe_allow_html=True)
    st.markdown('<p class="footer-note">Carelio supports planning, prioritization, and outreach using the latest available project dataset.</p>', unsafe_allow_html=True)
    st.markdown('<p class="footer-note">This tool is manually updated and does not refresh in real time.</p>', unsafe_allow_html=True)
    st.markdown('<p class="footer-note"><strong>Current update plan:</strong> Monthly manual data refresh</p>', unsafe_allow_html=True)
    st.markdown('<p class="footer-note"><strong>Last updated:</strong> April 2026</p>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Dashboard page
# -----------------------------
elif st.session_state.page == "dashboard":
    st.markdown(
        """
        <div class="section-hero">
            <div class="section-hero-inner">
                <h1>Carelio Dashboard</h1>
                <p class="tagline">Interactive county priority view</p>
                <p class="subnote">Review top-priority counties, compare urgency levels, and explore county-level need in a practical way.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav1, nav2, nav3 = st.columns(3)
    with nav1:
        if st.button("← Back", use_container_width=True):
            st.session_state.page = "menu"
            st.rerun()
    with nav2:
        if st.button("⌂ Home", use_container_width=True):
            st.session_state.started = False
            st.session_state.page = "menu"
            st.rerun()
    with nav3:
        if st.button("About Me", use_container_width=True):
            st.session_state.page = "about"
            st.rerun()

    st.sidebar.markdown("## Filters")
    st.sidebar.markdown("Choose an urgency level to focus the county ranking.")
    urgency_options = ["All"] + sorted(df["Urgency Level"].unique().tolist())
    selected_urgency = st.sidebar.selectbox("Urgency Level", urgency_options)

    if selected_urgency != "All":
        filtered_df = df[df["Urgency Level"] == selected_urgency].copy()
    else:
        filtered_df = df.copy()

    filtered_df = filtered_df.sort_values(priority_col, ascending=False).reset_index(drop=True)
    critical_count = int((filtered_df["Urgency Level"] == "Critical").sum())

    st.markdown('<div class="content-wrap">', unsafe_allow_html=True)

    if filtered_df.empty:
        st.markdown(
            """
            <div class="pink-box">
                <h3>No counties available</h3>
                <p>No counties match the selected urgency level.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        top_county = filtered_df.iloc[0][county_col]
        top_score = filtered_df.iloc[0][priority_col]
        avg_score = filtered_df[priority_col].mean()

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(metric_card("Counties in current view", str(len(filtered_df))), unsafe_allow_html=True)
        with m2:
            st.markdown(metric_card("Top county", str(top_county)), unsafe_allow_html=True)
        with m3:
            st.markdown(metric_card("Highest score", f"{top_score:.2f}"), unsafe_allow_html=True)
        with m4:
            st.markdown(metric_card("Critical counties", str(critical_count)), unsafe_allow_html=True)

        top_left, top_right = st.columns([1.7, 1])

        with top_left:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)

            if selected_urgency == "All":
                st.markdown('<h3>Top 10 Priority Counties</h3>', unsafe_allow_html=True)
                st.markdown('<div class="section-caption">Fast visual summary of the highest-priority counties in the current view</div>', unsafe_allow_html=True)
                chart_df = filtered_df[[county_col, priority_col, "Urgency Level"]].head(10).copy()
            else:
                st.markdown(f'<h3>Top {min(len(filtered_df), 10)} {selected_urgency} Counties</h3>', unsafe_allow_html=True)
                st.markdown('<div class="section-caption">Fast visual summary of counties in the selected urgency level</div>', unsafe_allow_html=True)
                chart_df = filtered_df[[county_col, priority_col, "Urgency Level"]].head(10).copy()

            chart = alt.Chart(chart_df).mark_bar(
                cornerRadiusTopLeft=8,
                cornerRadiusTopRight=8
            ).encode(
                x=alt.X(f"{county_col}:N", sort='-y', title="County"),
                y=alt.Y(f"{priority_col}:Q", title="Final Priority Score"),
                color=alt.Color(
                    "Urgency Level:N",
                    scale=alt.Scale(
                        domain=["Critical", "High", "Moderate", "Low"],
                        range=["#ef4444", "#f59e0b", "#3b82f6", "#22c55e"]
                    ),
                    legend=alt.Legend(title="Urgency Level")
                ),
                tooltip=[county_col, priority_col, "Urgency Level"]
            ).properties(height=360)

            st.altair_chart(chart, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with top_right:
            st.markdown('<div class="white-box">', unsafe_allow_html=True)
            st.markdown('<h3 style="color:#111827; margin-bottom:6px;">County Detail</h3>', unsafe_allow_html=True)

            county_list = filtered_df[county_col].tolist()
            selected_county = st.selectbox("Select a county", county_list)

            county_data = filtered_df[filtered_df[county_col] == selected_county].iloc[0]

            st.markdown(metric_card("County", str(county_data[county_col])), unsafe_allow_html=True)
            st.markdown(metric_card("Food Need Score", f"{county_data[food_col]:.2f}"), unsafe_allow_html=True)
            st.markdown(metric_card("Health Risk Score", f"{county_data[health_col]:.2f}"), unsafe_allow_html=True)
            st.markdown(metric_card("Final Priority Score", f"{county_data[priority_col]:.2f}"), unsafe_allow_html=True)
            st.markdown(urgency_badge(county_data["Urgency Level"]), unsafe_allow_html=True)
            st.markdown(
                '<p class="mini-note">Use this panel to review the selected county before making outreach or support decisions.</p>',
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        bottom_left, bottom_mid, bottom_right = st.columns([1.3, 1.1, 1.1])

        with bottom_left:
            st.markdown('<div class="green-box">', unsafe_allow_html=True)
            st.markdown('<h3 style="color:#111827; margin-bottom:6px;">All County Ranking</h3>', unsafe_allow_html=True)
            st.markdown('<div class="section-caption">Counties ranked by Final Priority Score</div>', unsafe_allow_html=True)
            display_df = filtered_df[[county_col, food_col, health_col, priority_col, "Urgency Level"]].copy()
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with bottom_mid:
            st.markdown(
                f"""
                <div class="yellow-box">
                    <h3>What this score means</h3>
                    <p>{explain_score(county_data[priority_col])}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            why_title, why_text = why_county_ranked(
                county_data[food_col],
                county_data[health_col],
                county_data[priority_col],
                county_data["Urgency Level"]
            )

            st.markdown(
                f"""
                <div class="blue-box">
                    <h3>{why_title}</h3>
                    <p>{why_text}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with bottom_right:
            st.markdown(
                """
                <div class="pink-box">
                    <h3>How dashboard works</h3>
                    <ul>
                        <li>Scan the chart to identify the strongest need signal.</li>
                        <li>Use the ranking table to compare counties side by side.</li>
                        <li>Open County Detail to review one county more closely.</li>
                        <li>Filter by urgency level from the sidebar for faster planning.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                """
                <div class="white-box">
                    <h3>Score formula used</h3>
                    <p><strong>Final Priority Score</strong> is based on the combined use of Food Need Score and Health Risk Score.</p>
                    <p>This version is intended for prioritization and comparison across counties.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(metric_card("Average score in current view", f"{avg_score:.2f}"), unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
