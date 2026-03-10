# Розгортання та налаштування (включно з MCP)

Цей документ описує кроки розгортання weather-agent та налаштування всіх опційних компонентів: змінні оточення, Google Calendar (LangChain Toolkit), MCP (Model Context Protocol) та історична погода (RAG/ChromaDB).

---

## 1. Мінімальне розгортання (без календаря та MCP)

Щоб запустити бота лише з погодою та історичною погодою (без календаря):

1. **Клонуйте репозиторій і перейдіть у каталог проєкту.**

2. **Створіть віртуальне середовище та встановіть залежності:**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/macOS
   # або: venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Налаштуйте `.env`:**
   ```bash
   cp .env.example .env
   ```
   Відкрийте `.env` і заповніть обов’язкові поля:
   - **TELEGRAM_BOT_TOKEN** — токен від [@BotFather](https://t.me/BotFather).
   - **OPENAI_API_KEY** — ключ з [OpenAI](https://platform.openai.com/api-keys).

4. **Запуск:**
   ```bash
   python main.py
   ```
   Або через Make: `make install` потім `make run`.

Бот працює в режимі long polling і відповідає на текстові повідомлення. Рекомендації по одягу базуються на поточній погоді (Open-Meteo); при `PROMPT_VERSION=3` доступна також історична погода (RAG), якщо попередньо виконати `make historical-build`.

---

## 2. Змінні оточення (повний список)

Усі змінні зчитуються з `.env` (або з середовища). Нижче — повний перелік і призначення.

| Змінна | Обов’язкова | Опис |
|--------|-------------|------|
| **TELEGRAM_BOT_TOKEN** | Так | Токен Telegram-бота від @BotFather. |
| **OPENAI_API_KEY** | Так | Ключ API OpenAI для LLM. |
| **DEFAULT_MODEL** | Ні | Модель OpenAI (за замовчуванням `gpt-4o-mini`). |
| **PROMPT_VERSION** | Ні | Версія системного промпта: `1`, `2` або `3`. `3` — з історичною погодою та календарем. |
| **GOOGLE_CALENDAR_CREDENTIALS_PATH** | Ні | Шлях до `credentials.json` (Google Calendar API). Потрібен для інтеграції з календарем через LangChain Toolkit. |
| **GOOGLE_CALENDAR_TOKEN_PATH** | Ні | Шлях до `token.json` (зберігається після першої OAuth-авторизації). |
| **MCP_ENDPOINT** | Ні | URL HTTP-endpoint MCP-сервера. Використовується лише якщо ви підключаєте додаткові MCP-інструменти (не календар — календар йде через LangChain Toolkit). |
| **MCP_TIMEOUT_SECONDS** | Ні | Таймаут запитів до MCP (за замовчуванням `10`). |
| **CHROMA_PERSIST_DIR** | Ні | Каталог для ChromaDB (історична погода). За замовчуванням `chroma_langchain_db`. |
| **CHROMA_COLLECTION_NAME** | Ні | Ім’я колекції Chroma. За замовчуванням `historical_weather`. |
| **OPENAI_EMBEDDING_MODEL** | Ні | Модель для embedding при побудові RAG. За замовчуванням `text-embedding-3-small`. |

Файл `.env` не комітиться в репозиторій; шаблон — `.env.example`.

---

## 3. Налаштування Google Calendar (LangChain Toolkit)

Календар у проєкті підключений через **офіційний LangChain Google Calendar Toolkit**, а не через MCP. Агент отримує інструменти типу пошуку подій, поточної дати/часу тощо без окремого MCP-сервера.

### Крок 1: Google Cloud Console

1. Перейдіть у [Google Cloud Console](https://console.cloud.google.com/).
2. Створіть проєкт (або оберіть існуючий).
3. Увімкніть **Google Calendar API**: APIs & Services → Enable APIs and Services → знайдіть «Google Calendar API» → Enable.
4. Створіть облікові дані для «Desktop app»:
   - APIs & Services → Credentials → Create Credentials → OAuth client ID.
   - Application type: **Desktop app**.
   - Завантажте JSON-файл і збережіть його як `credentials.json` у зручному каталозі (наприклад, корінь проєкту).

Детальна інструкція: [Google Calendar API quickstart (Python)](https://developers.google.com/calendar/api/quickstart/python#authorize_credentials_for_a_desktop_application).

### Крок 2: Локальні файли

- **credentials.json** — вже маєте після кроку 1.
- **token.json** — створюється автоматично при першому запуску, коли бот звертається до календаря; відкриється браузер для входу в Google-акаунт. Зберігайте цей файл у безпечному місці і не комітьте його в репозиторій.

### Крок 3: Змінні оточення

У `.env` додайте (або розкоментуйте та вкажіть реальні шляхи):

```env
GOOGLE_CALENDAR_CREDENTIALS_PATH=./credentials.json
GOOGLE_CALENDAR_TOKEN_PATH=./token.json
```

Якщо не вказати шляхи, `CalendarToolkit` намагатиметься знайти `credentials.json` у поточному каталозі (поведінка за замовчуванням з [документації LangChain](https://docs.langchain.com/oss/python/integrations/tools/google_calendar)).

### Крок 4: Запуск з календарем

1. Запустіть бота з промптом версії 3: `make run PROMPT_VERSION=3` або `PROMPT_VERSION=3 python main.py`.
2. При першому зверненні до календаря може відкритися браузер для авторизації; після цього з’явиться `token.json`.
3. Далі агент зможе враховувати події з вашого календаря в рекомендаціях (наприклад: «Сьогодні в мене зустріч о 18:00 в центрі Києва — що вдягнути?»).

---

## 4. MCP (Model Context Protocol): коли і як налаштовувати

### Що таке MCP у цьому проєкті

- **MCP (Model Context Protocol)** — протокол для підключення зовнішніх інструментів (tools) до агентів. У коді є модуль `src/weather_agent/mcp/`: клієнт (`client.py`) та інструменти поверх MCP (`tools.py`).
- **Зараз календар у weather-agent не використовує MCP.** Календар підключений через LangChain Google Calendar Toolkit (прямі виклики Google Calendar API). MCP у проєкті залишено для можливих майбутніх інтеграцій (інші MCP-сервери: нотифікації, таски, тощо).

### Коли потрібно налаштовувати MCP

Налаштовуйте MCP лише якщо ви:

- піднімаєте **окремий MCP-сервер** (наприклад, сторонній сервер з інструментами);
- хочете, щоб агент викликав саме цей сервер (через HTTP JSON-RPC).

Якщо вам потрібен лише **Google Calendar** — достатньо налаштування з розділу 3 (LangChain Toolkit), MCP-сервер для календаря не потрібен.

### Як налаштувати MCP (якщо ви використовуєте зовнішній MCP-сервер)

1. **Запустіть MCP-сервер** окремо (згідно з його документацією). Припустимо, він віддає HTTP-endpoint, наприклад `http://localhost:8080/mcp` або `http://your-server:3000`.

2. **Додайте в `.env`:**
   ```env
   MCP_ENDPOINT=http://localhost:8080/mcp
   MCP_TIMEOUT_SECONDS=10
   ```

3. **Підключення до агента.** За зараз агент у `agent.py` використовує лише LangChain Calendar Toolkit і не підключає інструменти з `weather_agent.mcp.tools` автоматично. Щоб знову використовувати MCP-інструменти (наприклад, `get_calendar_events` з MCP-сервера), потрібно в `agent.py` додати ці tools до списку інструментів агента і переконатися, що ваш MCP-сервер реалізує очікувані методи (наприклад, `tools/list`, `tools/call` у форматі JSON-RPC, як у `mcp/client.py`).

4. **Перевірка:** переконайтеся, що MCP-сервер доступний за вказаним URL (наприклад, `curl -X POST "$MCP_ENDPOINT" -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":"1","method":"tools/list","params":{}}'`).

### Підсумок по MCP

| Сценарій | Що робити |
|----------|------------|
| Тільки погода + опційно історична погода | Не налаштовувати MCP. |
| Погода + календар (події, розклад) | Налаштувати Google Calendar за розділом 3 (LangChain Toolkit). MCP не потрібен. |
| Погода + інші зовнішні інструменти через MCP | Запустити свій MCP-сервер, вказати `MCP_ENDPOINT` у `.env`, при потребі додати виклики MCP-інструментів у агента. |

---

## 5. Історична погода (RAG / ChromaDB)

Щоб агент міг додавати порівняння «цей день в історії» (при промпті v3):

1. Підготуйте дані: CSV `data/chunks.csv` з колонками `city`, `station_id`, `year`, `month`, `day`, `text`.
2. Побудуйте індекс ChromaDB (потрібен **OPENAI_API_KEY** для embedding):
   ```bash
   make historical-build
   ```
3. Запускайте бота з `PROMPT_VERSION=3`: `make run PROMPT_VERSION=3`.

Деталі — у README, секція «Historical / RAG режим».

---

## 6. Розгортання в Docker

- Зберіть образ: `make docker-build` або `docker build -t weather-agent:latest .`.
- Секрети передавайте через `.env` (не копіюйте їх у образ): `docker run --rm --env-file .env weather-agent:latest` або `make docker-run`.
- Якщо використовуєте Google Calendar, потрібно змонтувати каталог з `credentials.json` та `token.json` у контейнер і вказати відповідні шляхи в `.env` (наприклад, `GOOGLE_CALENDAR_CREDENTIALS_PATH=/secrets/credentials.json`).

Приклад запуску з примонтованими credentials:

```bash
docker run --rm --env-file .env \
  -v "$(pwd)/credentials.json:/secrets/credentials.json:ro" \
  -v "$(pwd)/token.json:/secrets/token.json:ro" \
  -e GOOGLE_CALENDAR_CREDENTIALS_PATH=/secrets/credentials.json \
  -e GOOGLE_CALENDAR_TOKEN_PATH=/secrets/token.json \
  weather-agent:latest
```

---

## 7. Перевірка після налаштування

- **Без календаря й MCP:** надішліть боту, наприклад, «Що одягнути в Києві?» — має прийти порада на основі погоди.
- **З календарем:** після налаштування credentials і `PROMPT_VERSION=3` напишіть: «Сьогодні в мене зустріч у центрі Києва о 18:00 — що вдягнути?» Агент може викликати інструменти календаря й погоди й дати комбіновану пораду.
- **Тести:** `make test-no-llm` — перевірка без реального LLM; `make test` — усі тести (з OPENAI_API_KEY для LLM-тестів).

Якщо виникнуть помилки авторизації Google, перевірте шляхи до `credentials.json` та `token.json` і scope доступу (для читання подій достатньо `https://www.googleapis.com/auth/calendar.readonly` у конфігурації OAuth).

---

## 8. Тести MCP та FastMCP

У проєкті є unit-тести для MCP-клієнта та MCP-based tools і опційний інтеграційний тест з **FastMCP**.

### Як запускати MCP-тести

- **Усі тести (включно з MCP unit):** `make test-no-llm` або `pytest tests/UnitMock/ tests/IntegrationMock/ -v` — тести в `test_mcp_client.py` та `test_mcp_tools.py` виконуються разом з іншими UnitMock/IntegrationMock.
- **Лише тести, позначені маркером `mcp`:**  
  `pytest -m mcp -v`  
  Це запустить unit-тести MCP-клієнта та MCP tools і, якщо встановлено `fastmcp`, інтеграційний тест з FastMCP-сервером.
- **Інтеграційний тест FastMCP (окремо):**  
  `pytest tests/integration_mcp/ -v`  
  Потрібна dev-залежність `fastmcp` (`pip install -e ".[dev]"`). Тест запускає тестовий FastMCP-сервер у subprocess (один tool `echo`), підключається до нього через FastMCP Client і перевіряє виклик `call_tool("echo", {"text": "hello"})`.

### Що таке FastMCP у контексті проєкту

- **FastMCP** ([gofastmcp.com](https://gofastmcp.com/)) — фреймворк для MCP-серверів і клієнтів (Python). У weather-agent він використовується **лише в тестах**: тестовий сервер (`tests/integration_mcp/fastmcp_test_server.py`) і офіційний FastMCP Client у інтеграційному тесті перевіряють, що MCP-шар працює з реальним сервером.
- Production-код використовує власний HTTP JSON-RPC клієнт (`weather_agent.mcp.client`). Його протокол (методи `tools/list`, `tools/call`) може відрізнятися від офіційного MCP HTTP-транспорту FastMCP; тому інтеграційний тест поки що запускає **FastMCP Client + FastMCP Server**, а не наш клієнт до FastMCP endpoint. У майбутньому можна додати адаптер або перейти на FastMCP Client для звернень до MCP-серверів.
