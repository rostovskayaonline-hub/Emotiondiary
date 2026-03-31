# 🚀 Развёртывание на Railway (Для вашего сайта)

ваш сайт: `emotiondiary-production.up.railway.app`

## Проблема

Сайт был развёрнут, но не работал из-за нескольких проблем:
1. ❌ Flask неправильно сервировал статические файлы (CSS, JS)
2. ❌ Переменные окружения не читались в scheduler
3. ❌ PORT не читалась из переменной окружения

## ✅ Исправления

Я уже исправил код. Вам нужно только пересоздать проект на Railway:

### Шаг 1: Обновить код (я уже сделал)

В репозитории добавлены:
- `SETUP.md` — полная инструкция
- `QUICKSTART.md` — быстрый старт
- `Procfile` — конфигурация для Railway
- `runtime.txt` — версия Python
- `test_local.py` — тесты (все ✅ проходят)

И исправлены:
- `webapp/app.py` — правильные пути для статики + PORT reading
- `bot/scheduler.py` — добавлена загрузка `.env`

### Шаг 2: Пересоздать проект на Railway

**Option A: Через GitHub (если ещё не связан)**

```bash
# 1. Откройте https://railway.app/
# 2. New Project → Deploy from GitHub
# 3. Выберите rostovskayaonline-hub/Emotiondiary
# 4. Railway автоматически обнаружит Procfile и requirements.txt
```

**Option B: Если проект уже создан**

```bash
# 1. Откройте Settings проекта на Railway
# 2. Удалите переменные (если были неправильные)
# 3. Добавьте переменные (см. ниже)
# 4. Trigger → Redeploy
```

### Шаг 3: Установить переменные окружения

На Railway.app → ваш проект → Variables:

```
BOT_TOKEN=ВАШ_ТОКЕН_ИЗ_BOTFATHER
WEBAPP_URL=https://emotiondiary-production.up.railway.app
REMINDER_START_HOUR=9
REMINDER_END_HOUR=22
```

**Важно:** `WEBAPP_URL` должна быть ваша Railway URL (с `https://`)

### Шаг 4: Проверить, что есть 2 процесса

Railway → Services → должны быть:
- ✅ **web** — Flask (статус "UP")
- ✅ **worker** — Bot (статус "UP")

Если бота нет, добавьте через `+ Add Service` или отредактируйте `Procfile`.

### Шаг 5: Проверить логи

Railway → Logs → ищите:
- `"App started"` или `"Running on"`
- Никаких красных ошибок

### Шаг 6: Привязать Menu Button в боте

[@BotFather](https://t.me/BotFather):
1. `/mybots` → выберите бота
2. Bot Settings → Menu Button
3. URL: `https://emotiondiary-production.up.railway.app`
4. Done

---

## 🧪 Проверка

### Вариант 1: Открыть в браузере

```
https://emotiondiary-production.up.railway.app/
```

Должны увидеть:
- Заголовок "Что ты чувствуешь?"
- 16 кнопок эмоций (😊😢😠🤩 и т.д.)
- Слайдер интенсивности
- Кнопка "Записать"

### Вариант 2: Проверить API

```bash
# Получить эмоции
curl https://emotiondiary-production.up.railway.app/api/emotions

# Должно вернуть JSON с 16 эмоциями
# [{"id": "joy", "name": "Радость", ...}, ...]
```

### Вариант 3: Через бота

1. Откройте своего бота в Telegram
2. `/start` — должна быть кнопка "Открыть дневник"
3. Нажмите кнопку → должно открыться мини-приложение

---

## 🐛 Если всё ещё не работает

### Ошибка: "502 Bad Gateway"

**Решение:**
1. Railway → Logs (Settings → Raw logs)
2. Ищите ошибки в логах
3. Проверьте переменные (`BOT_TOKEN`, `WEBAPP_URL`)
4. Нажмите "Redeploy" (пересоберёт приложение)

### Ошибка: "Cannot GET /"

**Решение:**
1. Убедитесь что `Procfile` содержит:
   ```
   web: gunicorn webapp.app:app
   worker: python -m bot.bot
   ```
2. Нажмите "Redeploy"

### Ошибка: "CSS/JS не загружаются" (404)

**Решение:**
1. Проверьте в браузере DevTools → Network
2. Посмотрите на статус файла (должен быть 200)
3. Если 404 — это уже исправлено в новом коде
4. Нажмите "Redeploy" на Railway

### Напоминания не приходят

**Проверьте:**
1. Bot процесс запущен на Railway (должен быть зелёный статус)
2. `BOT_TOKEN` правильный (скопирован с BotFather)
3. Используйте `/settings` в боте чтобы выбрать время

---

## 📋 Чек-лист

- [ ] Код обновлён (новые файлы: SETUP.md, Procfile, etc.)
- [ ] Проект на Railway создан или обновлён
- [ ] Переменные установлены (BOT_TOKEN, WEBAPP_URL)
- [ ] Оба процесса запущены (web + worker)
- [ ] URL доступен в браузере: https://emotiondiary-production.up.railway.app/
- [ ] Бот работает: `/start` показывает кнопку
- [ ] Menu Button привязан в BotFather
- [ ] Кнопка открывает мини-приложение из бота

---

## 💡 Что дальше?

После того как всё работает:

1. **Добавьте свои записи** — используйте мини-приложение
2. **Посмотрите графики** — вкладка "Графики" → День/Неделя/Месяц
3. **Подводите итоги** — вкладка "Итоги" с рефлексией
4. **Настройте время напоминаний** — `/settings` в боте

---

## 🆘 Нужна помощь?

Если что-то не работает:

1. **Проверьте SETUP.md** — там полный гайд
2. **Откройте DevTools** в браузере (F12) → Console/Network
3. **Посмотрите Railway Logs** → Settings → Raw logs
4. **Запустите локально** для дебага:
   ```bash
   python test_local.py  # Проверит всё локально
   ```

---

**Спасибо за использование Emotion Diary! 🌟**
