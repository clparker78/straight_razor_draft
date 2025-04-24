import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from PIL import Image, ImageDraw
import random
import os

st.set_page_config(page_title="Straight Razor Draft 2025", layout="wide")

# ---------- Load Data ----------
sheet_url = "https://docs.google.com/spreadsheets/d/1UZkdBJlZ0T4Wd0TM9q6U5HBfyeQOH7ORE8y7QZOI4PQ/export?format=csv"

@st.cache_data(ttl=60)
def load_draft_results():
    return pd.read_csv(sheet_url)

@st.cache_data
def load_entries():
    return pd.read_excel("Straight_Razor_Entries.xlsx", engine="openpyxl")

try:
    draft_df = load_draft_results()
    draft_df = draft_df[draft_df['Pick'] <= 32]
    picks_done = len(draft_df)
except:
    draft_df = pd.DataFrame()
    picks_done = 0

try:
    entries_df = load_entries()
except:
    entries_df = pd.DataFrame()

# ---------- Score Logic ----------
def calculate_scores(entries_df, results_df):
    scores = []
    for i, row in entries_df.iterrows():
        name = row[2]  # Name is in column C
        user_picks = row[3:].values.tolist()
        total_score = 0
        correct = 0
        streak = 0
        max_streak = 0
        for pos, player in enumerate(user_picks):
            if player in results_df['Player'].values:
                actual_pos = results_df[results_df['Player'] == player]['Pick'].values[0]
                diff = abs((pos+1) - actual_pos)
                score = 32 if diff == 0 else max(0, 32 - diff)
                total_score += score
                if diff == 0:
                    correct += 1
                    streak += 1
                    max_streak = max(max_streak, streak)
                else:
                    streak = 0
        scores.append({
            "name": name,
            "score": total_score,
            "correct": correct
        })
    return sorted(scores, key=lambda x: (-x['score'], -x['correct']))

leaderboard = calculate_scores(entries_df, draft_df) if not entries_df.empty and not draft_df.empty else []


# ---------- Styling ----------
st.markdown("""
<style>
/* Bouncing logo animation */
.logo-img {
    display: block;
    margin: 0 auto;
    width: 220px;
    animation: bounce-in 1.5s ease forwards;
}
@keyframes bounce-in {
    0%   { transform: scale(0.5) translateY(-50px); opacity: 0; }
    50%  { transform: scale(1.2) translateY(0); opacity: 1; }
    100% { transform: scale(1) translateY(0); opacity: 1; }
}

/* Toast */
.toast {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: #2E8B57;
    color: white;
    padding: 10px 15px;
    border-radius: 5px;
    font-weight: bold;
    z-index: 1000;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    opacity: 1;
    transition: opacity 2s ease-in;
}
.toast.hide {
    opacity: 0;
}

/* Goalpost container */
.goalpost-container {
    position: fixed;
    top: 80px; right: 20px;
    width: 240px;
    height: 300px;
    z-index: 1000;
    text-align: center;
}
.goalpost-img {
    width: 150%;
}
.ball-img {
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    width: 60px;
    visibility: hidden;
}
.ball-animate { animation: kick 2s ease forwards; }
.ball-animate-double { animation: doublekick 2.5s ease forwards; }
.pick-info {
    position: absolute;
    top: 5px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(250, 240, 230, 0.9);
    color: black;
    padding: 3px 6px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: bold;
    opacity: 0;
    transition: opacity 0.5s;
}
@keyframes kick {
    0%   { bottom: 0; left: 50%; visibility: visible; }
    50%  { bottom: 100%; left: 50%; }
    100% { bottom: 100%; left: 50%; visibility: hidden; }
}
@keyframes doublekick {
    0%   { bottom: 0; left: 48%; visibility: visible; }
    25%  { bottom: 70%; left: 0%; }
    50%  { bottom: 30%; left: 80%; }
    75%  { bottom: 70%; left: 100%; }
    100% { bottom: 100%; left: 50%; visibility: hidden; }
}
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar Logo----------
with st.sidebar:
    st.sidebar.subheader("Welcome to the")
    st.image("Straight_Razor_Draft_2025.jpg", width=300)

# ---------- Sidebar Manual Refresh Button ----------
with st.sidebar:
    if st.button("🔄 Refresh Draft Results"):
        st.cache_data.clear()
        st.rerun()

# ---------- Pick Tracker ----------
def draw_pick_pie(picks_done, total=32):
    fig = go.Figure(go.Pie(
        values=[picks_done, total - picks_done],
        hole=0.5,
        sort=False,
        direction='clockwise',
        marker_colors=['#8B4513', '#e0dfd5'],
        textinfo='none'
    ))
    fig.update_layout(
        width=300, height=180,
        margin=dict(t=20, b=20, l=20, r=20),
        showlegend=False,
        annotations=[{
            "text": f"{picks_done}/32",
            "font": {"size": 24, "color": "black"},
            "showarrow": False,
            "xref": "paper", "yref": "paper",
            "x": 0.5, "y": 0.5
        }]
    )
    return fig

# ---------- Sidebar Tracker----------
with st.sidebar:
    st.sidebar.subheader("📋First Round Picks")
    st.plotly_chart(draw_pick_pie(picks_done), config={"staticPlot": True}, use_container_width=True)

# ---------- Race Visual ----------
def create_race_image(participants, width=600, height=200):
    try:
        field_bg = Image.open("field_background.png").resize((width, height))
    except:
        field_bg = Image.new("RGB", (width, height), color=(34, 139, 34))
        draw = ImageDraw.Draw(field_bg)
        for x in range(0, width, width // 4):
            draw.line([(x, 0), (x, height)], fill="white", width=2)

    placeholder = Image.open("placeholder.png").resize((40, 40))
    lanes = len(participants)
    if lanes == 0:
        return field_bg
    lane_height = height // lanes
    for idx, p in enumerate(participants):
        head_img = placeholder
        try:
            image_path = f"headshots/{p['name'].replace(' ', '_')}.png"
            if os.path.exists(image_path):
                head_img = Image.open(image_path).resize((40, 40))
        except:
            pass
        progress_ratio = p['score'] / 1024  # Max 32x32 = 1024
        x_pos = int(progress_ratio * (width - 50))
        y_pos = int(lane_height * idx + (lane_height / 2) - 20)
        field_bg.paste(head_img, (x_pos, y_pos), mask=head_img.convert("RGBA"))

# Add score next to image
        draw = ImageDraw.Draw(field_bg)
        score_text = f"{p['score']} pts"
        draw.text((x_pos + 45, y_pos + 10), score_text, fill="white")

    return field_bg

# Main page race visual
st.subheader("🏁 Leaderboard")
top_runners = leaderboard[:5] if leaderboard else []
race_image = create_race_image(top_runners, 600, 200)
st.image(race_image, use_container_width=True)

# ---------- AI Commentary ----------

def get_commentary(old_board, new_board):
    comments = []
    old_rank = {x['name']: i+1 for i, x in enumerate(old_board)}
    new_rank = {x['name']: i+1 for i, x in enumerate(new_board)}

    if not new_board: return ["The silence before the storm..."]

    lead_now = new_board[0]['name']
    lead_before = old_board[0]['name'] if old_board else None
    if lead_now != lead_before:
        comments.append(f"👑 {lead_now} just took the top spot — {lead_before} is on notice.")

    for p in new_board:
        name = p['name']
        if name in old_rank:
            diff = old_rank[name] - new_rank[name]
            if diff >= 2:
                comments.append(f"🚀 {name} rockets up from #{old_rank[name]} to #{new_rank[name]}!")
            elif diff <= -2:
                comments.append(f"📉 {name} drops from #{old_rank[name]} to #{new_rank[name]} — ouch.")
        if p.get("current_streak", 0) >= 3:
            comments.append(f"🔥 {name} is on a heater with {p['current_streak']} straight hits.")

    if not comments:
        comments.append("All quiet on the draft front... for now.")
    return comments[:3]

if leaderboard:
    commentary = get_commentary(st.session_state.prev_leaderboard, leaderboard)
    for line in commentary:
        st.write(line)
    st.session_state.prev_leaderboard = leaderboard.copy()

# Full leaderboard
st.subheader("🏆 The Straight Razor Draft Leaderboard")
if leaderboard:
    st.dataframe(pd.DataFrame(leaderboard))
else:
    st.info("Waiting for picks and entries...")


# ---------- Goalpost Animation ----------

# Centered goalpost image in the main content area
col1, col2, col3 = st.columns([1, 2, 1])

if 'last_pick_count' not in st.session_state:
    st.session_state.last_pick_count = 0

team_logos = {team: f"logos/{team}.png" for team in draft_df['Team'].unique()} if not draft_df.empty else {}

current_pick_count = len(draft_df)
if current_pick_count > st.session_state.last_pick_count:
    st.session_state.last_pick_count = current_pick_count
    latest = draft_df.iloc[-1]
    pick_num = latest['Pick']
    team_name = latest['Team']
    team_logo = team_logos.get(team_name, "")
    anim_class = "ball-animate-double" if team_name == "Chicago Bears" else "ball-animate"
    js = f"""
    <script>
    var ball = document.getElementById('football');
    var info = document.getElementById('pick-info');
    if (ball && info) {{
        ball.className = 'ball-img {anim_class}';
        info.innerHTML = "Pick {pick_num}: <img src='{team_logo}' class='team-logo' alt='{team_name}'/>";
        info.style.opacity = 1;
        setTimeout(function() {{
            ball.className = 'ball-img';
            info.style.opacity = 0;
            info.innerHTML = "";
        }}, 3000);
    }}
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)


# ---------- Draft Picks Table ----------
st.subheader("📋 First Round NFL Draft Picks")

if not draft_df.empty:
    st.dataframe(
        draft_df[['Pick', 'Player', 'Team']],
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No picks have been entered yet.")


# ---------- Footer / Signature (Optional) ----------
st.markdown("---")
st.caption("Straight Razor Draft 2025 · Built with Streamlit · Designed for drama 🏈")

