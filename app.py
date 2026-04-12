import base64
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Carelio", layout="wide")

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

def urgency_badge(urgency):
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

def contact_icon_card(icon: str, label: str, href: str) -> str:
    return f"""
    <a class="contact-icon-card" href="{href}" target="_blank">
        <div class="contact-icon">{icon}</div>
        <div class="contact-icon-label">{label}</div>
    </a>
    """

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
            linear-gradient(rgba(255,255,255,0.76), rgba(255,255,255,0.84)),
            url("data:image/jpg;base64,{page_bg}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    .block-container {{
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1260px;
        animation: pageFade 0.8s ease-out;
    }}

    section[data-testid="stSidebar"] {{
        background: rgba(255, 247, 236, 0.97);
        border-right: 2px solid rgba(240, 190, 95, 0.45);
        backdrop-filter: blur(8px);
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
            linear-gradient(rgba(0,0,0,0.40), rgba(0,0,0,0.52)),
            url("data:image/avif;base64,{header_banner}");
        background-size: cover;
        background-position: center;
        box-shadow: 0 20px 46px rgba(0,0,0,0.18);
        animation: heroRise 0.95s ease-out;
    }}

    .hero-screen::before {{
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(120deg, rgba(255,255,255,0.08), rgba(255,255,255,0.00), rgba(255,255,255,0.09));
        animation: shimmer 8s linear infinite;
        pointer-events: none;
    }}

    .hero-inner {{
        position: relative;
        z-index: 2;
        max-width: 940px;
        animation: fadeInSoft 1s ease-out;
    }}

    .hero-title {{
        color: #ffffff !important;
        font-size: 96px !important;
        font-weight: 900 !important;
        letter-spacing: 0.8px !important;
        margin-bottom: 10px !important;
        animation: softPulse 4s ease-in-out infinite;
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

    div.stButton {{
        display: flex;
        justify-content: center;
        margin-top: 8px;
    }}

    div.stButton > button:first-child {{
        background: linear-gradient(135deg, #f59e0b, #f97316) !important;
        color: white !important;
        border: none !important;
        border-radius: 999px !important;
        padding: 0.9rem 2.8rem !important;
        font-size: 1.05rem !important;
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

    .dashboard-hero {{
        position: relative;
        overflow: hidden;
        background:
            linear-gradient(rgba(0,0,0,0.40), rgba(0,0,0,0.48)),
            url("data:image/avif;base64,{header_banner}");
        background-size: cover;
        background-position: center;
        border-radius: 30px;
        min-height: 250px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 34px;
        margin-bottom: 18px;
        box-shadow: 0 14px 34px rgba(0,0,0,0.18);
        animation: heroRise 0.9s ease-out;
    }}

    .dashboard-hero::before {{
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(120deg, rgba(255,255,255,0.06), rgba(255,255,255,0.00), rgba(255,255,255,0.08));
        animation: shimmer 8s linear infinite;
        pointer-events: none;
    }}

    .dashboard-hero-inner {{
        position: relative;
        z-index: 2;
    }}

    .dashboard-hero h1 {{
        color: white !important;
        font-size: 70px !important;
        margin: 0 0 8px 0 !important;
        font-weight: 900 !important;
        letter-spacing: 0.5px !important;
        animation: softPulse 3.8s ease-in-out infinite;
    }}

    .dashboard-hero .tagline {{
        color: #fffaf2 !important;
        font-size: 22px !important;
        margin: 6px 0 !important;
        font-weight: 700 !important;
        line-height: 1.4 !important;
    }}

    .dashboard-hero .subnote {{
        color: #fff8ef !important;
        font-size: 17px !important;
        margin: 12px 0 0 0 !important;
        line-height: 1.65 !important;
        font-weight: 500 !important;
    }}

    .content-wrap {{
        background: rgba(255,255,255,0.72);
        border-radius: 30px;
        padding: 24px;
        backdrop-filter: blur(8px);
        box-shadow: 0 12px 28px rgba(0,0,0,0.08);
        animation: fadeInSoft 0.8s ease-out;
    }}

    .glass-card {{
        backdrop-filter: blur(6px);
    }}

    .pink-box, .yellow-box, .white-box, .green-box, .contact-box, .chart-card {{
        border-radius: 22px;
        padding: 20px;
        margin-bottom: 18px;
        box-shadow: 0 6px 14px rgba(0,0,0,0.06);
        color: #111827 !important;
        animation: fadeInSoft 0.75s ease-out;
        transition: transform 0.28s ease, box-shadow 0.28s ease;
    }}

    .pink-box:hover, .yellow-box:hover, .white-box:hover, .green-box:hover,
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

    .pink-box h3, .yellow-box h3, .white-box h3, .green-box h3, .contact-box h3, .chart-card h3 {{
        color: #111827 !important;
        font-size: 24px !important;
        margin: 0 0 10px 0 !important;
        font-weight: 700 !important;
    }}

    .pink-box p, .yellow-box p, .white-box p, .green-box p, .contact-box p, .chart-card p,
    .pink-box li, .yellow-box li, .white-box li, .green-box li, .contact-box li {{
        color: #111827 !important;
        font-size: 16px !important;
        line-height: 1.7 !important;
        margin-bottom: 8px !important;
    }}

    .pink-box ul, .yellow-box ul, .white-box ul, .green-box ul, .contact-box ul {{
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
        color: #6b7280 !important;
        line-height: 1.7 !important;
        animation: fadeInSoft 0.9s ease-out;
    }}

    .contact-name {{
        color: #111827 !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        margin-bottom: 12px !important;
    }}

    .contact-icon-row {{
        display: flex;
        gap: 14px;
        flex-wrap: wrap;
        margin-top: 12px;
        margin-bottom: 6px;
    }}

    .contact-icon-card {{
        display: flex;
        align-items: center;
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

    .contact-icon-card:active {{
        animation: clickPop 0.2s ease;
    }}

    .contact-icon {{
        font-size: 22px;
        line-height: 1;
    }}

    .contact-icon-label {{
        color: #111827 !important;
        font-size: 15px !important;
        font-weight: 700 !important;
    }}

    .urgency-badge {{
        padding: 10px 14px;
        border-radius: 12px;
        font-weight: 700;
        display: inline-block;
        margin-top: 8px;
    }}

    .stSelectbox label,
    .stMultiSelect label,
    .stTextInput label,
    .stTextArea label {{
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
        st.rerun()

# -----------------------------
# Dashboard page
# -----------------------------
else:
    st.markdown(
        """
        <div class="dashboard-hero">
            <div class="dashboard-hero-inner">
                <h1>Carelio</h1>
                <p class="tagline">Minnesota county priority view</p>
                <p class="subnote">Review top-priority counties, compare urgency levels, and explore county-level need in seconds.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
                chart_df = filtered_df[[county_col, priority_col]].head(10).copy()
            else:
                st.markdown(f'<h3>Top {min(len(filtered_df), 10)} {selected_urgency} Counties</h3>', unsafe_allow_html=True)
                st.markdown('<div class="section-caption">Fast visual summary of counties in the selected urgency level</div>', unsafe_allow_html=True)
                chart_df = filtered_df[[county_col, priority_col]].head(10).copy()

            st.bar_chart(chart_df.set_index(county_col), use_container_width=True, height=360)
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

        rank_left, rank_right = st.columns([2.2, 1])

        with rank_left:
            st.markdown('<div class="green-box">', unsafe_allow_html=True)
            st.markdown('<h3 style="color:#111827; margin-bottom:6px;">All County Ranking</h3>', unsafe_allow_html=True)
            st.markdown('<div class="section-caption">Counties ranked by Final Priority Score</div>', unsafe_allow_html=True)

            display_df = filtered_df[[county_col, food_col, health_col, priority_col, "Urgency Level"]].copy()
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            st.markdown("</div>", unsafe_allow_html=True)

        with rank_right:
            st.markdown(
                """
                <div class="pink-box">
                    <h3>What Carelio does</h3>
                    <p>Carelio helps sponsors, nonprofits, and community organizations quickly see where food support may be needed most across Minnesota.</p>
                    <p>It combines food need and health risk signals into a simpler starting point for outreach, prioritization, and support planning.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(metric_card("Average score in current view", f"{avg_score:.2f}"), unsafe_allow_html=True)

        info1, info2 = st.columns(2)

        with info1:
            st.markdown(
                """
                <div class="white-box">
                    <h3>How to use this</h3>
                    <ul>
                        <li>Scan the top chart to identify the strongest need signal.</li>
                        <li>Use the county ranking to compare counties side by side.</li>
                        <li>Open County Detail to review one county more closely.</li>
                        <li>Filter by urgency level from the sidebar for faster planning.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with info2:
            st.markdown(
                """
                <div class="yellow-box">
                    <h3>Why combine food need and health risk</h3>
                    <p>Food need highlights access challenges. Health risk adds another signal about community vulnerability. Together, they create a more useful priority view than either signal alone.</p>
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

        contact_html = f"""
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
st.markdown('</div>', unsafe_allow_html=True)
            <p class="footer-note">Carelio supports planning, prioritization, and outreach using the latest available project dataset.</p>
            <p class="footer-note">This tool is manually updated and does not refresh in real time.</p>
            <p class="footer-note"><strong>Current update plan:</strong> Monthly manual data refresh</p>
            <p class="footer-note"><strong>Last updated:</strong> April 2026</p>
        </div>
        """
        st.markdown(contact_html, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
