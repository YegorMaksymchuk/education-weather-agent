# Посібник з observability (OpenLIT + OpenTelemetry + Grafana)

Цей документ пояснює **навчальним** кроком, як у проєкті налаштовано моніторинг LLM-додатку: що таке трейси/метрики/логи, як працює **OpenLIT**, і що означає кожен файл у каталозі `observability/`.

---

## 1. Навіщо observability для AI-застосунків?

**Observability** (спостережуваність) — це здатність зрозуміти поведінку системи за **зовнішніми сигналами**:

| Сигнал | Що це | Приклад для LLM |
|--------|--------|-----------------|
| **Traces (трейси)** | Ієрархія операцій з часом і зв’язком (trace id) | Виклик агента → кілька кроків моделі → виклик tool «погода» |
| **Metrics (метрики)** | Числа в часі: лічильники, гістограми | Кількість токенів, оцінка вартості |
| **Logs (логи)** | Події та повідомлення | Помилки експорту, додаткові записи OpenTelemetry |

**OpenTelemetry (OTel)** — відкритий стандарт для збору цих сигналів і відправки їх у бекенди (колектори, бази, Grafana тощо).

**OpenLIT** — SDK, який **автоматично** додає інструментацію до популярних AI-бібліотек (зокрема LangChain і OpenAI), формуючи атрибути за угодами **GenAI** (наприклад `gen_ai.request.model`, `gen_ai.usage.total_tokens`).

---

## 2. Роль OpenLIT у цьому репозиторії

У коді застосунку ([`main.py`](../main.py)) викликається:

```python
openlit.init(
    otlp_endpoint=...,
    application_name=...,  # legacy alias; часто збігається з service_name
    service_name=...,  # OTEL_SERVICE_NAME
    environment=...,
    capture_message_content=...,  # чи логувати текст промптів/відповідей
)
```

**Важливо:** цей виклик виконується **до** імпорту модуля бота, щоб підвантажити інструментацію до першого імпорту LangChain. Точний список аргументів див. `help(openlit.init)` у вашому віртуальному середовищі — вони можуть змінюватися між версіями пакета `openlit`.

Параметри також можна задавати через стандартні змінні OTel (див. [документацію OpenLIT — Configuration](https://docs.openlit.io/latest/sdk/configuration)).

---

## 3. Загальна схема потоку даних

```text
Python (OpenLIT SDK)
    → OTLP HTTP :4318 (або gRPC :4317)
        → OpenTelemetry Collector Contrib
            → процесори: resourcedetection, transform/openlit, batch
                → експортер ClickHouse
                    → база даних `otel` (таблиці на кшталт otel_traces, otel_logs)
                        → Grafana (плагін ClickHouse + дашборд)
```

---

## 4. Файли в `observability/` — покроковий опис

### 4.1. [`observability/otel-collector-config.yaml`](../observability/otel-collector-config.yaml)

Це конфігурація **OpenTelemetry Collector** (збірка `otel/opentelemetry-collector-contrib`).

| Секція | Призначення |
|--------|-------------|
| `receivers.otlp` | Приймає телеметрію за OTLP: gRPC `0.0.0.0:4317`, HTTP `0.0.0.0:4318`. |
| `processors.batch` | Групує дані пакетами перед записом (менше дрібних операцій). |
| `processors.resourcedetection` | Додає атрибути з середовища (`env`) та ОС (`system`). |
| `processors.transform/openlit` | Виправляє розміщення атрибутів: копіює з span у resource поля `service.name`, `deployment.environment`, `telemetry.sdk.name`, якщо OpenLIT поклав їх у span. |
| `exporters.clickhouse` | Підключення до ClickHouse: `tcp://clickhouse:9000`, БД `otel`, `create_schema: true` створює потрібні таблиці. |
| `service.pipelines` | Три пайплайни: `traces`, `metrics`, `logs` — усі виходять у `clickhouse`. |
| `service.telemetry` | Внутрішня телеметрія самого колектора (наприклад метрики через OTLP на localhost у контейнері). |

### 4.2. [`observability/clickhouse/initdb/01_create_databases.sh`](../observability/clickhouse/initdb/01_create_databases.sh)

Скрипт виконується при першому старті контейнера ClickHouse (том `docker-entrypoint-initdb.d`). Створює базу **`otel`**, якщо її ще немає. Решта таблиць для OpenTelemetry зазвичай створюється **експортером колектора** (`create_schema: true`).

### 4.3. [`observability/grafana/provisioning/datasources/clickhouse.yml`](../observability/grafana/provisioning/datasources/clickhouse.yml)

**Provisioning** Grafana: автоматичне додавання джерела даних при старті.

| Поле | Значення |
|------|----------|
| `name` | Відображувана назва: `clickhouse`. |
| `uid` | Стабільний ідентифікатор (`P7E099F39B84EA795`) — на нього посилаються дашборд і алерти. |
| `type` | `grafana-clickhouse-datasource` (плагін встановлюється через `GF_PLUGINS_PREINSTALL`). |
| `jsonData.host` / `port` | Хост `clickhouse` у Docker-мережі, порт **9000** (нативний протокол). |
| `jsonData.logs` / `traces` | Увімкнено режим OTel для таблиць `otel_logs` та `otel_traces`. |

### 4.4. [`observability/grafana/provisioning/dashboards/dashboards.yml`](../observability/grafana/provisioning/dashboards/dashboards.yml)

Каже Grafana, звідки завантажувати JSON-дашборди: каталог `/etc/grafana/provisioning/dashboards` (у контейнері змонтовано з репозиторію).

### 4.5. [`observability/grafana/provisioning/dashboards/GenAI Observability.json`](../observability/grafana/provisioning/dashboards/GenAI%20Observability.json)

Готовий дашборд (у файлі зазвичай вказано заголовок на кшталт **GenAI Cost Dashboard**). Панелі будуються SQL-запитами до ClickHouse по таблиці `otel_traces`: запити до моделей, токени, вартість, тривалість, розбивки за атрибутами тощо. Якщо **UID** джерела даних у Grafana не збігається з полем `datasource.uid` у JSON, панелі не відкриються — тому в `clickhouse.yml` зафіксовано `uid`, узгоджений з дашбордом.

### 4.6. [`observability/grafana/provisioning/alerting/alert-rules.yaml`](../observability/grafana/provisioning/alerting/alert-rules.yaml)

Приклад **правила алерту** «Max Tokens Consumption»:

1. Запит **A** до ClickHouse: максимум `gen_ai.usage.total_tokens` за останню годину.
2. Редукція **B** (останнє значення).
3. Умова **C**: поріг `> 1000` токенів.

Для реальних сповіщень потрібно налаштувати **contact points** у Grafana (email, Slack тощо); у файлі вказано `receiver: grafana-default-email` як приклад.

---

## 5. Docker Compose і мережа

У [`docker-compose.yml`](../docker-compose.yml):

- Сервіси `clickhouse`, `grafana`, `otel-collector` підключені до мережі `observability-net`.
- Сервіс `weather-agent` також у цій мережі й отримує `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318`, щоб ім’я хоста `otel-collector` резолвилось у Docker DNS.

Локально без контейнера бота використовуйте `http://localhost:4318`, якщо порти 4317/4318 проброшені на хост.

---

## 6. Змінні середовища (швидкий довідник)

| Змінна | Опис |
|--------|------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Куди слати OTLP (HTTP). Порожнє значення — експорт вимкнено (див. [`config.py`](../src/weather_agent/config.py)). |
| `OTEL_SERVICE_NAME` | `service.name` у ресурсі. |
| `OTEL_DEPLOYMENT_ENVIRONMENT` | Наприклад `development` / `production`. |
| `OPENLIT_TRACE_CONTENT` | У коді передається в `openlit.init(..., capture_message_content=...)`. |
| `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` | Якщо задана непорожня, перевизначає `OPENLIT_TRACE_CONTENT` (зручно для узгодження з іншими OTel-гайдами). |
| `OTEL_TESTS_EXPORT` | `1` / `true` / `yes` — увімкнути експорт OTLP під час **`pytest`** (див. розділ 7 нижче). Без цієї змінної в тестах endpoint скидається. |

Додаткові атрибути ресурсу: `OTEL_RESOURCE_ATTRIBUTES`, `OTEL_SERVICE_VERSION` (стандарт OpenTelemetry).

---

## 7. Pytest і експорт OTLP (`OTEL_TESTS_EXPORT`)

За замовчуванням тести **не** надсилають телеметрію в колектор: у [`tests/conftest.py`](../tests/conftest.py) експорт вимикається, щоб CI та локальні прогони не засмічували Grafana й не залежали від запущеного OTLP.

Щоб після виконання тестів побачити трейси/метрики в Grafana:

1. Підніміть стек (OpenTelemetry Collector має приймати OTLP на хості, зазвичай порт **4318**):

   ```bash
   make observability-up
   ```

2. Запустіть тести **одним із способів**:

   **`make test-with-otel-export`** — усі основні каталоги тестів (як `test-no-llm`, плюс **`IntegrationLLM`** і **`SystemLLM`**) з експортом OTLP. Для LLM-каталогів потрібен **`OPENAI_API_KEY`**; без ключа ці тести пропускаються, і в Grafana залишаться переважно «часткові» спани (наприклад `execute_tool` / vectordb без `gen_ai.request.model`).

   ```bash
   make test-with-otel-export
   ```

   **`make test-with-otel-llm`** — лише **`tests/IntegrationLLM/`** і **`tests/SystemLLM/`** (реальні виклики `ChatOpenAI` через агента). Це найкоротший шлях, щоб **заповнити всі панелі** GenAI Cost Dashboard (модель, токени, вартість, `gen_ai.system`, тощо). Обов’язково задайте **`OPENAI_API_KEY`**.

   ```bash
   make test-with-otel-llm
   ```

   **Вручну** — повний набір або лише LLM-тести:

   ```bash
   OTEL_TESTS_EXPORT=1 OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 pytest tests/
   ```

   ```bash
   OTEL_TESTS_EXPORT=1 OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 pytest tests/IntegrationLLM/ tests/SystemLLM/
   ```

Якщо `OTEL_EXPORTER_OTLP_ENDPOINT` не заданий, при `OTEL_TESTS_EXPORT=1` у `conftest` підставляється `http://localhost:4318`. У ресурсі трейсів типово **`service.name` = `weather-agent-tests`** (або ваш `OTEL_SERVICE_NAME`), **`deployment.environment` = `test`**.

**Чому не всі панелі заповнені без реального LLM:** тести з моками не викликають OpenAI — OpenLIT не додає на спани повний набір атрибутів (`gen_ai.request.model`, `gen_ai.usage.*`, `gen_ai.usage.cost`, тощо). Дашборд будується SQL-запитами до цих полів; для повної картини використовуйте **`make test-with-otel-llm`**, інтеграційні LLM-тести або запуск бота ([`main.py`](../main.py) / `make run-with-otel`).

---

## 8. Типові проблеми (troubleshooting)

| Симптом | Що перевірити |
|---------|----------------|
| У Grafana немає даних | Чи запущені ClickHouse і колектор; чи бот має `OTEL_EXPORTER_OTLP_ENDPOINT`; чи є мережа Docker між ботом і колектором. |
| Дашборд порожній / помилка datasource | Чи збігається `uid` у `clickhouse.yml` з посиланнями в JSON дашборду. |
| Потрібен експорт OTLP під час `pytest` | Встановіть `OTEL_TESTS_EXPORT=1` і `OTEL_EXPORTER_OTLP_ENDPOINT` (наприклад `http://localhost:4318`), див. розділ 7. Без `OTEL_TESTS_EXPORT` у тестах endpoint навмисно порожній. |
| Панелі GenAI частково порожні (немає моделі/токенів/вартості) | Запустіть тести з реальним OpenAI: **`make test-with-otel-llm`** (потрібен `OPENAI_API_KEY`), див. розділ 7. |
| Під час звичайного `pytest` не хочеться жодного OTLP | Не задавайте `OTEL_TESTS_EXPORT` — поведінка за замовчуванням без експорту. |

---

## 9. Де читати далі

- [OpenLIT — LangChain integration](https://docs.openlit.io/latest/sdk/integrations/langchain)
- [OpenTelemetry Collector — ClickHouse exporter](https://github.com/open-telemetry/opentelemetry-collector-contrib) (модуль у contrib-дистрибутиві)
- [Semantic conventions for Gen AI](https://opentelemetry.io/docs/specs/semconv/gen-ai/) (загальний контекст атрибутів `gen_ai.*`)
