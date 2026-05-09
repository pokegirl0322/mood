import calendar
import hashlib
import random
import altair as alt
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from db import get_all_data, get_streak, get_daily_award as db_get_daily_award, save_daily_award, get_all_daily_awards
from ai import generate_summary

SURPRISE_REWARDS = [
    "🎮 Extra hour of screen time!",
    "🛋️ Skip one chore today!",
    "🎵 DJ of the day — pick the family playlist!",
    "🍕 Choose what's for dinner tomorrow!",
    "🕹️ Extra 30 min of video games!",
    "👑 King/Queen of the couch — best seat all evening!",
    "🃏 Swap one chore with another family member!",
    "📺 Pick what to watch during family time!",
    "🛒 Add one snack to the grocery list!",
    "🐾 No pet duties for a day!",
]

mood_emoji_map = {"good": "😄", "okay": "🙂", "meh": "😐", "bad": "😕", "awful": "😡"}
mood_score = {"good": 5, "okay": 4, "meh": 3, "bad": 2, "awful": 1}


def get_daily_award(d, users):
    """Get daily award from DB, or generate and store one for today."""
    winner, reward = db_get_daily_award(d)
    if winner:
        return winner, reward
    # Only generate new awards for today (not past dates without one)
    if d == date.today() and len(users) > 0:
        winner = random.choice(users)
        reward = random.choice(SURPRISE_REWARDS)
        save_daily_award(d, winner, reward)
        return winner, reward
    return None, None


# --- Page config & branding ---
st.set_page_config(page_title="Family Mood Quest", page_icon="🌟", layout="wide")

st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #e8f4fd 0%, #fef9e7 50%, #fde8e8 100%);
    }

    /* Header banner */
    .mood-banner {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3);
    }
    .mood-banner h1 {
        color: white;
        font-size: 2.2em;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    .mood-banner p {
        color: rgba(255,255,255,0.9);
        font-size: 1.1em;
        margin: 4px 0 0 0;
    }

    /* Section cards */
    .section-card {
        background: white;
        border-radius: 12px;
        padding: 20px 24px;
        margin: 16px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid #4facfe;
    }
    .section-card.rewards {
        border-left-color: #f5a623;
    }
    .section-card.trends {
        border-left-color: #7ed321;
    }

    /* Calendar cells */
    .cal-cell {
        padding: 6px;
        min-height: 70px;
        border-radius: 8px;
        background: white;
        margin: 2px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        font-size: 0.85em;
    }
    .cal-cell.today {
        border: 2px solid #4facfe;
        background: rgba(79, 172, 254, 0.08);
    }
    .cal-cell.muted {
        background: transparent;
        box-shadow: none;
        color: #ccc;
    }
    .cal-award {
        font-size: 0.7em;
        color: #f5a623;
        margin-top: 2px;
    }
    .cal-header {
        font-weight: 700;
        text-align: center;
        color: #555;
        padding: 4px;
    }

    /* Streak badges */
    .streak-badge {
        display: inline-block;
        background: linear-gradient(135deg, #f5a623, #f7c948);
        color: white;
        border-radius: 20px;
        padding: 4px 14px;
        font-weight: 600;
        font-size: 0.9em;
        margin: 4px 0;
    }

    /* Award highlight */
    .award-box {
        background: linear-gradient(135deg, #fff9e6, #fff3cd);
        border: 1px solid #f5a623;
        border-radius: 10px;
        padding: 14px 18px;
        margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- Banner ---
st.markdown("""
<div class="mood-banner">
    <h1>🌟 Family Mood Quest 🌟</h1>
    <p>Check In. Cheer Up. Earn Rewards!</p>
</div>
""", unsafe_allow_html=True)

# --- Load data ---
data = get_all_data()

if not data:
    st.info("No mood data yet. Use the Discord bot to start checking in!")
    st.stop()

df = pd.DataFrame(data, columns=["id", "user", "mood", "reason", "response", "theme", "timestamp"])
df["timestamp"] = pd.to_datetime(df["timestamp"])
df["date"] = df["timestamp"].dt.date
df["score"] = df["mood"].map(mood_score)

today = date.today()
users = sorted(df["user"].unique().tolist())

# =============================================================================
# CALENDAR
# =============================================================================
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown("## 📅 Mood Calendar")

col_m, col_y, _ = st.columns([1, 1, 4])
month_names = list(calendar.month_name)[1:]
selected_month = col_m.selectbox("Month", range(1, 13), index=today.month - 1, format_func=lambda m: month_names[m - 1])
years_available = sorted(df["timestamp"].dt.year.unique(), reverse=True)
if today.year not in years_available:
    years_available = [today.year] + list(years_available)
selected_year = col_y.selectbox("Year", years_available)

# Build mood lookup: date -> list of (user, mood)
month_df = df[(df["timestamp"].dt.month == selected_month) & (df["timestamp"].dt.year == selected_year)]
day_moods = {}
for _, row in month_df.iterrows():
    d = row["date"]
    if d not in day_moods:
        day_moods[d] = []
    day_moods[d].append((row["user"], row["mood"]))

# Render calendar grid
cal = calendar.Calendar(firstweekday=6)  # Sunday first
weeks = cal.monthdatescalendar(selected_year, selected_month)

# Header row
day_headers = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
header_cols = st.columns(7)
for i, name in enumerate(day_headers):
    header_cols[i].markdown(f'<div class="cal-header">{name}</div>', unsafe_allow_html=True)

# Calendar weeks
selected_date = None
for week in weeks:
    cols = st.columns(7)
    for i, day in enumerate(week):
        with cols[i]:
            if day.month != selected_month:
                st.markdown(f'<div class="cal-cell muted">{day.day}</div>', unsafe_allow_html=True)
            else:
                entries = day_moods.get(day, [])
                emojis = " ".join(mood_emoji_map.get(m, "❓") for _, m in entries) if entries else ""
                is_today = day == today
                css_class = "cal-cell today" if is_today else "cal-cell"

                # Daily award for this date
                winner, reward = get_daily_award(day, users)
                award_html = ""
                if winner and entries:  # only show award on days with check-ins
                    award_html = f'<div class="cal-award">🏆 {winner}</div>'

                cell_html = f'<div class="{css_class}"><b>{day.day}</b>'
                if emojis:
                    cell_html += f"<br>{emojis}"
                cell_html += award_html + "</div>"
                st.markdown(cell_html, unsafe_allow_html=True)

                if entries:
                    with st.expander("Details"):
                        day_df = df[df["date"] == day]
                        for _, row in day_df.iterrows():
                            emoji = mood_emoji_map.get(row["mood"], "❓")
                            st.markdown(f"**{row['user']}** {emoji} — {row['reason']}  ")
                            st.caption(f"_{row['response']}_")
                        w, r = get_daily_award(day, users)
                        if w:
                            st.markdown(f'<div class="award-box">🏆 <b>Daily Surprise:</b> {w} — {r}</div>', unsafe_allow_html=True)
                        if st.button("🧠 AI Summary", key=f"sum_{day}"):
                            day_text = day_df[["user", "mood", "reason"]].to_string(index=False)
                            st.info(generate_summary(day_text))

st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# REWARDS & STREAKS
# =============================================================================
st.markdown('<div class="section-card rewards">', unsafe_allow_html=True)
st.markdown("## 🏆 Rewards & Streaks")

rcol1, rcol2, rcol3 = st.columns(3)

# --- Today's surprise ---
with rcol1:
    st.markdown("#### 🎲 Today's Surprise")
    winner, reward = get_daily_award(today, users)
    if winner:
        st.markdown(f'<div class="award-box">🎉 <b>{winner}</b><br>{reward}</div>', unsafe_allow_html=True)

# --- Streaks ---
with rcol2:
    st.markdown("#### 🔥 Streaks")
    for user in users:
        streak = get_streak(user)
        if streak >= 7:
            st.markdown(f'**{user}** <span class="streak-badge">🔥 {streak} days</span>', unsafe_allow_html=True)
        else:
            st.write(f"**{user}** — {streak} days (need 7)")

# --- Family improvement ---
with rcol3:
    st.markdown("#### 📈 Family Trend")
    week_ago = today - timedelta(days=7)
    two_weeks_ago = today - timedelta(days=14)
    this_week = df[(df["date"] > week_ago) & (df["date"] <= today)]
    last_week = df[(df["date"] > two_weeks_ago) & (df["date"] <= week_ago)]

    if not this_week.empty and not last_week.empty:
        this_avg = this_week["score"].mean()
        last_avg = last_week["score"].mean()
        diff = this_avg - last_avg
        st.metric("This week", f"{this_avg:.1f}", f"{diff:+.1f}")
        if diff > 0.5:
            st.success("Family mood is improving!")
        elif diff > 0:
            st.info("Slight improvement — keep going!")
        else:
            st.caption("Mood dipped a bit. Hang in there! 💪")
    else:
        st.write("Not enough data yet.")

st.markdown('</div>', unsafe_allow_html=True)

# =============================================================================
# MOOD TRENDS
# =============================================================================
score_labels = {1: "😡 Awful", 2: "😕 Bad", 3: "😐 Meh", 4: "🙂 Okay", 5: "😄 Good"}
y_scale = alt.Scale(domain=[1, 5])
y_axis = alt.Axis(values=[1, 2, 3, 4, 5], labelExpr="datum.value == 1 ? '😡' : datum.value == 2 ? '😕' : datum.value == 3 ? '😐' : datum.value == 4 ? '🙂' : '😄'")

st.markdown('<div class="section-card trends">', unsafe_allow_html=True)
st.markdown("## 📊 Mood Trends")

# Overall mood trend
daily_avg = df.groupby("date")["score"].mean().reset_index()
daily_avg.columns = ["Date", "Avg Mood Score"]
overall_chart = alt.Chart(daily_avg).mark_line(point=True, color="#4facfe").encode(
    x=alt.X("Date:T", title="Date"),
    y=alt.Y("Avg Mood Score:Q", scale=y_scale, axis=y_axis, title="Mood"),
    tooltip=["Date:T", alt.Tooltip("Avg Mood Score:Q", format=".1f")],
).properties(height=250)
st.altair_chart(overall_chart, width="stretch")

# Per-user charts side by side
st.markdown("#### 👥 Per-User Trends")
user_cols = st.columns(len(users)) if len(users) <= 4 else st.columns(2)
for idx, user in enumerate(users):
    with user_cols[idx % len(user_cols)]:
        user_df = df[df["user"] == user].groupby("date")["score"].mean().reset_index()
        user_df.columns = ["Date", "Score"]
        st.markdown(f"**{user}**")
        user_chart = alt.Chart(user_df).mark_line(point=True).encode(
            x=alt.X("Date:T", title=None, axis=alt.Axis(labels=False)),
            y=alt.Y("Score:Q", scale=y_scale, axis=y_axis, title=None),
            tooltip=["Date:T", alt.Tooltip("Score:Q", format=".1f")],
        ).properties(height=150)
        st.altair_chart(user_chart, width="stretch")

# Mood distribution + recent check-ins
dcol1, dcol2 = st.columns(2)
with dcol1:
    dist_range = st.radio("Mood Distribution", ["This Week", "This Month", "All Time"], horizontal=True, label_visibility="visible")
    if dist_range == "This Week":
        dist_df = df[df["date"] > today - timedelta(days=7)]
    elif dist_range == "This Month":
        dist_df = df[(df["timestamp"].dt.month == today.month) & (df["timestamp"].dt.year == today.year)]
    else:
        dist_df = df
    score_counts = dist_df["score"].value_counts().reset_index()
    score_counts.columns = ["Score", "Count"]
    score_counts["Label"] = score_counts["Score"].map(score_labels)
    dist_chart = alt.Chart(score_counts).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X("Score:O", title="Mood", axis=alt.Axis(labelExpr="datum.value == 1 ? '😡 Awful' : datum.value == 2 ? '😕 Bad' : datum.value == 3 ? '😐 Meh' : datum.value == 4 ? '🙂 Okay' : '😄 Good'")),
        y=alt.Y("Count:Q", title="Check-ins"),
        color=alt.Color("Score:O", scale=alt.Scale(domain=[1, 2, 3, 4, 5], range=["#F44336", "#FF9800", "#FFC107", "#8BC34A", "#4CAF50"]), legend=None),
        tooltip=["Label:N", "Count:Q"],
    ).properties(height=250)
    st.altair_chart(dist_chart, width="stretch")

with dcol2:
    st.markdown("#### 🕐 Recent Check-ins")
    recent = df.sort_values("timestamp", ascending=False).head(8)
    for _, row in recent.iterrows():
        emoji = mood_emoji_map.get(row["mood"], "❓")
        st.markdown(f"{emoji} **{row['user']}** — {row['reason']} ({row['timestamp'].strftime('%m/%d %H:%M')})")

st.markdown('</div>', unsafe_allow_html=True)
