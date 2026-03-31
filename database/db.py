import sqlite3
import os
from datetime import datetime, date, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "emotion_diary.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            reminder_start_hour INTEGER DEFAULT 9,
            reminder_end_hour INTEGER DEFAULT 22,
            timezone_offset INTEGER DEFAULT 3,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS emotion_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            emotion TEXT NOT NULL,
            intensity INTEGER NOT NULL CHECK(intensity BETWEEN 1 AND 10),
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            period_type TEXT NOT NULL CHECK(period_type IN ('day', 'week', 'month')),
            period_date TEXT NOT NULL,
            summary_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE INDEX IF NOT EXISTS idx_entries_user_date
            ON emotion_entries(user_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_summaries_user_period
            ON summaries(user_id, period_type, period_date);
    """)

    conn.commit()
    conn.close()


# --- User operations ---

def get_or_create_user(user_id, username=None, first_name=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name),
        )
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()

    conn.close()
    return dict(user)


def update_user_settings(user_id, reminder_start_hour, reminder_end_hour, timezone_offset):
    conn = get_connection()
    conn.execute(
        """UPDATE users SET reminder_start_hour = ?, reminder_end_hour = ?, timezone_offset = ?
           WHERE user_id = ?""",
        (reminder_start_hour, reminder_end_hour, timezone_offset, user_id),
    )
    conn.commit()
    conn.close()


def get_all_users():
    conn = get_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return [dict(u) for u in users]


# --- Emotion entry operations ---

EMOTIONS = [
    {"id": "joy", "name": "Радость", "emoji": "😊", "color": "#FFD93D"},
    {"id": "sadness", "name": "Грусть", "emoji": "😢", "color": "#6C9BCF"},
    {"id": "anger", "name": "Злость", "emoji": "😠", "color": "#E74C3C"},
    {"id": "fear", "name": "Страх", "emoji": "😰", "color": "#9B59B6"},
    {"id": "surprise", "name": "Удивление", "emoji": "😲", "color": "#F39C12"},
    {"id": "disgust", "name": "Отвращение", "emoji": "🤢", "color": "#27AE60"},
    {"id": "anxiety", "name": "Тревога", "emoji": "😟", "color": "#E67E22"},
    {"id": "calm", "name": "Спокойствие", "emoji": "😌", "color": "#3498DB"},
    {"id": "love", "name": "Любовь", "emoji": "🥰", "color": "#E91E63"},
    {"id": "guilt", "name": "Вина", "emoji": "😔", "color": "#795548"},
    {"id": "shame", "name": "Стыд", "emoji": "😳", "color": "#FF7043"},
    {"id": "excitement", "name": "Возбуждение", "emoji": "🤩", "color": "#FF6F00"},
    {"id": "boredom", "name": "Скука", "emoji": "😑", "color": "#90A4AE"},
    {"id": "gratitude", "name": "Благодарность", "emoji": "🙏", "color": "#66BB6A"},
    {"id": "loneliness", "name": "Одиночество", "emoji": "🥺", "color": "#5C6BC0"},
    {"id": "hope", "name": "Надежда", "emoji": "🌟", "color": "#FFCA28"},
]


def add_emotion_entry(user_id, emotion, intensity, note=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO emotion_entries (user_id, emotion, intensity, note) VALUES (?, ?, ?, ?)",
        (user_id, emotion, intensity, note),
    )
    conn.commit()
    entry_id = cursor.lastrowid
    conn.close()
    return entry_id


def get_entries_for_date(user_id, target_date):
    conn = get_connection()
    entries = conn.execute(
        """SELECT * FROM emotion_entries
           WHERE user_id = ? AND date(created_at) = ?
           ORDER BY created_at""",
        (user_id, target_date),
    ).fetchall()
    conn.close()
    return [dict(e) for e in entries]


def get_entries_for_range(user_id, start_date, end_date):
    conn = get_connection()
    entries = conn.execute(
        """SELECT * FROM emotion_entries
           WHERE user_id = ? AND date(created_at) BETWEEN ? AND ?
           ORDER BY created_at""",
        (user_id, start_date, end_date),
    ).fetchall()
    conn.close()
    return [dict(e) for e in entries]


def get_daily_summary_data(user_id, target_date):
    """Get aggregated emotion data for a single day."""
    entries = get_entries_for_date(user_id, target_date)
    return _aggregate_entries(entries)


def get_weekly_summary_data(user_id, target_date):
    """Get aggregated emotion data for the week containing target_date."""
    d = datetime.strptime(target_date, "%Y-%m-%d").date()
    start = d - timedelta(days=d.weekday())  # Monday
    end = start + timedelta(days=6)  # Sunday

    entries = get_entries_for_range(user_id, start.isoformat(), end.isoformat())

    # Group by day and get dominant emotion per day
    days = {}
    for e in entries:
        day = e["created_at"][:10]
        days.setdefault(day, []).append(e)

    daily_dominants = []
    for day_entries in days.values():
        agg = _aggregate_entries(day_entries)
        if agg:
            # Pick the emotion with highest average intensity
            top = max(agg, key=lambda x: x["avg_intensity"])
            daily_dominants.append(top)

    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "daily_data": {day: _aggregate_entries(de) for day, de in days.items()},
        "overall": _aggregate_entries(entries),
        "total_entries": len(entries),
    }


def get_monthly_summary_data(user_id, year, month):
    """Get aggregated emotion data for a month."""
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)

    entries = get_entries_for_range(user_id, start.isoformat(), end.isoformat())

    days = {}
    for e in entries:
        day = e["created_at"][:10]
        days.setdefault(day, []).append(e)

    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "daily_data": {day: _aggregate_entries(de) for day, de in days.items()},
        "overall": _aggregate_entries(entries),
        "total_entries": len(entries),
    }


def _aggregate_entries(entries):
    """Aggregate entries into emotion stats: count, avg intensity, total duration."""
    if not entries:
        return []

    emotions = {}
    for e in entries:
        emo = e["emotion"]
        if emo not in emotions:
            emotions[emo] = {"emotion": emo, "count": 0, "total_intensity": 0}
        emotions[emo]["count"] += 1
        emotions[emo]["total_intensity"] += e["intensity"]

    result = []
    for emo, data in emotions.items():
        data["avg_intensity"] = round(data["total_intensity"] / data["count"], 1)
        result.append(data)

    result.sort(key=lambda x: (-x["count"], -x["avg_intensity"]))
    return result


# --- Summary operations ---

def save_summary(user_id, period_type, period_date, summary_text):
    conn = get_connection()
    # Upsert
    existing = conn.execute(
        "SELECT id FROM summaries WHERE user_id = ? AND period_type = ? AND period_date = ?",
        (user_id, period_type, period_date),
    ).fetchone()

    if existing:
        conn.execute(
            "UPDATE summaries SET summary_text = ? WHERE id = ?",
            (summary_text, existing["id"]),
        )
    else:
        conn.execute(
            "INSERT INTO summaries (user_id, period_type, period_date, summary_text) VALUES (?, ?, ?, ?)",
            (user_id, period_type, period_date, summary_text),
        )
    conn.commit()
    conn.close()


def get_summary(user_id, period_type, period_date):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM summaries WHERE user_id = ? AND period_type = ? AND period_date = ?",
        (user_id, period_type, period_date),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_emotion_entry(entry_id, user_id):
    conn = get_connection()
    conn.execute(
        "DELETE FROM emotion_entries WHERE id = ? AND user_id = ?",
        (entry_id, user_id),
    )
    conn.commit()
    conn.close()
