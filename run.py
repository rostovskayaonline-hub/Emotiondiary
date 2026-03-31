"""
Entry point to run both the Telegram bot and the Flask web app.
For production, run them separately:
  - Bot: python -m bot.bot
  - Web: gunicorn webapp.app:app -b 0.0.0.0:5000
"""
import asyncio
import threading
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from database.db import init_db


def run_webapp():
    from webapp.app import app
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


async def run_bot():
    from bot.bot import main
    await main()


if __name__ == "__main__":
    init_db()
    print("Starting Emotion Diary...")
    print("Web app: http://localhost:5000")
    print("Bot: polling Telegram...")

    webapp_thread = threading.Thread(target=run_webapp, daemon=True)
    webapp_thread.start()

    asyncio.run(run_bot())
