import os
from datetime import datetime, date, timedelta
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
}
DB_NAME = os.getenv("MYSQL_DATABASE", "familymood")


def _get_connection(use_db=True):
    config = dict(DB_CONFIG)
    if use_db:
        config["database"] = DB_NAME
    return mysql.connector.connect(**config)


def init_db():
    conn = _get_connection(use_db=False)
    c = conn.cursor()
    c.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
    conn.commit()
    conn.close()

    conn = _get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS moods (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user VARCHAR(255),
            mood VARCHAR(50),
            reason VARCHAR(255),
            response TEXT,
            theme VARCHAR(50),
            timestamp DATETIME
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_awards (
            award_date DATE PRIMARY KEY,
            winner VARCHAR(255),
            reward TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS streak_rewards (
            user VARCHAR(255) PRIMARY KEY,
            last_reward_date DATE
        )
    """)
    conn.commit()
    conn.close()


def log_mood(user, mood, reason, response, theme):
    conn = _get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO moods (user, mood, reason, response, theme, timestamp) VALUES (%s, %s, %s, %s, %s, %s)",
        (user, mood, reason, response, theme, datetime.now()),
    )
    conn.commit()
    conn.close()


def get_all_data():
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT id, user, mood, reason, response, theme, timestamp FROM moods ORDER BY timestamp")
    rows = c.fetchall()
    conn.close()
    return rows


def get_user_checkins_today(user):
    conn = _get_connection()
    c = conn.cursor()
    today_start = datetime.combine(date.today(), datetime.min.time())
    c.execute(
        "SELECT COUNT(*) FROM moods WHERE user = %s AND timestamp >= %s",
        (user, today_start),
    )
    count = c.fetchone()[0]
    conn.close()
    return count


def _consecutive_streak(dates):
    """Count consecutive days back from today (or yesterday) in a desc-sorted date list."""
    if not dates:
        return 0
    today = date.today()
    if dates[0] != today and dates[0] != today - timedelta(days=1):
        return 0
    streak = 1
    for i in range(1, len(dates)):
        if dates[i] == dates[i - 1] - timedelta(days=1):
            streak += 1
        else:
            break
    return streak


def get_streak(user):
    """Number of consecutive days (ending today or yesterday) the user has at least one check-in."""
    conn = _get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT DISTINCT DATE(timestamp) AS d FROM moods WHERE user = %s ORDER BY d DESC",
        (user,),
    )
    dates = [row[0] for row in c.fetchall()]
    conn.close()
    return _consecutive_streak(dates)


def get_unrewarded_streak(user):
    """Streak counted only from the day after the user's last streak reward — used to gate the next reward."""
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT last_reward_date FROM streak_rewards WHERE user = %s", (user,))
    row = c.fetchone()
    last_reward = row[0] if row else None

    c.execute(
        "SELECT DISTINCT DATE(timestamp) AS d FROM moods WHERE user = %s ORDER BY d DESC",
        (user,),
    )
    dates = [row[0] for row in c.fetchall()]
    conn.close()

    if last_reward:
        dates = [d for d in dates if d > last_reward]
    return _consecutive_streak(dates)


def record_streak_reward(user, reward_date):
    """Record that a streak reward was given to a user on a date — resets their streak counter."""
    conn = _get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO streak_rewards (user, last_reward_date) VALUES (%s, %s) "
        "ON DUPLICATE KEY UPDATE last_reward_date = VALUES(last_reward_date)",
        (user, reward_date),
    )
    conn.commit()
    conn.close()


def get_daily_award(award_date):
    """Get stored daily award for a date. Returns (winner, reward) or (None, None)."""
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT winner, reward FROM daily_awards WHERE award_date = %s", (award_date,))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    return None, None


def save_daily_award(award_date, winner, reward):
    """Store a daily award. Does nothing if one already exists for that date."""
    conn = _get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT IGNORE INTO daily_awards (award_date, winner, reward) VALUES (%s, %s, %s)",
        (award_date, winner, reward),
    )
    conn.commit()
    conn.close()


def get_all_daily_awards():
    """Get all stored daily awards. Returns list of (date, winner, reward)."""
    conn = _get_connection()
    c = conn.cursor()
    c.execute("SELECT award_date, winner, reward FROM daily_awards ORDER BY award_date")
    rows = c.fetchall()
    conn.close()
    return rows


# Initialize on import
init_db()
