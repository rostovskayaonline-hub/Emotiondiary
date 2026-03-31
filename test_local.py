#!/usr/bin/env python
"""
Quick test script to verify everything works locally
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

def test_database():
    print("🗄️  Testing database...")
    try:
        from database.db import init_db, get_or_create_user, add_emotion_entry, get_entries_for_date
        from datetime import date

        init_db()
        user = get_or_create_user(12345, "testuser", "Test")
        print(f"   ✅ User created/fetched: {user['first_name']}")

        entry_id = add_emotion_entry(12345, "joy", 8, "test entry")
        print(f"   ✅ Entry added: ID {entry_id}")

        entries = get_entries_for_date(12345, date.today().isoformat())
        print(f"   ✅ Entries fetched: {len(entries)} entries")

        return True
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return False


def test_flask():
    print("\n🌐 Testing Flask app...")
    try:
        from database.db import init_db
        from webapp.app import app

        init_db()

        with app.test_client() as client:
            # Test homepage
            r = client.get('/')
            assert r.status_code == 200, f"GET / returned {r.status_code}"
            print(f"   ✅ GET / → 200 OK")

            # Test API: emotions
            r = client.get('/api/emotions')
            assert r.status_code == 200, f"Emotions returned {r.status_code}"
            emotions = r.get_json()
            assert len(emotions) > 0, "No emotions returned"
            print(f"   ✅ GET /api/emotions → {len(emotions)} emotions")

            # Test API: static files
            r = client.get('/static/css/style.css')
            assert r.status_code == 200, f"CSS returned {r.status_code}"
            print(f"   ✅ GET /static/css/style.css → 200 OK")

            r = client.get('/static/js/app.js')
            assert r.status_code == 200, f"JS returned {r.status_code}"
            print(f"   ✅ GET /static/js/app.js → 200 OK")

            # Test API: add entry
            r = client.post('/api/entries',
                json={'emotion': 'joy', 'intensity': 7, 'note': 'test'},
                headers={'X-User-Id': '12345'}
            )
            assert r.status_code == 200, f"POST returned {r.status_code}"
            print(f"   ✅ POST /api/entries → 200 OK")

            # Test API: get entries
            r = client.get('/api/entries/2026-03-31', headers={'X-User-Id': '12345'})
            assert r.status_code == 200, f"GET entries returned {r.status_code}"
            entries = r.get_json()
            print(f"   ✅ GET /api/entries/date → {len(entries)} entries")

            # Test API: stats
            r = client.get('/api/stats/day/2026-03-31', headers={'X-User-Id': '12345'})
            assert r.status_code == 200, f"Stats returned {r.status_code}"
            print(f"   ✅ GET /api/stats/day → 200 OK")

        return True
    except Exception as e:
        print(f"   ❌ Flask error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_env():
    print("\n⚙️  Testing environment...")
    try:
        from dotenv import load_dotenv
        load_dotenv()

        bot_token = os.getenv('BOT_TOKEN', '').strip()
        if bot_token and bot_token != 'your_telegram_bot_token_here':
            print(f"   ✅ BOT_TOKEN is set")
        else:
            print(f"   ⚠️  BOT_TOKEN not configured (set in .env)")

        webapp_url = os.getenv('WEBAPP_URL', '')
        if webapp_url and webapp_url != 'https://your-domain.com':
            print(f"   ✅ WEBAPP_URL is set: {webapp_url}")
        else:
            print(f"   ⚠️  WEBAPP_URL not configured (use http://localhost:5000 for local)")

        print(f"   ✅ Environment variables loaded")
        return True
    except Exception as e:
        print(f"   ❌ Environment error: {e}")
        return False


def main():
    print("=" * 50)
    print("🧪 Emotion Diary - Local Test")
    print("=" * 50)

    results = []
    results.append(("Environment", test_env()))
    results.append(("Database", test_database()))
    results.append(("Flask API", test_flask()))

    print("\n" + "=" * 50)
    print("📊 Test Results")
    print("=" * 50)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} — {name}")

    all_passed = all(r[1] for r in results)

    print("\n" + "=" * 50)
    if all_passed:
        print("✅ All tests passed! Ready to run:")
        print("   Terminal 1: python -m flask --app webapp.app run --port 5000")
        print("   Terminal 2: python -m bot.bot")
        print("   Browser:   http://localhost:5000")
    else:
        print("❌ Some tests failed. Check errors above.")
        sys.exit(1)
    print("=" * 50)


if __name__ == "__main__":
    main()
