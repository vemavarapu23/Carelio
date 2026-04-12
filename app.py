import streamlit as st
import pandas as pd

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="Carelio", layout="wide")

# -------------------- VFX + UI CSS --------------------
st.markdown("""
<style>

/* 🌈 Animated background */
.stApp {
    background: linear-gradient(135deg, #fdf6ff, #f7fbff, #fff8f2);
    background-size: 300% 300%;
    animation: gradientBG 12s ease infinite;
}

@keyframes gradientBG {
    0% {background-position: 0% 50%;}
    50% {background-position: 100% 50%;}
    100% {background-position: 0% 50%;}
}

/* ✨ Glass Card */
.card {
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(14px);
    border-radius: 20px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 10px 30px rgba(0,0,0,0.12);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

/* Hover Animation */
.card:hover {
    transform: translateY(-6px) scale(1.01);
    box-shadow: 0 18px 40px rgba(0,0,0,0.18);
}

/* Floating Animation */
.floating {
    animation: float 4s ease-in-out infinite;
}

@keyframes float {
    0% { transform: translateY(0px);}
    50% { transform: translateY(-6px);}
    100% { transform: translateY(0px);}
}

/* Shine Effect */
.card::before {
    content: "";
    position: absolute;
    top: -120%;
    left: -40%;
    width: 60%;
    height: 300%;
    background: linear-gradient(
        120deg,
        rgba(255,255,255,0) 20%,
        rgba(255,255,255,0.4) 50%,
        rgba(255,255,255,0) 80%
    );
    transform: rotate(20deg);
    animation: shine 6s linear infinite;
}

@keyframes shine {
    0% { left: -60%; }
    100% { left: 140%; }
}

/* 🏷 Badge */
.badge {
    padding: 6px 12px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: bold;
    display: inline-block;
    margin-bottom: 10px;
}

.high { background: #ff6b6b; color: white; }
.medium { background: #f7b731; color: white; }
.low { background: #2ecc71; color: white; }

/* Titles */
h1, h2, h3 {
    font-weight: 800;
}

/* Button style */
button[kind="primary"] {
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# -------------------- SAMPLE DATA --------------------
data = {
    "County": ["Mahnomen", "Nobles", "Beltrami", "Clearwater", "Todd"],
    "Food Need Score": [86.7, 72.0, 68.9, 72.2, 61.7],
    "Health Risk Score": [97.1, 64.0, 59.0, 50.0, 53.0]
}
df = pd.DataFrame(data)

# -------------------- PRIORITY CALC --------------------
def get_priority(food, health):
    avg = (food + health) / 2
    if avg >= 75:
        return "High"
    elif avg >= 55:
        return "Moderate"
    else:
        return "Low"

df["Priority"] = df.apply(lambda x: get_priority(x["Food Need Score"], x["Health Risk Score"]), axis=1)

# -------------------- SIDEBAR --------------------
st.sidebar.title("Filters")

priority_filter = st.sidebar.selectbox(
    "Select Urgency Level",
    ["All", "High", "Moderate", "Low"]
)

# Filter data
if priority_filter != "All":
    df = df[df["Priority"] == priority_filter]

# -------------------- TITLE --------------------
st.title("🌍 Carelio – Food & Health Priority Insights")

# -------------------- TABLE --------------------
st.subheader("County Ranking")

st.dataframe(df, use_container_width=True)

# -------------------- SELECT COUNTY --------------------
selected_county = st.selectbox("Select a County", df["County"])

row = df[df["County"] == selected_county].iloc[0]

food_score = row["Food Need Score"]
health_score = row["Health Risk Score"]
priority = row["Priority"]

# -------------------- DYNAMIC EXPLANATION --------------------
def get_reason(food, health, priority):
    if priority == "High":
        return "Both food need and health risk are significantly high, making this county a top priority for intervention."
    elif priority == "Moderate":
        return "One or both indicators show moderate risk levels, placing this county in a balanced priority category."
    else:
        return "Food need and health risk are comparatively lower, so this county has a lower urgency level."

reason = get_reason(food_score, health_score, priority)

# -------------------- BADGE CLASS --------------------
badge_class = "high" if priority == "High" else "medium" if priority == "Moderate" else "low"

# -------------------- UI CARDS --------------------
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div class="card floating">
        <div class="badge {badge_class}">{priority} Priority</div>
        <h3>📊 Why this county is ranked this way</h3>
        <p>{reason}</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="card floating">
        <h3>📈 Score Breakdown</h3>
        <p><b>Food Need Score:</b> {food_score}</p>
        <p><b>Health Risk Score:</b> {health_score}</p>
    </div>
    """, unsafe_allow_html=True)

# -------------------- ABOUT SECTION --------------------
with st.expander("ℹ️ About this project"):
    st.markdown("""
    This project analyzes county-level food insecurity and health risk to prioritize areas that need support.

    Data source: Minnesota Public Health datasets.

    Built using SQL, Python, and Streamlit for real-time data insights.
    """)

# -------------------- EXTRA ANIMATION --------------------
st.markdown("""
<div style="text-align:center; margin-top:30px; font-size:14px; opacity:0.7;">
✨ Built with data + design thinking ✨
</div>
""", unsafe_allow_html=True)
