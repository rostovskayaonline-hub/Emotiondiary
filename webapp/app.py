import os
import sys
import hashlib
import hmac
import json
from datetime import date, datetime, timedelta
from urllib.parse import parse_qs, unquote

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database.db import (
    init_db,
    get_or_create_user,
    add_emotion_entry,
    get_entries_for_date,
    get_entries_for_range,
    get_daily_summary_data,
    get_weekly_summary_data,
    get_monthly_summary_data,
    save_summary,
    get_summary,
    delete_emotion_entry,
    EMOTIONS,
)

load_dotenv()

app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), "static"),
    template_folder=os.path.join(os.path.dirname(__file__), "templates"),
)
CORS(app)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")


def validate_init_data(init_data: str) -> dict | None:
    """Validate Telegram WebApp init data and return user info."""
    if not init_data or not BOT_TOKEN:
        return None

    try:
        parsed = parse_qs(init_data)
        received_hash = parsed.get("hash", [None])[0]
        if not received_hash:
            return None

        data_check_parts = []
        for key in sorted(parsed.keys()):
            if key == "hash":
                continue
            data_check_parts.append(f"{key}={unquote(parsed[key][0])}")
        data_check_string = "\n".join(data_check_parts)

        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(computed_hash, received_hash):
            return None

        user_data = json.loads(unquote(parsed.get("user", ["{}"])[0]))
        return user_data
    except Exception:
        return None


def get_user_id_from_request():
    """Extract user_id from request — validates init_data or falls back to header."""
    init_data = request.headers.get("X-Telegram-Init-Data", "")
    user_data = validate_init_data(init_data)
    if user_data:
        return user_data.get("id")

    # Fallback for development
    user_id = request.headers.get("X-User-Id")
    if user_id:
        return int(user_id)

    return None


# --- Serve frontend ---

@app.route("/")
def index():
    return send_from_directory(app.template_folder, "index.html")


@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory(app.static_folder, path)


# --- API endpoints ---

@app.route("/api/emotions", methods=["GET"])
def api_emotions():
    return jsonify(EMOTIONS)


@app.route("/api/entries", methods=["POST"])
def api_add_entry():
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    get_or_create_user(user_id)

    data = request.json
    emotion = data.get("emotion")
    intensity = data.get("intensity")
    note = data.get("note", "")

    if not emotion or not intensity:
        return jsonify({"error": "emotion and intensity are required"}), 400

    if not (1 <= intensity <= 10):
        return jsonify({"error": "intensity must be between 1 and 10"}), 400

    # Accept client local time if provided, otherwise server will use CURRENT_TIMESTAMP
    local_time = data.get("local_time")  # ISO string from client e.g. "2026-03-31T14:30:00"
    entry_id = add_emotion_entry(user_id, emotion, intensity, note, local_time)
    return jsonify({"id": entry_id, "status": "ok"})


@app.route("/api/entries/<target_date>", methods=["GET"])
def api_get_entries(target_date):
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    entries = get_entries_for_date(user_id, target_date)
    return jsonify(entries)


@app.route("/api/entries/<int:entry_id>", methods=["DELETE"])
def api_delete_entry(entry_id):
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    delete_emotion_entry(entry_id, user_id)
    return jsonify({"status": "ok"})


@app.route("/api/stats/day/<target_date>", methods=["GET"])
def api_stats_day(target_date):
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = get_daily_summary_data(user_id, target_date)
    entries = get_entries_for_date(user_id, target_date)
    return jsonify({"stats": data, "entries": entries})


@app.route("/api/stats/week/<target_date>", methods=["GET"])
def api_stats_week(target_date):
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = get_weekly_summary_data(user_id, target_date)
    return jsonify(data)


@app.route("/api/stats/month/<int:year>/<int:month>", methods=["GET"])
def api_stats_month(year, month):
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = get_monthly_summary_data(user_id, year, month)
    return jsonify(data)


@app.route("/api/summary", methods=["POST"])
def api_save_summary():
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    period_type = data.get("period_type")
    period_date = data.get("period_date")
    summary_text = data.get("summary_text")

    if not all([period_type, period_date, summary_text]):
        return jsonify({"error": "Missing required fields"}), 400

    if period_type not in ("day", "week", "month"):
        return jsonify({"error": "Invalid period_type"}), 400

    save_summary(user_id, period_type, period_date, summary_text)
    return jsonify({"status": "ok"})


@app.route("/api/summary/<period_type>/<period_date>", methods=["GET"])
def api_get_summary(period_type, period_date):
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    summary = get_summary(user_id, period_type, period_date)
    return jsonify(summary or {"summary_text": ""})


@app.route("/api/user/settings", methods=["GET"])
def api_get_user_settings():
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    user = get_or_create_user(user_id)
    return jsonify({
        "reminder_start_hour": user["reminder_start_hour"],
        "reminder_end_hour": user["reminder_end_hour"],
        "timezone_offset": user["timezone_offset"],
    })


@app.route("/api/user/settings", methods=["POST"])
def api_update_user_settings():
    from database.db import update_user_settings
    user_id = get_user_id_from_request()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    start_h = data.get("reminder_start_hour", 9)
    end_h = data.get("reminder_end_hour", 22)
    tz = data.get("timezone_offset", 3)

    if not (0 <= start_h < end_h <= 23):
        return jsonify({"error": "Invalid hours"}), 400

    update_user_settings(user_id, start_h, end_h, tz)
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    init_db()
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host="0.0.0.0", port=port, debug=debug, use_reloader=False)
