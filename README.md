# Weather outfit agent (Що одягнути)

Простий Telegram-бот на Python: агент на базі LangChain з одним інструментом погоди (Open-Meteo). Користувач пише місто або запит — бот відповідає, що вдягнути. Є команди /start та /help, системні промпти версіонуються (PROMPT_VERSION), тести розбиті за рівнями (Unit/Integration/System, Mock/LLM).

Проєкт створений як навчальний приклад тестування AI-agent додатків для студентів. Під час розробки використовувалися Cursor IDE та підхід Spec Driven Development на основі планування.

## Що потрібно

- Python 3.10+
- Токен Telegram-бота ([@BotFather](https://t.me/BotFather))
- API-ключ OpenAI (для моделі, напр. `gpt-4o-mini`)
- (опційно) Облікові дані Google Calendar (credentials.json / token.json), якщо хочете, щоб агент враховував ваш розклад через LangChain Google Calendar Toolkit

## Віртуальне середовище (venv)

Рекомендовано використовувати venv, щоб не змішувати залежності з системним Python.

```bash
cd support-wather-agent
python -m venv venv
```

Активація:

- **Linux / macOS:** `source venv/bin/activate`
- **Windows (cmd):** `venv\Scripts\activate.bat`
- **Windows (PowerShell):** `venv\Scripts\Activate.ps1`

## Встановлення

У активованому venv:

```bash
pip install -r requirements.txt
```

Або з використанням проєкту як пакета:

```bash
pip install -e .
```

## Налаштування

1. Скопіюйте `.env.example` у `.env`:
   ```bash
   cp .env.example .env
   ```

2. Відкрийте `.env` і вкажіть:
   - **TELEGRAM_BOT_TOKEN** — токен від @BotFather
   - **OPENAI_API_KEY** — ключ з [OpenAI](https://platform.openai.com/api-keys)

3. За бажанням змініть:
   - **DEFAULT_MODEL** (за замовчуванням `gpt-4o-mini`)
   - **PROMPT_VERSION** (1 — базовий, 2 — тепліший тон, 3 — з історичною погодою/RAG та інтеграцією з календарем)
   - **GOOGLE_CALENDAR_CREDENTIALS_PATH** / **GOOGLE_CALENDAR_TOKEN_PATH** (опційні шляхи до файлів `credentials.json` та `token.json` для інтеграції з Google Calendar через LangChain Google Calendar Toolkit)

Детальні кроки розгортання, налаштування Google Calendar та MCP описані в [doc/Deployment_and_MCP_Setup.md](doc/Deployment_and_MCP_Setup.md).

## Запуск

З кореня проєкту:

```bash
python main.py
```

Бот працює в режимі long polling і відповідає на текстові повідомлення.

## Docker

Образ збирається за **multi-stage** Dockerfile: етап builder (Python 3.12 slim) встановлює залежності в `/opt/venv`, етап runtime копіює лише venv та код і запускає контейнер від користувача **appuser** (non-root). Секрети в образ не потрапляють; `docker-compose.yml` підключає `env_file: .env`, `read_only: true`, `tmpfs: /tmp`, `restart: unless-stopped`.

**Через Make (рекомендовано):**

Перед першим запуском створіть `.env` з `TELEGRAM_BOT_TOKEN` та `OPENAI_API_KEY`.

```bash
make docker-build    # Зібрати образ (за замовчуванням weather-agent:latest)
make docker-run     # Зібрати і запустити контейнер з --env-file .env (один раз, у foreground)
make docker-up      # Зібрати і запустити у фоні (docker compose up -d)
make docker-down    # Зупинити контейнер (docker compose down)
make docker-logs    # Логи (docker compose logs -f)
```

Ім’я образу можна змінити: `make docker-build DOCKER_IMAGE=my-agent:v1`.

**Вручну (docker):**

```bash
docker build -t weather-agent:latest .
docker run --rm --read-only --tmpfs /tmp --env-file .env weather-agent:latest
```

**Вручну (змінні в CLI):**

```bash
docker run --rm --read-only --tmpfs /tmp \
  -e TELEGRAM_BOT_TOKEN=... -e OPENAI_API_KEY=... \
  weather-agent:latest
```

**Вручну (Compose):**

```bash
docker compose up -d
```

**Безпека:** не копіюйте `.env` в образ; передавайте секрети через `-e` або `--env-file`. Для перевірки образу: `docker scout` або `trivy image`.

## Observability (моніторинг LLM / OpenLIT)

У проєкті підключено **[OpenLIT](https://github.com/openlit/openlit)** — OpenTelemetry-орієнтований SDK для автоматичного збору трейсів, метрик і логів викликів LLM (LangChain, OpenAI, httpx, ChromaDB тощо). Телеметрія відправляється за протоколом **OTLP** у **OpenTelemetry Collector**, далі зберігається в **ClickHouse** і візуалізується в **Grafana** (дашборд «GenAI Cost Dashboard»).

### Як це працює (коротко)

1. У [`main.py`](main.py) викликається `openlit.init(...)` **до** імпорту Telegram-бота, щоб інструментація встигла підключитися до LangChain.
2. За замовчуванням `OTEL_EXPORTER_OTLP_ENDPOINT` не заданий — експорт у колектор вимкнено (зручно для локальної розробки без Docker-стеку).
3. У **Docker Compose** сервіс `weather-agent` підключено до мережі `observability-net` і отримує `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318`.
4. Колектор обробляє дані (у т.ч. процесор `transform/openlit`) і пише їх у БД `otel` у ClickHouse; Grafana читає таблиці `otel_traces` / `otel_logs`.

### Швидкий старт

1. Підніміть стек observability (ClickHouse, OTel Collector, Grafana):

   ```bash
   make observability-up
   ```

2. Запустіть бота на хості з експортом OTLP на `localhost:4318`:

   ```bash
   make run-with-otel
   ```

   Або вручну встановіть змінні середовища (див. [`.env.example`](.env.example)) і виконайте `python main.py`.

3. Відкрийте Grafana: **http://localhost:3000** (дефолтний логін Grafana — зазвичай `admin` / `admin` при першому запуску, якщо не змінено). Перегляньте дашборд **GenAI Cost Dashboard**.

### Якщо в Grafana порожні панелі

1. **Перевірте OTLP:** при запуску бота на хості без `make run-with-otel` змінна `OTEL_EXPORTER_OTLP_ENDPOINT` має бути задана в `.env` (наприклад `http://localhost:4318`). Інакше в логах з’явиться попередження, що експорт вимкнено — трейси не потрапляють у ClickHouse. У Docker для сервісу `weather-agent` endpoint задає Compose.
2. **Панель «Diagnostics: span rows»** на дашборді показує кількість усіх спанів у вибраному часі без фільтра `gen_ai.*`. Якщо **0** — немає даних у ClickHouse (колектор, мережа або не було трафіку). Якщо **> 0**, а інші віджети порожні — перегляньте, чи є в трейсах атрибути GenAI (потрібні реальні виклики LLM через OpenLIT).
3. **Часовий діапазон** у Grafana (правий верхній кут): розширте, наприклад, до «Last 24 hours», якщо дані з’явилися раніше.
4. **Джерело даних:** у Grafana → Connections → Data sources → `clickhouse` → **Save & test**. У панелі — **Query inspector**, якщо є помилка SQL або підключення.
5. **CLI:** після `make observability-up` виконайте `make observability-verify` — покаже кількість рядків у `otel_traces` і ключі `gen_ai.*` у останньому спані (для діагностики без Grafana).

### Pytest і Grafana (`OTEL_TESTS_EXPORT`)

За замовчуванням `pytest` **не** надсилає OTLP — див. [`tests/conftest.py`](tests/conftest.py). Щоб після прогону тестів з’явились трейси/метрики в Grafana:

1. Підніміть стек observability (колектор має слухати `localhost:4318`):

   ```bash
   make observability-up
   ```

2. **Усі основні тести з OTLP** (як `test-no-llm`, плюс `IntegrationLLM` і `SystemLLM`; для останніх потрібен **`OPENAI_API_KEY`** у середовищі або `.env`):

   ```bash
   make test-with-otel-export
   ```

3. **Лише тести з реальним OpenAI** — найкраще для **заповнення всіх панелей** GenAI Cost Dashboard (`gen_ai.request.model`, токени, вартість тощо). Потрібен **`OPENAI_API_KEY`**:

   ```bash
   make test-with-otel-llm
   ```

4. Або **вручну**:

   ```bash
   OTEL_TESTS_EXPORT=1 OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 pytest tests/
   ```

   Для лише LLM-тестів (мінімум для повного дашборду):

   ```bash
   OTEL_TESTS_EXPORT=1 OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 pytest tests/IntegrationLLM/ tests/SystemLLM/
   ```

У Grafana сервіс зазвичай відображається як **`weather-agent-tests`** (або значення `OTEL_SERVICE_NAME`, якщо задали своє). Детальніше — розділ «Pytest і експорт OTLP» у **[doc/Observability_Guide.md](doc/Observability_Guide.md)**.

### Що моніториться автоматично

- Виклики чат-моделі OpenAI через LangChain (`ChatOpenAI`, `create_agent`).
- Інструменти агента (погода, RAG, календар) — як зовнішні виклики в залежності від інтеграції.
- HTTP-запити через `httpx` (наприклад Open-Meteo), за наявності відповідної інструментації OpenLIT.
- За потреби — увімкнення збору системних метрик через параметри OpenLIT (див. офіційну документацію).

### Деякі атрибути GenAI (у трейсах)

У ClickHouse/Grafana зустрічаються семантичні атрибути на кшталт `gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.total_tokens`, `gen_ai.usage.cost` — вони використовуються дашбордом і правилом алерту «Max Tokens Consumption».

### Алерти

У [`observability/grafana/provisioning/alerting/alert-rules.yaml`](observability/grafana/provisioning/alerting/alert-rules.yaml) налаштовано приклад **алерту за максимальним споживанням токенів** за останню годину. Для сповіщень потрібно налаштувати **contact point** у Grafana (наприклад email).

### Змінні середовища (довідник)

| Змінна | Призначення |
|--------|-------------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | URL OTLP (HTTP), напр. `http://localhost:4318` або `http://otel-collector:4318` у Docker |
| `OTEL_TESTS_EXPORT` | `1` / `true` — увімкнути експорт OTLP під час `pytest` (інакше в тестах endpoint скидається); разом з `OTEL_EXPORTER_OTLP_ENDPOINT` |
| `OTEL_SERVICE_NAME` | Назва сервісу в ресурсі трейсів (за замовчуванням `weather-agent`) |
| `OTEL_DEPLOYMENT_ENVIRONMENT` | Середовище (напр. `development`, `production`) |
| `OPENLIT_TRACE_CONTENT` | `true`/`false` — чи записувати текст промптів і відповідей (у коді передається як `capture_message_content` у `openlit.init`) |
| `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` | Альтернативна назва: якщо задана непорожня, має пріоритет над `OPENLIT_TRACE_CONTENT` |

Детальний розбір усіх файлів у каталозі `observability/` — у **[doc/Observability_Guide.md](doc/Observability_Guide.md)**.

## Historical / RAG режим

Додатково до поточної погоди агент може підхоплювати **історичні приклади погоди в цей день** (RAG на базі ChromaDB):

- `data/chunks.csv` — вихідний CSV з текстовими описами історичної погоди (city, year, month, day, text).
- `src/weather_agent/historical/store.py` — побудова/збереження Chroma-колекції з CSV (`build_and_persist_chroma`).
- `src/weather_agent/historical/retrieval.py` — пошук історичних записів за містом і календарною датою (`retrieve_historical_same_day`).
- `src/weather_agent/historical/tools.py` — LangChain tool `get_historical_weather`, який агент може викликати після `get_weather`.
- `prompts/system_prompt_v3.txt` — системний промпт, який підказує агенту використовувати historical/RAG порівняння.

Щоб побудувати локальний індекс ChromaDB (за замовчуванням каталог `CHROMA_PERSIST_DIR=chroma_langchain_db`):

```bash
make historical-build  # Потрібен OPENAI_API_KEY і доступ до OpenAI embeddings
```

Після цього агент зможе викликати `get_historical_weather` і додавати до відповіді блок «історична погода в цей день». Для того щоб сильніше підштовхнути модель до такого порівняння, можна запускати бота з `PROMPT_VERSION=3`, наприклад:

```bash
make run PROMPT_VERSION=3
```

## Інтеграція з Google Calendar через LangChain Toolkit

Агент може враховувати ваші плани й події через **офіційний LangChain Google Calendar Toolkit** (`langchain-google-community[calendar]`). Це працює незалежно від Telegram — календарні інструменти підключаються безпосередньо до LangChain‑агента.

- `src/weather_agent/calendar/google_toolkit.py` — адаптер, який створює `CalendarToolkit` (залежно від ваших credentials) і повертає список інструментів для агента.
- `src/weather_agent/agent.py` — агент підключає календарні tools з `CalendarToolkit` поряд з `get_weather` та `get_historical_weather`, тому будь‑який клієнт (Telegram, CLI тощо) автоматично отримує доступ до вашого розкладу.
- `src/weather_agent/prompts/system_prompt_v3.txt` — системний промпт, який пояснює агенту, коли варто звертатися до календаря (коли користувач згадує зустрічі, поїздки, прогулянки тощо) і як поєднувати це з порадою по одягу.

Щоб увімкнути інтеграцію з Google Calendar:

1. Налаштуйте Google Calendar API, як описано в [Google Calendar API quickstart для Python](https://developers.google.com/calendar/api/quickstart/python#authorize_credentials_for_a_desktop_application): отримаєте `credentials.json`, а при першому запуску згенерується `token.json`.
2. Встановіть залежність (вона вже додана в `pyproject.toml` та `requirements.txt`):
   - `langchain-google-community[calendar]` (див. офіційні доки: [Google calendar toolkit integration](https://docs.langchain.com/oss/python/integrations/tools/google_calendar)).
3. Додайте в `.env` (або покладіть файли в дефолтні шляхи):
   - `GOOGLE_CALENDAR_CREDENTIALS_PATH=./credentials.json`
   - `GOOGLE_CALENDAR_TOKEN_PATH=./token.json`
4. Запустіть бота як зазвичай (`make run` / `python main.py`). Якщо користувач згадує плани/події, агент зможе використовувати календарні інструменти для уточнення поради по одягу з урахуванням вашого розкладу.

## CI (GitHub Actions)

У репозиторії налаштовані два workflow:

- **`.github/workflows/ci.yml`** — на `push` та `pull_request` до `main`/`master`: лінтер (Ruff), аналіз безпеки коду (Bandit), аналіз залежностей (pip-audit), шість груп тестів (UnitMock, UnitLLM, IntegrationMock, IntegrationLLM, SystemMock, SystemLLM). Для IntegrationLLM і SystemLLM у репозиторії має бути налаштований secret **OPENAI_API_KEY** (якщо його немає, ці тести пропускаються).
- **`.github/workflows/release.yml`** — при push тегу `v*` (наприклад `v1.0.0`): збірка Docker-образу та push у GitHub Container Registry. Образ тегується як `ghcr.io/<owner>/<repo>:sha-<short-sha>` та `ghcr.io/<owner>/<repo>:<git-tag>`.

Ті самі перевірки можна запустити локально через Make: `make lint`, `make code-security`, `make dependency-security`, `make test-no-llm` або одним викликом `make ci`.

## Make

У корені проєкту є **Makefile** (venv з урахуванням ОС, залежності, запуск бота, тести, lint/безпека, Docker, historical/RAG). Потрібен `make`.

```bash
make help               # Список усіх цілей
make install            # venv + встановлення залежностей та dev-залежностей
make run                # Запуск бота (PROMPT_VERSION=2 за замовчуванням)
make run PROMPT_VERSION=1
make run-prompt-1       # Бот з промптом v1
make run-prompt-2       # Бот з промптом v2
make test-no-llm        # Тести без реального LLM (для CI)
make test               # Усі тести
make test-unit-mock     # Лише UnitMock
make test-coverage      # Покриття (без LLM-тестів)
make lint               # Ruff check + format check (як у CI)
make lint-fix           # Ruff check --fix + format
make code-security      # Bandit scan (src/)
make dependency-security # pip-audit
make ci                 # lint + code-security + dependency-security + test-no-llm
make historical-build   # Побудова індексу ChromaDB з data/chunks.csv (потрібен OPENAI_API_KEY)
make docker-build       # Зібрати Docker-образ
make docker-run         # Зібрати і запустити контейнер (--env-file .env)
make docker-up          # docker compose up -d
make docker-down        # docker compose down
make docker-logs        # docker compose logs -f
make observability-up   # Лише ClickHouse + OTel Collector + Grafana
make observability-down # docker compose down
make observability-logs # Логи otel-collector
make run-with-otel      # Бот з OTLP на localhost:4318 (після observability-up)
```

На Windows використовуйте `make` з Git Bash або WSL; Makefile визначає `venv\Scripts` для Windows.

## Приклади запитів

- «Що одягнути в Києві?»
- «Як одягнутися сьогодні у Львові?»
- «Погода в Одесі — що вдягнути?»

Агент спочатку отримує поточну погоду через Open-Meteo (Geocoding + Forecast), потім дає коротку рекомендацію українською.

## Структура проєкту

```
support-wather-agent/
├── main.py                    # Точка входу: .env, перевірка конфігу, запуск бота
├── Makefile                   # Автоматизація: venv, install, run, test, lint, ci, docker, historical-build
├── Dockerfile                 # Multi-stage: builder (venv) + runtime (appuser, CMD main.py)
├── docker-compose.yml         # Сервіс weather-agent: env_file, read_only, tmpfs, restart
├── .dockerignore              # Контекст збірки без тестів, venv, .env
├── .github/workflows/         # GitHub Actions: ci.yml (lint, security, tests), release.yml (GHCR)
├── pyproject.toml             # Метадані пакета, залежності, pytest markers, Ruff
├── requirements.txt           # Залежності для pip
├── .env.example               # Шаблон змінних (TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, PROMPT_VERSION)
├── .gitignore
├── LICENSE                    # MIT
├── README.md
├── doc/
│   ├── Deployment_and_MCP_Setup.md    # Розгортання, налаштування .env, Google Calendar, MCP
│   ├── Observability_Guide.md         # Детальний опис observability: OpenLIT, OTel Collector, Grafana, файли
│   └── Idea_How_To_Test_AI_Agent.md   # Матеріал з тестування AI-агентів (unit/integration/system, DeepEval)
├── observability/
│   ├── otel-collector-config.yaml     # Конфігурація OpenTelemetry Collector (OTLP → ClickHouse)
│   ├── clickhouse/initdb/             # Init-скрипти БД (створення `otel`)
│   └── grafana/provisioning/          # Grafana: datasources, dashboards, alerting
├── src/weather_agent/
│   ├── __init__.py
│   ├── config.py              # Змінні середовища (DEFAULT_MODEL, PROMPT_VERSION тощо)
│   ├── weather.py             # Tool get_weather: Open-Meteo Geocoding + Forecast
│   ├── agent.py               # LangChain-агент (create_agent, ask_agent), підключення промпта, historical tool та інструментів Google Calendar Toolkit
│   ├── bot.py                 # Telegram long polling: /start, /help, обробка текстових повідомлень
│   ├── mcp/                   # Інтеграція з MCP-серверами (загальний клієнт, не використовується для календаря після міграції)
│   │   ├── __init__.py
│   │   ├── client.py          # McpClientBase, HttpJsonRpcMcpClient, get_default_mcp_client
│   │   └── tools.py           # Інструменти поверх MCP (можуть бути використані для інших сервісів у майбутньому)
│   ├── calendar/              # Інтеграція з Google Calendar через LangChain Google Calendar Toolkit
│   │   ├── __init__.py
│   │   └── google_toolkit.py  # Адаптер CalendarToolkit, get_calendar_tools_for_agent()
│   ├── historical/            # Історична погода/RAG (ChromaDB)
│   │   ├── chunks.py          # Форматування/валідація денних записів
│   │   ├── store.py           # Побудова та збереження Chroma-колекції з CSV
│   │   ├── retrieval.py       # Retrieval історичних chunks за (місто, день, місяць)
│   │   └── tools.py           # LangChain tool get_historical_weather
│   └── prompts/
│       ├── __init__.py        # get_system_prompt(version) — читання .txt за PROMPT_VERSION
│       ├── system_prompt_v1.txt
│       ├── system_prompt_v2.txt
│       └── system_prompt_v3.txt
├── data/
│   └── chunks.csv             # Історичні текстові chunks погоди для побудови ChromaDB
└── tests/
    ├── conftest.py            # Спільні фікстури та конфіг pytest
    ├── __init__.py
    ├── UnitMock/              # Юніт-тести без LLM/HTTP (моки)
    │   ├── test_weather.py
    │   ├── test_config.py
    │   ├── test_bot_texts.py
    │   ├── test_prompts.py
    │   ├── test_mcp_client.py          # Тести MCP-клієнта (HttpJsonRpcMcpClient)
    │   ├── test_mcp_tools.py           # Тести MCP-based tools (залишені для сумісності, календар більше не використовує MCP)
    │   └── test_calendar_toolkit_adapter.py  # Тести адаптера LangChain Google Calendar Toolkit
    ├── UnitLLM/               # Юніт з фейковим LLM (GenericFakeChatModel)
    │   ├── conftest.py
    │   └── test_agent_fake_model.py
    ├── IntegrationMock/       # Інтеграція з замоканим LLM/HTTP
    │   └── test_agent_tool_flow.py
    ├── IntegrationLLM/        # Інтеграція з реальним/DeepEval LLM (потрібен OPENAI_API_KEY)
    │   ├── conftest.py
    │   └── test_deepeval_metrics.py
    ├── SystemMock/            # E2E з фейковим агентом (без реального API)
    │   └── test_bot_handlers.py
    └── SystemLLM/             # E2E з реальним агентом, safety-тести (потрібен OPENAI_API_KEY)
        ├── test_safety.py
        └── test_task_completion.py
```

## Тести

У проєкті є тести за шарами (UnitMock, UnitLLM, IntegrationMock, IntegrationLLM, SystemMock, SystemLLM). Тести з суфіксом **Mock** не викликають реальний OpenAI API.

**Через Make (рекомендовано):**

```bash
make install      # venv + усі залежності
make test-no-llm  # Тести без реального LLM (для CI)
make test         # Усі тести (IntegrationLLM/SystemLLM пропустяться без OPENAI_API_KEY)
make test-coverage
```

**Вручну:** встановити залежності `pip install -e ".[dev]"`, потім `pytest tests/UnitMock/ tests/UnitLLM/ tests/IntegrationMock/ tests/SystemMock/ -v` або `pytest tests/ -v`. Маркери: `unit_mock`, `unit_llm`, `integration_mock`, `integration_llm`, `system_mock`, `system_llm`, `safety`.

## Ліцензія та API

- [Open-Meteo](https://open-meteo.com/) — безкоштовний для некомерційного використання, API-ключ не потрібен.
- Токени та ключі зберігайте лише в `.env`, не комітьте файл `.env` у репозиторій.
