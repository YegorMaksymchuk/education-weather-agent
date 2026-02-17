# Weather outfit agent (Що одягнути)

Простий Telegram-бот на Python: агент на базі LangChain з одним інструментом погоди (Open-Meteo). Користувач пише місто або запит — бот відповідає, що вдягнути. Є команди /start та /help, системні промпти версіонуються (PROMPT_VERSION), тести розбиті за рівнями (Unit/Integration/System, Mock/LLM).

Проєкт створений як навчальний приклад тестування AI-agent додатків для студентів. Під час розробки використовувалися Cursor IDE та підхід Spec Driven Development на основі планування.

## Що потрібно

- Python 3.10+
- Токен Telegram-бота ([@BotFather](https://t.me/BotFather))
- API-ключ OpenAI (для моделі, напр. `gpt-4o-mini`)

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

3. За бажанням змініть **DEFAULT_MODEL** (за замовчуванням `gpt-4o-mini`) та **PROMPT_VERSION** (1 або 2).

## Запуск

З кореня проєкту:

```bash
python main.py
```

Бот працює в режимі long polling і відповідає на текстові повідомлення.

## Make

У корені проєкту є **Makefile** (venv з урахуванням ОС, залежності, запуск бота з версією промпта, тести). Потрібен `make`.

```bash
make help              # Список цілей
make install           # venv + встановлення залежностей та dev-залежностей
make run               # Запуск бота (PROMPT_VERSION=2 за замовчуванням)
make run PROMPT_VERSION=1
make run-prompt-1      # Бот з промптом v1
make run-prompt-2      # Бот з промптом v2
make test-no-llm      # Тести без реального LLM (для CI)
make test             # Усі тести
make test-unit-mock   # Лише UnitMock
make test-coverage    # Покриття (без LLM-тестів)
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
├── Makefile                   # Автоматизація: venv, install, run, test, coverage
├── pyproject.toml             # Метадані пакета, залежності, pytest markers
├── requirements.txt           # Залежності для pip
├── .env.example               # Шаблон змінних (TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, PROMPT_VERSION)
├── .gitignore
├── LICENSE                    # MIT
├── README.md
├── doc/
│   └── Idea_How_To_Test_AI_Agent.md   # Матеріал з тестування AI-агентів (unit/integration/system, DeepEval)
├── src/weather_agent/
│   ├── __init__.py
│   ├── config.py              # Змінні середовища (DEFAULT_MODEL, PROMPT_VERSION тощо)
│   ├── weather.py             # Tool get_weather: Open-Meteo Geocoding + Forecast
│   ├── agent.py               # LangChain-агент (create_agent, ask_agent), підключення промпта
│   ├── bot.py                 # Telegram long polling: /start, /help, обробка текстових повідомлень
│   └── prompts/
│       ├── __init__.py        # get_system_prompt(version) — читання .txt за PROMPT_VERSION
│       ├── system_prompt_v1.txt
│       └── system_prompt_v2.txt
└── tests/
    ├── conftest.py            # Спільні фікстури та конфіг pytest
    ├── __init__.py
    ├── UnitMock/              # Юніт-тести без LLM/HTTP (моки)
    │   ├── test_weather.py
    │   ├── test_config.py
    │   ├── test_bot_texts.py
    │   └── test_prompts.py
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
