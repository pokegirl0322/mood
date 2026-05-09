# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Permissions

Claude Code should operate autonomously — run commands, edit files, and make changes without asking for permission.

## What This Is

A gamified family mood tracking app: Discord bot for quick emoji-based mood check-ins, AI-generated supportive responses via OpenRouter, MySQL storage, and a Streamlit analytics dashboard.

## Commands

```bash
# Activate venv (always do this first)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the Discord bot
python bot.py

# Run the Streamlit dashboard
streamlit run dashboard.py
```

There are no tests or linting configured.

## Architecture

Four modules with clear separation:

```
bot.py ──┬──> ai.py (generate_response, generate_image)
         └──> db.py (log_mood, get_user_checkins_today, get_streak)

dashboard.py ──┬──> db.py (get_all_data, get_streak)
               └──> ai.py (generate_summary)
```

- **bot.py** — Discord bot entry point. `MoodView` (emoji buttons) → `ReasonView` (reason buttons) → AI response → DB log. Has a `@tasks.loop(hours=4)` for random prompts. Enforces 2 check-ins/user/day.
- **ai.py** — OpenRouter client (OpenAI-compatible SDK). Generates short responses in a stuffed-animal persona ("Bao the Panda"), occasional images (15% chance), and daily summaries. Uses `BASE_MODEL` and `IMG_MODEL` from env.
- **db.py** — MySQL via `mysql-connector-python`. Auto-creates database and `moods` table on import. Single table with columns: id, user, mood, reason, response, theme, timestamp.
- **dashboard.py** — Streamlit app with three sidebar views: Calendar (daily summaries), Data (mood trend charts, mood scored as good=5 to awful=1), Rewards (streaks, week-over-week improvement, random weekly winner).

## Environment (.env)

Required variables: `DISCORD_TOKEN`, `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `BASE_MODEL`, `IMG_MODEL`, `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`.

OpenRouter is used as the AI backend — the OpenAI SDK connects to it via `OPENAI_BASE_URL=https://openrouter.ai/api/v1`.

## Key Constraints

- The old file `discord.py` was deleted to fix a circular import with the `discord` package — never name a file `discord.py`.
- `db.py` calls `init_db()` at module level on import, so importing it requires a running MySQL instance.
- The bot requires the **Message Content Intent** enabled in the Discord Developer Portal.
