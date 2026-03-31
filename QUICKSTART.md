# ⚡ Быстрый старт (5 минут)

## Локально на компьютере

### 1️⃣ Получить токен бота
- Напишите [@BotFather](https://t.me/BotFather)
- `/newbot` → назовите бота → скопируйте токен

### 2️⃣ Настроить окружение
```bash
cp .env.example .env
# Отредактируйте .env — замените YOUR_TOKEN_HERE на реальный токен
nano .env
```

### 3️⃣ Установить и запустить
```bash
pip install -r requirements.txt

# Терминал 1: веб-приложение
python -m flask --app webapp.app run --port 5000

# Терминал 2: бот
python -m bot.bot
```

✅ Готово! Откройте в браузере: http://localhost:5000

---

## На Railway (облаке)

### 1️⃣ Загрузить на GitHub
```bash
git add .
git commit -m "Add emotion diary"
git push origin main
```

### 2️⃣ Создать на Railway
1. Откройте https://railway.app/
2. New Project → Deploy from GitHub → выберите репозиторий
3. Railway автоматически обнаружит `requirements.txt` и `Procfile`
4. Дождитесь "Deployment successful"

### 3️⃣ Установить переменные
Railway → Variables → добавьте:
```
BOT_TOKEN=your_token_here
WEBAPP_URL=https://your-project-name.up.railway.app
```

### 4️⃣ Привязать к боту
1. [@BotFather](https://t.me/BotFather) → `/mybots` → ваш бот
2. Bot Settings → Menu Button
3. URL: ваш Railway URL
4. Done!

✅ Готово! Кнопка появится в боте.

---

## 📝 Как использовать

**Вкладки в мини-приложении:**

1. **✏️ Запись** — выберите эмоцию, интенсивность 1-10, добавьте заметку
2. **📋 История** — все записи за день с таймлайном
3. **📊 Графики** — аналитика (день/неделя/месяц)
4. **📝 Итоги** — подведение итогов с подсказками для рефлексии

**Бот командует:**
- `/start` — кнопка "Открыть дневник"
- `/settings` — выбрать время напоминаний
- `/today` — записи за сегодня

---

## 🐛 Если что-то не работает

| Проблема | Решение |
|----------|---------|
| "Cannot GET /" | Убедитесь что Flask запущен на порте 5000 |
| Графики пусты | Сначала добавьте записи эмоций |
| 502 ошибка на Railway | Проверьте Railway → Logs (Settings → Raw logs) |
| Напоминания не приходят | Используйте `/settings` чтобы выбрать время |

---

## 📚 Полная инструкция
Смотрите [SETUP.md](SETUP.md) для развёрнутого гайда.
