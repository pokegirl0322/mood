# Family Mood App — User Guide

## Starting the App

### 1. Start the Discord Bot
```bash
source venv/bin/activate
python bot.py
```
You should see `Logged in as <your bot name>` in the terminal.

### 2. Start the Dashboard
In a separate terminal:
```bash
source venv/bin/activate
streamlit run dashboard.py
```
Opens at `http://localhost:8501` in your browser.

---

## Using the Discord Bot

### Manual Check-in (Fastest Way to Test)

Type `!mood` in any channel the bot can see. The bot will reply with 5 emoji buttons:

| Button | Mood |
|--------|------|
| 😄 | Good |
| 🙂 | Okay |
| 😐 | Meh |
| 😕 | Bad |
| 😡 | Awful |

After you pick a mood, a second row of buttons appears asking **why**:

| Button | Reason |
|--------|--------|
| School/Work | Stressed from school or work |
| Tired | Low energy |
| Hungry | Need food |
| Social | Something social happened |
| Loss | Dealing with a loss |
| Skip | No specific reason |

After you pick a reason, the bot responds with a personalized AI message from your stuffed animal companion. Occasionally (~15% of the time) it also sends an AI-generated image.

### Random Prompts

The bot automatically sends mood check-ins to a random channel **every 4 hours**. You don't need to do anything — just click the buttons when they appear.

### Daily Limit

Each user can check in **up to 2 times per day**. After that, the bot will let you know to come back tomorrow.

### Streaks

If you check in for **5 or more consecutive days**, the bot will congratulate you and suggest a reward.

---

## Using the Dashboard

Open `http://localhost:8501` and use the sidebar to switch between views:

### 📅 Calendar View
- Pick a date from the dropdown
- See every check-in for that day (who, what mood, why)
- Read an AI-generated summary of the family's day

### 📊 Data View
- **Mood Trends**: Line chart of average family mood over time (5 = good, 1 = awful)
- **Per-User Trends**: Individual mood charts for each family member
- **Mood Distribution**: Bar chart showing how often each mood was picked
- **Recent Check-ins**: The last 10 entries with details

### 🏆 Rewards View
- **Streak Rewards**: 5+ consecutive days of check-ins earns a small reward (drinks, skip a chore)
- **Family Improvement**: If the family's average mood goes up week-over-week, earn a medium reward (movie night, dinner out)
- **Weekly Surprise**: One random family member gets a surprise reward each week (extra screen time)

---

## Quick Test Checklist

1. Start `python bot.py` — confirm "Logged in" message
2. Go to Discord, type `!mood`
3. Click an emoji → click a reason → get an AI response
4. Open the dashboard at `http://localhost:8501`
5. Your check-in should appear in all 3 views

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Bot doesn't respond to `!mood` | Make sure the bot has permission to read messages and send messages in the channel |
| "You've already checked in twice today" | Wait until tomorrow, or clear the `moods` table in MySQL to reset |
| Dashboard shows "No mood data yet" | Do at least one check-in via `!mood` first |
| Bot won't start | Check that `DISCORD_TOKEN` in `.env` is a valid bot token |
| Database errors | Make sure MySQL is running and the `.env` credentials are correct |
