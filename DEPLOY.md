# Деплой на Render

Проект настроен для деплоя на **Render** (подходит и для будущих проектов с OpenAI — ключ можно добавить в Environment Variables).

---

## Вариант 1: Деплой по Blueprint (рекомендуется)

1. Залейте в репозиторий все изменения (включая `requirements.txt`, `render.yaml`, правки в `app.py`):
   ```bash
   git add requirements.txt render.yaml app.py
   git commit -m "Add Render deploy config"
   git push
   ```

2. Зайдите на **https://render.com** и войдите (через GitHub удобнее).

3. В Dashboard нажмите **New +** → **Blueprint**.

4. Подключите репозиторий **annarybkina-bot/allio_prices** (если ещё не подключён — авторизуйте GitHub и выберите этот репозиторий).

5. Render подхватит `render.yaml` из корня. Нажмите **Apply**.

6. Дождитесь сборки и деплоя (2–5 минут). В логах не должно быть ошибок.

7. Откройте ссылку вида **https://allio-prices.onrender.com** (или как в карточке сервиса).

---

## Вариант 2: Ручное создание Web Service

1. **New +** → **Web Service**.

2. Подключите репозиторий **allio_prices**.

3. Настройки:
   - **Name:** `allio-prices` (или любое).
   - **Region:** ближайший (например Frankfurt).
   - **Branch:** `main`.
   - **Runtime:** Python 3.
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT app:app`

4. **Plan:** Free.

5. **Create Web Service**. Дождитесь деплоя и откройте выданный URL.

---

## Переменные окружения (для будущего проекта с OpenAI)

В карточке сервиса: **Environment** → **Add Environment Variable**:

- **Key:** `OPENAI_API_KEY`
- **Value:** ваш ключ из кабинета OpenAI

После сохранения Render перезапустит сервис. В коде используйте `os.environ.get('OPENAI_API_KEY')`.

---

## Ограничения бесплатного плана Render

- Сервис «засыпает» после ~15 минут без запросов; первый запрос после сна может идти 30–60 секунд.
- Есть лимиты по времени работы в месяц (достаточно для тестов и демо).

Для постоянной работы без «сна» нужен платный план.
