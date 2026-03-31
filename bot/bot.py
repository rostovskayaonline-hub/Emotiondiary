import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
    MenuButtonWebApp,
)
from aiogram.enums import ParseMode
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from database.db import init_db, get_or_create_user, update_user_settings, get_entries_for_date, EMOTIONS
from bot.scheduler import start_scheduler

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-domain.com")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user = get_or_create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📖 Открыть дневник эмоций",
            web_app=WebAppInfo(url=WEBAPP_URL),
        )],
        [InlineKeyboardButton(
            text="⚙️ Настройки напоминаний",
            callback_data="settings",
        )],
    ])

    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        "Я — твой дневник эмоций. Помогу тебе отслеживать и понимать свои чувства.\n\n"
        "🔹 Нажми кнопку ниже, чтобы открыть дневник\n"
        "🔹 Я буду напоминать тебе каждый час записать свои эмоции\n"
        f"🔹 Сейчас напоминания настроены с {user['reminder_start_hour']}:00 до {user['reminder_end_hour']}:00\n\n"
        "Используй /help для списка команд.",
        reply_markup=keyboard,
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📋 <b>Команды:</b>\n\n"
        "/start — Начать работу с ботом\n"
        "/diary — Открыть дневник эмоций\n"
        "/today — Посмотреть записи за сегодня\n"
        "/settings — Настроить напоминания\n"
        "/help — Показать эту справку",
        parse_mode=ParseMode.HTML,
    )


@dp.message(Command("diary"))
async def cmd_diary(message: types.Message):
    get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📖 Открыть дневник эмоций",
            web_app=WebAppInfo(url=WEBAPP_URL),
        )],
    ])
    await message.answer("Нажми кнопку, чтобы открыть дневник:", reply_markup=keyboard)


@dp.message(Command("today"))
async def cmd_today(message: types.Message):
    from datetime import date
    user_id = message.from_user.id
    get_or_create_user(user_id, message.from_user.username, message.from_user.first_name)

    entries = get_entries_for_date(user_id, date.today().isoformat())

    if not entries:
        await message.answer("Сегодня ещё нет записей. Время сделать первую! 📝")
        return

    emotions_map = {e["id"]: e for e in EMOTIONS}
    text = f"📊 <b>Записи за {date.today().strftime('%d.%m.%Y')}:</b>\n\n"

    for entry in entries:
        emo_info = emotions_map.get(entry["emotion"], {})
        emoji = emo_info.get("emoji", "❓")
        name = emo_info.get("name", entry["emotion"])
        time_str = entry["created_at"][11:16]
        text += f"{emoji} <b>{name}</b> — {entry['intensity']}/10 ({time_str})\n"
        if entry.get("note"):
            text += f"   💬 {entry['note']}\n"
        text += "\n"

    text += f"Всего записей: {len(entries)}"
    await message.answer(text, parse_mode=ParseMode.HTML)


@dp.message(Command("settings"))
async def cmd_settings(message: types.Message):
    user = get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.first_name)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️", callback_data="start_minus"),
            InlineKeyboardButton(text=f"Начало: {user['reminder_start_hour']}:00", callback_data="noop"),
            InlineKeyboardButton(text="➡️", callback_data="start_plus"),
        ],
        [
            InlineKeyboardButton(text="⬅️", callback_data="end_minus"),
            InlineKeyboardButton(text=f"Конец: {user['reminder_end_hour']}:00", callback_data="noop"),
            InlineKeyboardButton(text="➡️", callback_data="end_plus"),
        ],
        [InlineKeyboardButton(text="✅ Готово", callback_data="settings_done")],
    ])

    await message.answer(
        "⚙️ <b>Настройки напоминаний</b>\n\n"
        "Выбери время начала и конца напоминаний.\n"
        "Бот будет напоминать тебе каждый час в этот промежуток.",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


@dp.callback_query(F.data == "settings")
async def cb_settings(callback: types.CallbackQuery):
    user = get_or_create_user(callback.from_user.id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️", callback_data="start_minus"),
            InlineKeyboardButton(text=f"Начало: {user['reminder_start_hour']}:00", callback_data="noop"),
            InlineKeyboardButton(text="➡️", callback_data="start_plus"),
        ],
        [
            InlineKeyboardButton(text="⬅️", callback_data="end_minus"),
            InlineKeyboardButton(text=f"Конец: {user['reminder_end_hour']}:00", callback_data="noop"),
            InlineKeyboardButton(text="➡️", callback_data="end_plus"),
        ],
        [InlineKeyboardButton(text="✅ Готово", callback_data="settings_done")],
    ])

    await callback.message.edit_text(
        "⚙️ <b>Настройки напоминаний</b>\n\n"
        "Выбери время начала и конца напоминаний.\n"
        "Бот будет напоминать тебе каждый час в этот промежуток.",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )
    await callback.answer()


@dp.callback_query(F.data.in_({"start_minus", "start_plus", "end_minus", "end_plus"}))
async def cb_adjust_time(callback: types.CallbackQuery):
    user = get_or_create_user(callback.from_user.id)
    start_h = user["reminder_start_hour"]
    end_h = user["reminder_end_hour"]

    if callback.data == "start_minus" and start_h > 0:
        start_h -= 1
    elif callback.data == "start_plus" and start_h < end_h - 1:
        start_h += 1
    elif callback.data == "end_minus" and end_h > start_h + 1:
        end_h -= 1
    elif callback.data == "end_plus" and end_h < 23:
        end_h += 1

    update_user_settings(callback.from_user.id, start_h, end_h, user["timezone_offset"])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️", callback_data="start_minus"),
            InlineKeyboardButton(text=f"Начало: {start_h}:00", callback_data="noop"),
            InlineKeyboardButton(text="➡️", callback_data="start_plus"),
        ],
        [
            InlineKeyboardButton(text="⬅️", callback_data="end_minus"),
            InlineKeyboardButton(text=f"Конец: {end_h}:00", callback_data="noop"),
            InlineKeyboardButton(text="➡️", callback_data="end_plus"),
        ],
        [InlineKeyboardButton(text="✅ Готово", callback_data="settings_done")],
    ])

    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data == "settings_done")
async def cb_settings_done(callback: types.CallbackQuery):
    user = get_or_create_user(callback.from_user.id)
    await callback.message.edit_text(
        f"✅ Напоминания настроены: с {user['reminder_start_hour']}:00 до {user['reminder_end_hour']}:00\n"
        "Я буду напоминать тебе каждый час записать свои эмоции.",
    )
    await callback.answer("Сохранено!")


@dp.callback_query(F.data == "noop")
async def cb_noop(callback: types.CallbackQuery):
    await callback.answer()


async def main():
    init_db()
    start_scheduler(bot)
    logger.info("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
