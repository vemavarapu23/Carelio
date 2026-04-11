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
    if urgency == "Critical":
        return '<div class="critical-badge">Urgency Level: Critical</div>'
    elif urgency == "High":
        return '<div class="high-badge">Urgency Level: High</div>'
    elif urgency == "Moderate":
        return '<div class="moderate-badge">Urgency Level: Moderate</div>'
    return '<div class="low-badge">Urgency Level: Low</div>'

# -----------------------------
# Images
# -----------------------------
header_banner = get_base64_image("header_banner.avif")
page_bg = get_base64_image("page_bg.jpg")

# -----------------------------
# CSS
# -----------------------------
st.markdown(f"""
<style>
    .stApp {{
        background:
            linear-gradient(rgba(255,255,255,0.80), rgba(255,255,255,0.84)),
            url("data:image/jpg;base64,{page_bg}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    .block-container {{
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1250px;
    }}

    section[data-testid="stSidebar"] {{
        background: rgba(255, 247, 236, 0.92);
        border-right: 2px solid rgba(240, 190, 95, 0.55);
        backdrop-filter: blur(8px);
    }}

    .hero-banner {{
        background:
            linear-gradient(rgba(0,0,0,0.48), rgba(0,0,0,0.48)),
            url("data:image/avif;base64,{header_banner}");
        background-size: cover;
        background-position: center;
        border-radius: 28px;
        min-height: 320px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 42px;
        margin-bottom: 24px;
        box-shadow: 0 10px 28px rgba(0,0,0,0.16);
    }}

    .hero-banner h1 {{
        color: white !important;
        font-size: 82px !important;
        margin-bottom: 10px !important;
        font-weight: 900 !important;
    }}

    .hero-banner .tagline {{
        color: #fffaf2 !important;
        font-size: 25px !important;
        margin: 7px 0 !important;
        font-weight: 700 !important;
        line-height: 1.4 !important;
    }}

    .hero-banner .creator {{
        color: #fffaf6 !important;
        font-size: 26px !important;
        margin-top: 16px !important;
        font-weight: 700 !important;
        font-family: "Segoe Script", "Lucida Handwriting", "Brush Script MT", cursive !important;
    }}

    .content-wrap {{
        background: rgba(255,255,255,0.58);
        border-radius: 28px;
        padding: 24px;
        backdrop-filter: blur(4px);
    }}

    .pink-box {{
        background: rgba(255, 233, 243, 0.90);
        border: 2px solid rgba(242, 167, 200, 0.85);
        border-radius: 22px;
        padding: 18px;
        box-shadow: 0 6px 14px rgba(0,0,0,0.05);
        margin-bottom: 18px;
    }}

    .yellow-box {{
        background: rgba(255, 245, 196, 0.90);
        border: 2px solid rgba(244, 201, 93, 0.85);
        border-radius: 22px;
        padding: 18px;
        box-shadow: 0 6px 14px rgba(0,0,0,0.05);
        margin-bottom: 18px;
    }}

    .white-box {{
        background: rgba(255,255,255,0.90);
        border: 1px solid rgba(234, 215, 164, 0.95);
        border-radius: 22px;
        padding: 18px;
        box-shadow: 0 6px 14px rgba(0,0,0,0.05);
        margin-bottom: 18px;
    }}

    .green-box {{
        background: rgba(232, 247, 236, 0.92);
        border: 1px solid rgba(144, 196, 157, 0.95);
        border-radius: 22px;
        padding: 18px;
        box-shadow: 0 6px 14px rgba(0,0,0,0.05);
        margin-bottom: 18px;
    }}

    .skyblue-box {{
        background: rgba(232, 244, 255, 0.92);
        border: 1px solid rgba(147, 197, 253, 0.95);
        border-radius: 22px;
        padding: 18px;
        box-shadow: 0 6px 14px rgba(0,0,0,0.05);
        margin-bottom: 18px;
    }}

    .contact-box {{
        background: rgba(255,255,255,0.90);
        border: 1px solid rgba(234, 215, 164, 0.95);
        border-radius: 22px;
        padding: 18px;
        box-shadow: 0 6px 14px rgba(0,0,0,0.05);
        margin-bottom: 18px;
    }}

    .action-card-yellow {{
        background: rgba(255, 247, 196, 0.92);
        border: 1px solid rgba(244, 201, 93, 0.95);
        border-radius: 22px;
        padding: 18px;
        min-height: 180px;
        box-shadow: 0 6px 14px rgba(0,0,0,0.05);
    }}

    .action-card-pink {{
        background: rgba(255, 236, 245, 0.92);
        border: 1px solid rgba(242, 167, 200, 0.95);
        border-radius: 22px;
        padding: 18px;
        min-height: 180px;
        box-shadow: 0 6px 14px rgba(0,0,0,0.05);
    }}

    .action-card-orange {{
        background: rgba(255, 238, 220, 0.92);
        border: 1px solid rgba(245, 158, 11, 0.95);
        border-radius: 22px;
        padding: 18px;
        min-height: 180px;
        box-shadow: 0 6px 14px rgba(0,0,0,0.05);
    }}

    .action-card-yellow h3,
    .action-card-pink h3,
    .action-card-orange h3 {{
        color: #5b21b6 !important;
        font-size: 24px !important;
        margin-bottom: 8px !important;
    }}

    .action-card-yellow p,
    .action-card-pink p,
    .action-card-orange p {{
        color: #374151 !important;
        font-size: 17px !important;
        line-height: 1.6 !important;
    }}

    div[data-testid="metric-container"] {{
        background: linear-gradient(to bottom right, rgba(255,255,255,0.97), rgba(255,249,242,0.97));
        border: 1px solid rgba(243, 217, 164, 0.95);
        padding: 18px;
        border-radius: 18px;
        box-shadow: 0 6px 14px rgba(255, 138, 0, 0.10);
    }}

    .critical-badge {{
        background: #ffe3e3;
        color: #b00020;
        padding: 10px 14px;
        border-radius: 12px;
        font-weight: 700;
        display: inline-block;
        margin-top: 8px;
    }}

    .high-badge {{
        background: #fff1d6;
        color: #b45309;
        padding: 10px 14px;
        border-radius: 12px;
        font-weight: 700;
        display: inline-block;
        margin-top: 8px;
    }}

    .moderate-badge {{
        background: #dbeafe;
        color: #1d4ed8;
        padding: 10px 14px;
        border-radius: 12px;
        font-weight: 700;
        display: inline-block;
        margin-top: 8px;
    }}

    .low-badge {{
        background: #dcfce7;
        color: #15803d;
        padding: 10px 14px;
        border-radius: 12px;
        font-weight: 700;
        display: inline-block;
        margin-top: 8px;
    }}

    h2, h3 {{
        color: #4b1d6b !important;
    }}

    .mini-note {{
        color: #374151;
        font-size: 16px;
    }}

    .section-caption {{
        color: #6b7280;
        font-size: 16px;
        margin-top: -6px;
        margin-bottom: 8px;
    }}
</style>
""", unsafe_allow_html=True)

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
# Header
# -----------------------------
st.markdown("""
<div class="hero-banner">
    <div>
        <h1>Carelio</h1>
        <p class="tagline">A Minnesota food support prioritization tool for sponsors, nonprofits, and community organizations.</p>
        <p class="tagline">Helping identify where food support may be needed most across Minnesota.</p>
        <p class="creator">Created by Sruthi Vemavarapu</p>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Sidebar filter
# -----------------------------
st.sidebar.markdown("## Filters")
st.sidebar.markdown("Choose an urgency level to view matching counties.")
urgency_options = ["All"] + sorted(df["Urgency Level"].unique().tolist())
selected_urgency = st.sidebar.selectbox("Urgency Level", urgency_options)

if selected_urgency != "All":
    filtered_df = df[df["Urgency Level"] == selected_urgency].copy()
else:
    filtered_df = df.copy()

filtered_df = filtered_df.sort_values(priority_col, ascending=False).reset_index(drop=True)

# -----------------------------
# Main page
# -----------------------------
st.markdown('<div class="content-wrap">', unsafe_allow_html=True)

st.markdown('<div class="pink-box">', unsafe_allow_html=True)
st.subheader("Our Story")
st.markdown(
    "<div style='font-size:18px; line-height:1.7; color:#374151;'>"
    "Carelio was built to help sponsors, nonprofits, and community groups better understand "
    "where food support may be needed most across Minnesota. It combines food need and health-related risk "
    "to give a simple starting point for planning, outreach, and support."
    "</div>",
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="yellow-box">', unsafe_allow_html=True)
st.subheader("Why Carelio Is Different")
st.markdown(
    "<div style='font-size:18px; line-height:1.7; color:#374151;'>"
    "Carelio is designed to complement existing food resource tools by helping sponsors, nonprofits, "
    "and community organizations better understand where support may be needed most across Minnesota."
    "</div>",
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="white-box">', unsafe_allow_html=True)
st.subheader("Why Food Need and Health Risk Are Combined")
st.markdown(
    "<div style='font-size:18px; line-height:1.7; color:#374151;'>"
    "Carelio combines food need and health risk to give a more complete view of community need. "
    "Food need shows where people may be struggling more with access to enough nutritious food. "
    "Health risk shows where poor food access may have a bigger impact on overall well-being. "
    "When both are high in the same county, it can suggest that the county may need closer attention for food support planning."
    "</div>",
    unsafe_allow_html=True
)
st.markdown(
    "<div style='font-size:18px; line-height:1.7; color:#374151; margin-top:10px;'>"
    "This does not mean health risk alone decides where support should go. "
    "It is used as an extra signal to better understand vulnerability alongside food need. "
    "Together, these measures help sponsors, nonprofits, and community organizations make more informed decisions."
    "</div>",
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="white-box">', unsafe_allow_html=True)
st.subheader("What Carelio Means")
st.markdown(
    "<div style='font-size:18px; line-height:1.7; color:#374151;'>"
    "Carelio is inspired by the ideas of care, living, and organization. "
    "The name reflects support, well-being, and community action across Minnesota."
    "</div>",
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

if filtered_df.empty:
    st.markdown('<div class="pink-box">', unsafe_allow_html=True)
    st.subheader("No counties available")
    st.write("No counties match the selected urgency level.")
    st.markdown('</div>', unsafe_allow_html=True)
else:
    top_county = filtered_df.iloc[0][county_col]
    top_score = filtered_df.iloc[0][priority_col]

    st.markdown('<div class="yellow-box">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Counties in current view", len(filtered_df))
    c2.metric("Highest Priority County", top_county)
    c3.metric("Highest Priority Score", f"{top_score:.2f}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="pink-box">', unsafe_allow_html=True)
    st.subheader("How to Use This Tool")
    st.markdown("""
- Sponsors can use this tool to identify counties that may need greater food support attention  
- Nonprofits can use it to support outreach and planning decisions  
- Community groups can review county-level need before focusing support efforts  
- The results provide a starting point for food support prioritization across Minnesota  
""")
    st.markdown('</div>', unsafe_allow_html=True)

    a1, a2, a3 = st.columns(3)

    with a1:
        st.markdown("""
        <div class="action-card-yellow">
            <h3>Donate Support</h3>
            <p>Share your interest in donating funds, resources, or food support for higher-need Minnesota counties.</p>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("Open Donation Form", SUPPORT_FORM_URL, use_container_width=True)
        st.markdown(f"[Or email directly](mailto:{EMAIL_ADDRESS}?subject=Carelio%20Donation%20Interest)")

    with a2:
        st.markdown("""
        <div class="action-card-pink">
            <h3>Become a Sponsor</h3>
            <p>Organizations and businesses can express interest in sponsoring county-level food support efforts.</p>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("Open Sponsorship Form", SUPPORT_FORM_URL, use_container_width=True)
        st.markdown(f"[Or email directly](mailto:{EMAIL_ADDRESS}?subject=Carelio%20Sponsor%20Interest)")

    with a3:
        st.markdown("""
        <div class="action-card-orange">
            <h3>Partner Organization</h3>
            <p>Nonprofits and community organizations can connect to discuss outreach, planning, and collaboration.</p>
        </div>
        """, unsafe_allow_html=True)
        st.link_button("Open Partnership Form", SUPPORT_FORM_URL, use_container_width=True)
        st.markdown(f"[Or email directly](mailto:{EMAIL_ADDRESS}?subject=Carelio%20Partnership%20Interest)")

    left, right = st.columns([2.2, 1.1])

    with left:
        st.markdown('<div class="green-box">', unsafe_allow_html=True)
        st.subheader("County Priority Ranking")
        st.markdown('<div class="section-caption">Counties ranked by final priority score</div>', unsafe_allow_html=True)
        display_df = filtered_df[[county_col, food_col, health_col, priority_col, "Urgency Level"]].copy()
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="white-box">', unsafe_allow_html=True)
        st.subheader("County Detail")
        county_list = filtered_df[county_col].tolist()
        selected_county = st.selectbox("Select a county", county_list)

        county_data = filtered_df[filtered_df[county_col] == selected_county].iloc[0]

        st.metric("County", county_data[county_col])
        st.metric("Food Need Score", f"{county_data[food_col]:.2f}")
        st.metric("Health Risk Score", f"{county_data[health_col]:.2f}")
        st.metric("Final Priority Score", f"{county_data[priority_col]:.2f}")
        st.markdown(urgency_badge(county_data["Urgency Level"]), unsafe_allow_html=True)

        st.markdown("""
        <p class="mini-note">
        This county may deserve closer review for food support outreach and planning
        based on its relative score.
        </p>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    b1, b2 = st.columns([1.4, 1])

    with b1:
        st.markdown('<div class="skyblue-box">', unsafe_allow_html=True)
        if selected_urgency == "All":
            st.subheader("Top 10 Counties in Current View")
            shown_df = filtered_df[[county_col, priority_col, "Urgency Level"]].head(10).copy()
        else:
            st.subheader(f"{selected_urgency} Counties in Current View")
            shown_df = filtered_df[[county_col, priority_col, "Urgency Level"]].copy()
        st.dataframe(shown_df, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with b2:
        st.markdown('<div class="pink-box">', unsafe_allow_html=True)
        st.subheader("Planning Note")
        st.write(
            "This tool helps sponsors, nonprofit organizations, and community groups identify Minnesota counties "
            "where food support may be needed more urgently. It is designed to support planning and outreach."
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="contact-box">', unsafe_allow_html=True)
    st.subheader("Contact")
    st.write("For collaboration, sponsorship discussions, nonprofit partnerships, or project inquiries:")
    st.markdown(f"**Email:** [{EMAIL_ADDRESS}](mailto:{EMAIL_ADDRESS})")
    st.markdown(f"**LinkedIn:** [Connect on LinkedIn]({LINKEDIN_URL})")
    st.markdown("**Created by:** Sruthi Vemavarapu")
    st.markdown("---")
    st.markdown("**Update Note**")
    st.write(
        "Carelio is based on the latest available project dataset and is intended to support planning, prioritization, and outreach."
    )
    st.write(
        "This tool does not track live real-time county needs automatically. The data should be updated regularly, such as monthly, to reflect the most recent available information."
    )
    st.markdown("**Current update plan:** Monthly manual data refresh")
    st.markdown("**Last updated:** April 2026")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
