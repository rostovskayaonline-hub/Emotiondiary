#!/usr/bin/env python
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'bot':
        # Run bot
        import asyncio
        from database.db import init_db
        from bot.bot import main
        init_db()
        asyncio.run(main())
    else:
        # Run Flask (default for Railway web process)
        from database.db import init_db
        from webapp.app import app
        init_db()
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
