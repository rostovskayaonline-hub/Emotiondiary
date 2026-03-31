import os
import logging
from datetime import datetime, date, timedelta

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "")


def get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            reminder_start_hour INTEGER DEFAULT 9,
            reminder_end_hour INTEGER DEFAULT 22,
            timezone_offset INTEGER DEFAULT 3,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emotion_entries (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(user_id),
            emotion TEXT NOT NULL,
            intensity INTEGER NOT NULL CHECK(intensity BETWEEN 1 AND 10),
            note TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL REFERENCES users(user_id),
            period_type TEXT NOT NULL CHECK(period_type IN ('day', 'week', 'month')),
            period_date TEXT NOT NULL,
            summary_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_entries_user_date
            ON emotion_entries(user_id, created_at);
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_summaries_user_period
            ON summaries(user_id, period_type, period_date);
    """)

    conn.commit()
    cursor.close()
    conn.close()
    logger.info("Database initialized (PostgreSQL)")


# --- User operations ---

def get_or_create_user(user_id, username=None, first_name=None):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name) VALUES (%s, %s, %s)",
            (user_id, username, first_name),
        )
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()

    cursor.close()
    conn.close()
    return dict(user)


def update_user_settings(user_id, reminder_start_hour, reminder_end_hour, timezone_offset):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE users SET reminder_start_hour = %s, reminder_end_hour = %s, timezone_offset = %s
           WHERE user_id = %s""",
        (reminder_start_hour, reminder_end_hour, timezone_offset, user_id),
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_all_users():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.close()
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


def add_emotion_entry(user_id, emotion, intensity, note=None, local_time=None):
    conn = get_connection()
    cursor = conn.cursor()
    if local_time:
        cursor.execute(
            "INSERT INTO emotion_entries (user_id, emotion, intensity, note, created_at) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (user_id, emotion, intensity, note, local_time),
        )
    else:
        cursor.execute(
            "INSERT INTO emotion_entries (user_id, emotion, intensity, note) VALUES (%s, %s, %s, %s) RETURNING id",
            (user_id, emotion, intensity, note),
        )
    entry_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return entry_id


def get_entries_for_date(user_id, target_date):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """SELECT id, user_id, emotion, intensity, note,
                  to_char(created_at, 'YYYY-MM-DD"T"HH24:MI:SS') as created_at
           FROM emotion_entries
           WHERE user_id = %s AND created_at::date = %s
           ORDER BY created_at""",
        (user_id, target_date),
    )
    entries = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(e) for e in entries]


def get_entries_for_range(user_id, start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """SELECT id, user_id, emotion, intensity, note,
                  to_char(created_at, 'YYYY-MM-DD"T"HH24:MI:SS') as created_at
           FROM emotion_entries
           WHERE user_id = %s AND created_at::date BETWEEN %s AND %s
           ORDER BY created_at""",
        (user_id, start_date, end_date),
    )
    entries = cursor.fetchall()
    cursor.close()
    conn.close()
    return [dict(e) for e in entries]


def get_daily_summary_data(user_id, target_date):
    entries = get_entries_for_date(user_id, target_date)
    return _aggregate_entries(entries)


def get_weekly_summary_data(user_id, target_date):
    d = datetime.strptime(target_date, "%Y-%m-%d").date()
    start = d - timedelta(days=d.weekday())
    end = start + timedelta(days=6)

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


def get_monthly_summary_data(user_id, year, month):
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
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute(
        "SELECT id FROM summaries WHERE user_id = %s AND period_type = %s AND period_date = %s",
        (user_id, period_type, period_date),
    )
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            "UPDATE summaries SET summary_text = %s WHERE id = %s",
            (summary_text, existing["id"]),
        )
    else:
        cursor.execute(
            "INSERT INTO summaries (user_id, period_type, period_date, summary_text) VALUES (%s, %s, %s, %s)",
            (user_id, period_type, period_date, summary_text),
        )
    conn.commit()
    cursor.close()
    conn.close()


def get_summary(user_id, period_type, period_date):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT * FROM summaries WHERE user_id = %s AND period_type = %s AND period_date = %s",
        (user_id, period_type, period_date),
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return dict(row) if row else None


def delete_emotion_entry(entry_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM emotion_entries WHERE id = %s AND user_id = %s",
        (entry_id, user_id),
    )
    conn.commit()
    cursor.close()
    conn.close()
