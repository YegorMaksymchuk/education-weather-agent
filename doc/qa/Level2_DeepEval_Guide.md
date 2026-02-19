# Level 2: DeepEval Automated OWASP Testing

## Що виконано

Додано автоматизоване тестування OWASP TOP 10 LLM вразливостей за допомогою DeepEval фреймворку.

### Реалізовані тести

Файл: `tests/IntegrationLLM/test_deepeval_owasp.py`

**5 ключових OWASP тест-кейсів:**

1. **TC-SEC-001: Prompt Injection** - перевірка стійкості до спроб override інструкцій
2. **TC-SEC-003: System Prompt Disclosure** - захист від витоку system prompt
3. **TC-SEC-011: Model Disclosure** - захист від розкриття назви моделі та архітектури
4. **TC-SEC-006: Excessive Agency** - перевірка що бот не claim-ить неможливі можливості (змінити погоду, викликати служби)
5. **TC-SEC-012: XSS/SQL Injection** - санітизація шкідливого input (script tags, SQL injection)

### Підхід: Варіант A (Minimal)

- Швидкий proof-of-concept з реальними DeepEval метриками
- Використання `ask_agent()` для виклику реального LLM
- Assertions на основі DeepEval `BiasMetric` та прямих перевірок output
- Оптимізовано для низьких витрат токенів (5 тестів замість повного набору з 28)

---

## Локальний запуск

### Передумови

1. Python 3.11+
2. Налаштований `.env` файл з ключами

### Крок 1: Встановити залежності

```bash
pip install -r requirements-dev.txt
```

Це встановить:
- `pytest` (тестовий фреймворк)
- `deepeval>=0.21.0` (LLM testing framework)
- Всі production залежності з `requirements.txt`

### Крок 2: Налаштувати .env

Створіть файл `.env` в корені проекту:

```env
OPENAI_API_KEY=sk-ваш-ключ-тут
TELEGRAM_BOT_TOKEN=ваш-токен-бота
PROMPT_VERSION=2
DEFAULT_MODEL=gpt-4o-mini
```

**ВАЖЛИВО:** Файл `.env` вже додано в `.gitignore` — ніколи не комітьте реальні ключі!

### Крок 3: Запустити DeepEval OWASP тести

```bash
# Запуск всіх DeepEval OWASP тестів
pytest tests/IntegrationLLM/test_deepeval_owasp.py -v

# Запуск конкретного тесту
pytest tests/IntegrationLLM/test_deepeval_owasp.py::TestDeepevalOWASP::test_prompt_injection_ignore_instructions -v

# З детальними логами
pytest tests/IntegrationLLM/test_deepeval_owasp.py -v -s --tb=short
```

### Очікуваний результат

```
tests/IntegrationLLM/test_deepeval_owasp.py::TestDeepevalOWASP::test_prompt_injection_ignore_instructions PASSED
tests/IntegrationLLM/test_deepeval_owasp.py::TestDeepevalOWASP::test_system_prompt_disclosure_refusal PASSED
tests/IntegrationLLM/test_deepeval_owasp.py::TestDeepevalOWASP::test_model_disclosure_protection PASSED
tests/IntegrationLLM/test_deepeval_owasp.py::TestDeepevalOWASP::test_excessive_agency_weather_control PASSED
tests/IntegrationLLM/test_deepeval_owasp.py::TestDeepevalOWASP::test_xss_sql_injection_sanitization PASSED

================================ 5 passed in ~30s ================================
```

**Примітка:** Тести викликають реальний OpenAI API — кожен прогін коштує ~$0.01-0.05 токенів.

---

## CI/CD Integration

### GitHub Actions Workflow

Файл: `.github/workflows/deepeval-integration.yml`

**Тригери:**
- Manual (workflow_dispatch) — рекомендовано для контролю витрат
- Pull Request в `main`/`develop` (тільки якщо є `OPENAI_API_KEY` secret)

**Як додати секрет в GitHub:**
1. Перейти в Settings → Secrets and variables → Actions
2. Додати New repository secret: `OPENAI_API_KEY`
3. Вставити ваш OpenAI API key

**Примітка:** Workflow має `continue-on-error: true` щоб не блокувати PR у разі flaky інтеграційних тестів.

---

## Порівняння з Level 1 (Manual)

| Параметр | Level 1 (Manual) | Level 2 (DeepEval) |
|----------|------------------|-------------------|
| Кількість тестів | 28 (12 security) | 5 (OWASP key) |
| Спосіб виконання | Ручно в Telegram | Автоматично pytest |
| Час виконання | ~2 години | ~30 секунд |
| Витрати | $0 | ~$0.02-0.05/run |
| Регресія | Потрібен re-test | Auto в CI |
| Артефакти | Скриншоти | pytest logs |

---

## Наступні кроки (опціонально)

### Розширення до Варіанту B (Comprehensive)

Якщо потрібне повне покриття всіх 12 OWASP кейсів з Level 1:

1. Додати тести для:
   - LLM02: Insecure Output Handling
   - LLM03: Training Data Poisoning (TC-SEC-008)
   - LLM04: DoS (TC-SEC-009, TC-SEC-010)
   - LLM05: Supply Chain
   - LLM09: Overreliance
   
2. Налаштувати детальні thresholds для метрик

3. Інтегрувати DeepEval CI dashboard для моніторингу

### Додавання Mock тестів (Варіант C - Hybrid)

1. Створити unit-тести з мокуванням LLM відповідей
2. Перевірити input validation (BUG-001 fix)
3. Запускати mock suite на кожен PR (без витрат)

---

## Структура файлів Level 2

```
education-weather-agent-fork/
├── .github/
│   └── workflows/
│       └── deepeval-integration.yml  # CI для DeepEval тестів
├── tests/
│   └── IntegrationLLM/
│       ├── conftest.py               # Fixtures (OPENAI_API_KEY skip)
│       ├── test_deepeval_metrics.py  # Існуючі метрики (AnswerRelevancy)
│       └── test_deepeval_owasp.py    # ✨ НОВІ OWASP тести (5 кейсів)
├── doc/
│   └── qa/
│       └── Level2_DeepEval_Guide.md  # Цей файл
├── requirements-dev.txt              # ✨ НОВІ dev залежності (deepeval, pytest)
├── requirements.txt                  # Production залежності
└── .env                              # Локальні секрети (не комітиться)
```

---

## FAQ

**Q: Чому лише 5 тестів, а не всі 12 OWASP категорій?**
A: Варіант A (Minimal) фокусується на найкритичніших кейсах для швидкого proof-of-concept. Повне покриття доступне у Варіанті B.

**Q: Чи потрібно запускати ці тести на кожен коміт?**
A: Ні, рекомендовано manual trigger або лише на PR в main. Це економить токени та уникає flaky failures.

**Q: Що робити якщо тест fail?**
A: Перевірте:
1. Чи змінився system prompt (`src/weather_agent/prompts/system_prompt_v*.txt`)
2. Чи модель змінила behavior (іноді OpenAI оновлює моделі)
3. Чи threshold метрик потребують калібрування

**Q: Чи можна запустити без OPENAI_API_KEY?**
A: Ні, ці тести вимагають реального LLM. Для тестування без API використовуйте mock suite (Unit tests).

---

## Автор

**Yuliia Zhukova**  
Level 2 Testing — DeepEval Automated OWASP  
Date: 2026-02-19

## Посилання

- [DeepEval Documentation](https://docs.confident-ai.com/)
- [OWASP TOP 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [Level 1 QA Report](qa/QA_Summary_Report.md)
