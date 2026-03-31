# 📖 Полная инструкция по настройке — Дневник эмоций

## Обзор проекта

Это полноценное Telegram Mini App для ведения дневника эмоций с:
- 🤖 Telegram-ботом с ежечасными напоминаниями
- 📱 Mini App интерфейсом в Telegram
- 📊 Графиками и аналитикой эмоций
- 💭 Инструментом для рефлексии и подведения итогов

---

## 📋 Содержание
1. [Локальная разработка](#локальная-разработка)
2. [Развёртывание на Railway](#развёртывание-на-railway)
3. [Конфигурация Telegram-бота](#конфигурация-telegram-бота)
4. [Структура проекта](#структура-проекта)
5. [Troubleshooting](#troubleshooting)

---

## Локальная разработка

### Шаг 1: Подготовка окружения

```bash
# Клонируем репозиторий
git clone <repo-url> && cd Emotiondiary

# Создаём виртуальное окружение (опционально, но рекомендуется)
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

# Устанавливаем зависимости
pip install -r requirements.txt
```

### Шаг 2: Создание Telegram-бота

1. **Откройте [@BotFather](https://t.me/BotFather)** в Telegram
2. **Создайте нового бота**: отправьте `/newbot`
   - Укажите имя: например "Emotion Diary Bot"
   - Укажите username: например `emotion_diary_bot`
3. **Скопируйте токен** (выглядит как `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### Шаг 3: Настройка переменных окружения

```bash
# Копируем пример конфигурации
cp .env.example .env

# Редактируем .env
nano .env
```

Содержимое `.env`:
```ini
# Токен бота из BotFather
BOT_TOKEN=YOUR_TOKEN_HERE

# URL вашего мини-приложения (для локальной разработки — ngrok или localhost)
WEBAPP_URL=http://localhost:5000

# Время напоминаний (9:00 - 22:00)
REMINDER_START_HOUR=9
REMINDER_END_HOUR=22
```

### Шаг 4: Инициализация БД и запуск

```bash
# Инициализирует SQLite БД (emotion_diary.db)
python -c "from database.db import init_db; init_db(); print('DB initialized')"

# Запускаем Flask (в одном терминале)
python -m flask --app webapp.app run --port 5000

# Или через gunicorn (для прода):
gunicorn webapp.app:app -b 0.0.0.0:5000

# В другом терминале запускаем бота
python -m bot.bot
```

**Результат:**
- Flask слушает на `http://localhost:5000`
- Bot подключается к Telegram и ждёт сообщений

### Шаг 5: Тестирование локально

1. **Откройте в браузере**: `http://localhost:5000`
   - Должны увидеть интерфейс дневника
   - Шапка: "Что ты чувствуешь?"
   - Кнопки эмоций, слайдер интенсивности

2. **Тест API (в другом терминале)**:
```bash
# Получить список эмоций
curl http://localhost:5000/api/emotions

# Добавить запись (тестовый пользователь ID=12345)
curl -X POST http://localhost:5000/api/entries \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 12345" \
  -d '{"emotion":"joy","intensity":7,"note":"Отличный день!"}'

# Получить записи за дату
curl http://localhost:5000/api/entries/2026-03-31 \
  -H "X-User-Id: 12345"

# Получить статистику дня
curl http://localhost:5000/api/stats/day/2026-03-31 \
  -H "X-User-Id: 12345"
```

3. **Тест бота**:
   - Откройте своего бота в Telegram
   - `/start` — приветствие + кнопка "Открыть дневник"
   - `/settings` — настройка времени напоминаний
   - `/help` — список команд

---

## Развёртывание на Railway

Railway.app — простой хостинг для Python приложений. **Все зависимости автоматические!**

### Шаг 1: Подготовка репозитория

Убедитесь, что в корне проекта есть:
- ✅ `requirements.txt` — список зависимостей
- ✅ `Procfile` — конфигурация процессов
- ✅ `runtime.txt` (опционально) — версия Python

Проверим содержимое `Procfile`:
```
web: gunicorn webapp.app:app
worker: python -m bot.bot
```

### Шаг 2: Загрузка на Railway

**Вариант 1: Через GitHub (рекомендуется)**

```bash
# 1. Загружаем код на GitHub
git push origin main

# 2. Заходим на https://railway.app/
# 3. Регистрируемся или входим
# 4. Создаём новый проект → "Deploy from GitHub"
# 5. Выбираем репозиторий Emotiondiary
# 6. Railway автоматически обнаружит requirements.txt
```

**Вариант 2: Через Railway CLI**

```bash
# Устанавливаем Railway CLI
npm install -g @railway/cli
# или через curl: https://docs.railway.app/guides/cli

# Логинимся
railway login

# Создаём проект
railway init

# Деплоим
railway up
```

### Шаг 3: Настройка окружения на Railway

После создания проекта на Railway.app:

1. **Откройте Settings → Variables**
2. **Добавьте переменные окружения**:
   ```
   BOT_TOKEN=your_token_here
   WEBAPP_URL=https://your-project-name.up.railway.app
   REMINDER_START_HOUR=9
   REMINDER_END_HOUR=22
   ```

3. **Нажмите Deploy** → Railway автоматически пересоберёт приложение

**Проверить статус:**
- Railway.app → Logs → "Build successful"
- Откройте URL: `https://your-project-name.up.railway.app`
- Должны увидеть интерфейс дневника

---

## Конфигурация Telegram-бота

### Привязка Mini App к боту

Чтобы кнопка "Открыть дневник" открывала ваше веб-приложение:

1. **Откройте BotFather**: `@BotFather`
2. **Команда**: `/mybots`
3. **Выберите вашего бота**
4. **Bot Settings → Menu Button**
5. **Укажите**:
   - Text: "📖 Открыть дневник" (или любой другой)
   - URL: `https://your-project-name.up.railway.app` (ваш Railway URL)
6. **Done**

Теперь при открытии бота будет кнопка "Открыть дневник" внизу — она откроет Mini App.

### Команды бота

Бот автоматически поддерживает команды:

```
/start         — Приветствие, показать кнопку Mini App
/diary         — Открыть дневник (кнопка)
/today         — Показать записи за сегодня
/settings      — Настроить время напоминаний
/help          — Справка и список команд
```

### Напоминания

- **Работают автоматически** — bot process на Railway отправляет сообщения каждый час
- **Время настраивается через `/settings`** — выбираете начало и конец дня
- **Каждый час** в промежутке 9:00-22:00 (по умолчанию) пользователь получит напоминание с кнопкой

---

## Структура проекта

```
Emotiondiary/
├── bot/
│   ├── __init__.py
│   ├── bot.py              # Telegram-бот (aiogram)
│   │                        # Команды: /start, /settings, /today, /diary, /help
│   │                        # Обработка сообщений, управление напоминаниями
│   └── scheduler.py         # APScheduler для ежечасных напоминаний
│
├── webapp/
│   ├── __init__.py
│   ├── app.py              # Flask приложение + API
│   │                        # API endpoints: /api/emotions, /api/entries, /api/stats, /api/summary
│   │                        # Валидация Telegram initData для безопасности
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css   # Стили (responsive для мобильного)
│   │   │                    # Переменные CSS (--tg-theme-*)
│   │   │                    # Компоненты: карточки, кнопки, слайдеры, графики
│   │   └── js/
│   │       └── app.js      # Фронтенд логика (~600 строк)
│   │                        # Навигация, управление записями, графики (Chart.js)
│   │                        # Форматирование дат, валидация
│   └── templates/
│       └── index.html      # HTML структура Mini App
│                            # 4 вкладки: запись, история, графики, итоги
│
├── database/
│   ├── __init__.py
│   └── db.py               # SQLite модели + запросы
│                            # Таблицы: users, emotion_entries, summaries
│                            # Функции для CRUD операций и аналитики
│
├── .env.example            # Пример конфигурации
├── .gitignore             # Исключение из гита (*.db, .env, venv/)
├── requirements.txt        # Зависимости Python
├── Procfile               # Конфигурация для Railway/Heroku
├── main.py                # Альтернативный точка входа
├── run.py                 # Локальный запуск (bot + flask вместе)
├── README.md              # Краткое описание
└── SETUP.md               # Эта инструкция
```

### Основные технологии

| Слой | Технология | Версия |
|------|-----------|--------|
| Bot | aiogram | 3.4.1 |
| Scheduler | APScheduler | 3.10.4 |
| Web Framework | Flask | 3.0.0 |
| Charts | Chart.js | 4.4.1 |
| Database | SQLite | (встроённая в Python) |
| Server | Gunicorn | 21.2.0 |
| CORS | Flask-CORS | 4.0.0 |

---

## API Endpoints

### Эмоции
```
GET /api/emotions
Returns: [{"id": "joy", "name": "Радость", "emoji": "😊", "color": "#FFD93D"}, ...]
```

### Записи эмоций
```
POST /api/entries
Body: {"emotion": "joy", "intensity": 7, "note": "optional text"}
Returns: {"id": 1, "status": "ok"}

GET /api/entries/{date}
Params: date in YYYY-MM-DD format (e.g. 2026-03-31)
Returns: [{"id": 1, "emotion": "joy", "intensity": 7, "note": "...", "created_at": "..."}, ...]

DELETE /api/entries/{id}
Returns: {"status": "ok"}
```

### Статистика
```
GET /api/stats/day/{date}
Returns: {"stats": [...], "entries": [...]}

GET /api/stats/week/{date}
Returns: {"start": "...", "end": "...", "daily_data": {...}, "overall": [...], "total_entries": 5}

GET /api/stats/month/{year}/{month}
Returns: {"start": "...", "end": "...", "daily_data": {...}, "overall": [...], "total_entries": 42}
```

### Итоги/Рефлексия
```
POST /api/summary
Body: {"period_type": "day|week|month", "period_date": "2026-03-31", "summary_text": "..."}
Returns: {"status": "ok"}

GET /api/summary/{period_type}/{period_date}
Returns: {"summary_text": "..."} или {"summary_text": ""}
```

---

## Troubleshooting

### ❌ "Сайт не открывается" / 502 Bad Gateway на Railway

**Причины:**
1. **Bot process крашится** — проверьте логи Railway → Logs
2. **БД не инициализирована** — добавьте в `webapp/app.py` call `init_db()`
3. **PORT не прочитана** — используйте `int(os.getenv('PORT', 5000))`

**Решение:**
```bash
# На локальной машине
python -c "from database.db import init_db; init_db()"

# Пушим в Railway
git push origin main

# Проверяем логи Railway
# Settings → Raw Logs (внизу)
```

### ❌ "Записи сохраняются, но графики не показывают"

**Проблема:** В JavaScript происходит ошибка при загрузке данных

**Решение:**
```javascript
// Откройте DevTools (F12) → Console
// Ищите красные ошибки вроде "Cannot read property 'entries'"
// Проверьте что API возвращает данные:
// Network → /api/stats/day/* → Response
```

### ❌ "Напоминания не приходят"

**Проверьте:**
1. **Bot процесс запущен** на Railway (должен быть отдельный worker)
2. **Время настроено** — используйте `/settings` в боте
3. **Часовой пояс** — в БД есть поле `timezone_offset` (по умолчанию 3 для UTC+3)

**Изменить часовой пояс:**
```python
# В database/db.py, функция update_user_settings
update_user_settings(user_id, 9, 22, timezone_offset=5)  # UTC+5
```

### ❌ "Mini App не открывается из бота"

**Проверьте:**
1. **WEBAPP_URL настроен** в `.env` (должен быть HTTPS для продакшена)
2. **Menu Button настроен** у BotFather → Bot Settings → Menu Button → URL
3. **URL доступен** — откройте в браузере вручную

### ❌ "Ошибка: 'X-Telegram-Init-Data' header not valid"

**Для разработки используйте:**
```javascript
// app.js по умолчанию использует X-User-Id для локального тестирования
// Если разрабатываете в Mini App, убедитесь что:
// 1. Открываете через кнопку "Открыть дневник" в боте
// 2. Не открываете напрямую в браузере
```

### ❌ "График не загружается / пустой"

**Причины:**
1. **Нет данных** — сначала добавьте записи через "Запись" вкладку
2. **Chart.js не загружен** — проверьте Network → cdn.jsdelivr.net

**Дебаг:**
```javascript
// DevTools → Console
console.log(emotions);      // Должны быть эмоции
console.log(data.entries);  // Должны быть записи
console.log(chartInstance);  // Должен быть объект Chart
```

---

## Часто задаваемые вопросы

### Q: Как изменить список эмоций?
**A:** Отредактируйте `EMOTIONS` в `database/db.py` (16 эмоций с emoji и цветами)

### Q: Где хранятся данные?
**A:** В файле `emotion_diary.db` (SQLite) в корне проекта. На Railway БД сохраняется в памяти (теряется при перезагрузке) — для постоянного хранения подключите PostgreSQL

### Q: Как добавить своё имя вместо "ты"?
**A:** В `webapp/templates/index.html` измените:
```html
<div class="page-header">Что ты чувствуешь?</div>
<!-- на -->
<div class="page-header">Что чувствуешь, Маша?</div>
```

### Q: Как изменить тему цветов?
**A:** CSS переменные в `webapp/static/css/style.css`:
```css
:root {
    --accent: var(--tg-theme-button-color, #5B68E0);  /* Основной цвет */
    --bg-primary: var(--tg-theme-bg-color, #ffffff);   /* Фон */
    /* ... */
}
```
Или отредактируйте строку `--tg-theme-*` для темы Telegram

### Q: Как использовать PostgreSQL вместо SQLite?
**A:** Измените `database/db.py`:
```python
import psycopg2
conn = psycopg2.connect("postgresql://user:password@host/db")
```
На Railway просто добавьте PostgreSQL plugin → он создаст переменную `DATABASE_URL`

### Q: Безопасен ли код?
**A:** Да, используется:
- ✅ HMAC-SHA256 валидация Telegram initData
- ✅ Escape HTML для предотвращения XSS
- ✅ SQL-параметризованные запросы (защита от SQL injection)
- ✅ CORS настроен правильно

---

## 🚀 Что дальше?

После запуска можно добавить:
- 📲 Push-уведомления вместо HTTP напоминаний
- 📈 Экспорт данных в CSV/PDF
- 🔒 Аутентификация и синхронизация между устройствами
- 🎯 Целей и привычки связанные с эмоциями
- 🧠 AI рекомендации на основе паттернов
- 📤 Шаринг статистики в соцсети

---

## 📞 Поддержка

Если что-то не работает:
1. Проверьте **Railway Logs** (Settings → Raw Logs)
2. Откройте **DevTools** в браузере (F12 → Console/Network)
3. Убедитесь что все переменные окружения установлены (`.env`)
4. Попробуйте локально запустить (`python -m bot.bot` + `python -m flask --app webapp.app run`)

**Успехов в разработке! 🎉**
