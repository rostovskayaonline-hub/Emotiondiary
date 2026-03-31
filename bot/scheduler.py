import logging
import os
import sys
from datetime import datetime, timezone, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database.db import get_all_users

logger = logging.getLogger(__name__)

WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-domain.com")

REMINDER_MESSAGES = [
    "🕐 Как ты сейчас себя чувствуешь? Запиши свои эмоции!",
    "💭 Момент для рефлексии — что ты чувствуешь прямо сейчас?",
    "📝 Время заглянуть в себя. Какие эмоции ты испытываешь?",
    "🌿 Сделай паузу и отметь своё эмоциональное состояние.",
    "✨ Напоминание: запиши, что чувствуешь. Это важно!",
    "🫶 Как дела? Удели минутку своим эмоциям.",
]


async def send_reminders(bot: Bot):
    """Send reminders to all users whose current hour falls within their reminder window."""
    users = get_all_users()
    now_utc = datetime.now(timezone.utc)

    for user in users:
        try:
            offset = user.get("timezone_offset", 3)
            user_time = now_utc + timedelta(hours=offset)
            current_hour = user_time.hour

            start = user.get("reminder_start_hour", 9)
            end = user.get("reminder_end_hour", 22)

            if start <= current_hour <= end:
                # Pick message based on hour for variety
                msg = REMINDER_MESSAGES[current_hour % len(REMINDER_MESSAGES)]

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="📖 Записать эмоцию",
                        web_app=WebAppInfo(url=WEBAPP_URL),
                    )],
                ])

                await bot.send_message(
                    chat_id=user["user_id"],
                    text=msg,
                    reply_markup=keyboard,
                )
                logger.info(f"Reminder sent to user {user['user_id']}")
        except Exception as e:
            logger.error(f"Failed to send reminder to {user['user_id']}: {e}")


def start_scheduler(bot: Bot):
    """Start the APScheduler to send reminders every hour."""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_reminders,
        "cron",
        minute=0,  # Every hour at :00
        args=[bot],
        id="hourly_reminders",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — reminders every hour at :00")
