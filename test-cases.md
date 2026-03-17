# Manual Test Cases — Telegram Weather Outfit Chatbot

## Scope and assumptions

- **System under test**: Telegram chatbot that recommends what to wear based on **current weather** for a user-provided city (via Open‑Meteo geocoding + forecast) and responds **in Ukrainian**.
- **Primary interfaces**: Telegram commands `/start`, `/help`, and plain **text** messages (non-commands).
- **Out of scope**: Automated tests, CI, Docker validation, performance/load testing.

## Global preconditions (apply unless overridden)

- The bot is running (long polling) and accessible in Telegram.
- Environment variables are configured (valid `TELEGRAM_BOT_TOKEN`, valid `OPENAI_API_KEY`).
- The device has Internet access (Telegram + Open‑Meteo + OpenAI reachable).

## Notes for manual execution

- Expected outfit advice content is partially non-deterministic (LLM). Validate **intent and key constraints** rather than exact wording:
  - Should reference **current conditions** and give **actionable clothing recommendations**.
  - Should be **safe**, polite, and **in Ukrainian**.
- For error handling cases, validate the bot returns a clear, user-friendly message (and does not crash / stop responding).

---

## 1) Functional Testing (Positive Scenarios)

- TC ID: FP-01
  - Summary: Request outfit advice with a simple city name (Ukrainian)
  - Priority: High
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Open the chat with the bot in Telegram.
    2. Send message: `Київ`
  - Expected Result: Bot replies in Ukrainian with outfit advice based on current weather for Kyiv (no error text).

- TC ID: FP-02
  - Summary: Request outfit advice using a natural Ukrainian phrase (“Що одягнути в …?”)
  - Priority: High
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Що одягнути в Києві?`
  - Expected Result: Bot provides concise Ukrainian outfit recommendations for Kyiv based on current conditions.

- TC ID: FP-03
  - Summary: Request outfit advice using an alternative phrasing (“Як одягнутися сьогодні у …?”)
  - Priority: High
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Як одягнутися сьогодні у Львові?`
  - Expected Result: Bot provides Ukrainian outfit advice for Lviv based on current weather.

- TC ID: FP-04
  - Summary: Request outfit advice with punctuation/dash format (“Погода в … — що вдягнути?”)
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Погода в Одесі — що вдягнути?`
  - Expected Result: Bot responds with Ukrainian outfit advice relevant to Odesa and current conditions.

- TC ID: FP-05
  - Summary: Request outfit advice with an English city name
  - Priority: High
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `What should I wear in London today?`
  - Expected Result: Bot replies (preferably in Ukrainian per bot intent) with outfit advice based on current weather for London.

- TC ID: FP-06
  - Summary: Request outfit advice with mixed language input (Ukrainian + English city)
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Що одягнути в Paris?`
  - Expected Result: Bot responds with Ukrainian outfit advice based on current weather for Paris.

- TC ID: FP-07
  - Summary: Request outfit advice with a city that has diacritics (e.g., “Zürich”)
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Що вдягнути в Zürich?`
  - Expected Result: Bot responds with outfit advice; the city is correctly recognized (no “не вдалося знайти місто”).

- TC ID: FP-08
  - Summary: Request outfit advice for a US city with state hint in the message
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `What should I wear in Portland, Oregon?`
  - Expected Result: Bot provides outfit advice without asking irrelevant follow-up questions; no crash.

- TC ID: FP-09
  - Summary: Request outfit advice with additional context (commute/walking)
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Я буду багато ходити. Що вдягнути сьогодні в Харкові?`
  - Expected Result: Bot gives Ukrainian outfit advice tailored to current weather and considers walking context (e.g., comfortable footwear) when reasonable.

- TC ID: FP-10
  - Summary: Request outfit advice with time qualifier (“зранку/ввечері”) but still current-weather based
  - Priority: Low
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Що вдягнути в Дніпрі ввечері?`
  - Expected Result: Bot provides advice based on current weather; if it cannot do “evening” forecast, it should still provide sensible guidance (layering) without error.

- TC ID: FP-11
  - Summary: Request outfit advice with a question that implies weather lookup (“Яка погода і що вдягнути…?”)
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Яка зараз погода в Варшаві і що краще вдягнути?`
  - Expected Result: Bot answers with outfit guidance; may mention conditions, but must include clothing recommendation.

- TC ID: FP-12
  - Summary: Multiple consecutive requests in the same chat (different cities)
  - Priority: High
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Що одягнути в Києві?`
    2. Wait for reply.
    3. Send message: `А в Барселоні?`
  - Expected Result: Bot replies to both messages; second reply provides outfit advice for Barcelona (no stuck state).

- TC ID: FP-13
  - Summary: City name with trailing/leading spaces is handled
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `   Львів   `
  - Expected Result: Bot trims input and returns outfit advice (not an empty-input warning).

- TC ID: FP-14
  - Summary: City name in Cyrillic with common alternative spelling
  - Priority: Low
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Запоріжжя`
  - Expected Result: Bot returns outfit advice; city is resolved successfully.

- TC ID: FP-15
  - Summary: Request that includes multiple sentences; city is present in later sentence
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Привіт. Підкажи, будь ласка, що вдягнути сьогодні в Івано-Франківську?`
  - Expected Result: Bot responds with Ukrainian outfit advice; ignores greeting noise.

---

## 2) Functional Testing (Negative Scenarios)

- TC ID: FN-01
  - Summary: Invalid/nonexistent city name
  - Priority: High
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Що одягнути в МістоНемаєТакого?`
  - Expected Result: Bot responds with a clear message that the city couldn’t be found (e.g., “Не вдалося знайти місто …”), and suggests checking the name or trying another.

- TC ID: FN-02
  - Summary: Random string input that is not a city
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `asdasd qwe123`
  - Expected Result: Bot either asks for a city / clarifies, or returns “місто не знайдено” style message; no crash.

- TC ID: FN-03
  - Summary: Ambiguous city name without country/region (“Springfield”)
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Що одягнути в Springfield?`
  - Expected Result: Bot returns outfit advice for one resolved result or asks clarifying question; must not return a stack trace or raw tool output.

- TC ID: FN-04
  - Summary: Message contains two different cities (conflicting intent)
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Що вдягнути в Києві чи у Львові?`
  - Expected Result: Bot asks which city to use or chooses one and clearly indicates which; no crash.

- TC ID: FN-05
  - Summary: Non-weather-related question (general knowledge)
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Хто написав "Кобзар"?`
  - Expected Result: Bot should try to steer back to its purpose (outfit by weather) or ask for a city; response remains safe and helpful, without hallucinating weather.

- TC ID: FN-06
  - Summary: Non-weather-related request (coding help)
  - Priority: Low
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Напиши мені Python-скрипт для парсингу CSV`
  - Expected Result: Bot declines or redirects to weather/outfit assistance; no crash.

- TC ID: FN-07
  - Summary: Empty message equivalent (only spaces)
  - Priority: High
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message containing only spaces (e.g., `     `).
  - Expected Result: Bot replies with a prompt to provide a city (e.g., “Напишіть, для якого міста потрібна порада…”).

- TC ID: FN-08
  - Summary: Newline-only / whitespace-heavy message
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send a message that contains newlines and spaces but no letters (if Telegram allows).
  - Expected Result: Bot replies with the “provide a city” prompt; no crash.

- TC ID: FN-09
  - Summary: Message with only a city prefix (“в” / “у”) but no city name
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Що одягнути у ?`
  - Expected Result: Bot asks for a city or returns a clear validation prompt; no crash.

- TC ID: FN-10
  - Summary: Message is a Telegram command-like text but not a supported command
  - Priority: Low
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `/weather Kyiv`
  - Expected Result: Since commands other than `/start` and `/help` are not handled, Telegram should show “unknown command” or bot should not respond; bot remains responsive to subsequent plain text.

- TC ID: FN-11
  - Summary: City name with digits and symbols
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Kyiv!!!111`
  - Expected Result: Bot either fails gracefully with “city not found” message or still resolves; no crash.

- TC ID: FN-12
  - Summary: Simulated upstream weather service issue (network/offline)
  - Priority: High
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Temporarily disable Internet on the machine where the bot runs (or block Open‑Meteo).
    2. Send message: `Що одягнути в Києві?`
    3. Restore connectivity after observing the bot response.
  - Expected Result: Bot responds with a clear error message (e.g., “Виникла помилка. Спробуйте пізніше.” or a friendly failure). Bot continues working after connectivity is restored.

- TC ID: FN-13
  - Summary: Simulated OpenAI/LLM issue (invalid API key or service unavailable)
  - Priority: High
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Start the bot with an invalid `OPENAI_API_KEY` (or revoke the key).
    2. Send message: `Що одягнути в Києві?`
  - Expected Result: Bot replies with a graceful error message (no traceback in chat) and remains running.

---

## 3) Command Testing

- TC ID: CMD-01
  - Summary: `/start` returns welcome message
  - Priority: High
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Open the chat with the bot.
    2. Send command: `/start`
  - Expected Result: Bot replies with a welcome message explaining it can recommend clothing and provides an example query.

- TC ID: CMD-02
  - Summary: `/help` returns usage instructions and examples
  - Priority: High
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send command: `/help`
  - Expected Result: Bot replies with help text that includes example queries and lists `/start` and `/help`.

- TC ID: CMD-03
  - Summary: Commands work at any time during conversation
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Що одягнути в Києві?`
    2. Wait for reply.
    3. Send command: `/help`
  - Expected Result: Bot replies with help text; no dependency on previous context.

- TC ID: CMD-04
  - Summary: `/start` does not break normal text flow
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send command: `/start`
    2. Send message: `Львів`
  - Expected Result: Bot sends welcome text, then sends outfit advice for Lviv when a city is sent.

- TC ID: CMD-05
  - Summary: Unsupported command does not crash the bot
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send command: `/unknown`
    2. Send message: `Київ`
  - Expected Result: Bot may not respond to `/unknown`, but it must still respond normally to the next text message with outfit advice.

---

## 4) Input Validation

- TC ID: IV-01
  - Summary: Very long message containing a valid city name near the end
  - Priority: High
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send a long text (e.g., 1500–3000 characters) describing plans, with the city at the end: `... Підкажи, що вдягнути сьогодні в Києві?`
  - Expected Result: Bot still responds with outfit advice; response time may be longer but no failure.

- TC ID: IV-02
  - Summary: Very long message with no city at all
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send a long text (e.g., 1500–3000 characters) without any city names.
  - Expected Result: Bot asks for a city / clarifies the request rather than producing random city weather.

- TC ID: IV-03
  - Summary: Special characters only
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `!@#$%^&*()_+=[]{};:'",.<>/?\|`
  - Expected Result: Bot handles the input gracefully (asks for a city or indicates it can’t parse), no crash.

- TC ID: IV-04
  - Summary: City name with hyphen
  - Priority: Low
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Івано-Франківськ`
  - Expected Result: Bot returns outfit advice; city is recognized.

- TC ID: IV-05
  - Summary: Emojis added to a valid request
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Що одягнути в Одесі? 👗🧥☔`
  - Expected Result: Bot returns outfit advice; emojis do not break parsing.

- TC ID: IV-06
  - Summary: Emoji-only message
  - Priority: Low
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `🌧️🥶👟`
  - Expected Result: Bot asks for a city / clarifies; no crash.

- TC ID: IV-07
  - Summary: Cyrillic + Latin mix within city name
  - Priority: Low
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message with visually similar mixed characters, e.g. `Киiv` (mix of Cyrillic/Latin).
  - Expected Result: Bot either resolves the city or returns “city not found”; no crash or garbled output.

- TC ID: IV-08
  - Summary: Request in Russian language
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Что надеть в Киеве?`
  - Expected Result: Bot still provides outfit advice (ideally in Ukrainian) for Kyiv; no refusal.

- TC ID: IV-09
  - Summary: Request in English language (non-Ukrainian input)
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `What should I wear in Berlin?`
  - Expected Result: Bot provides outfit advice; should remain aligned with Ukrainian-response intent when feasible.

- TC ID: IV-10
  - Summary: Request in Polish language
  - Priority: Low
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Co mam dziś ubrać w Warszawie?`
  - Expected Result: Bot provides outfit advice (preferably in Ukrainian) for Warsaw; no crash.

- TC ID: IV-11
  - Summary: City name with apostrophe
  - Priority: Low
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Кам'янець-Подільський`
  - Expected Result: Bot handles apostrophe correctly; if geocoding fails, it returns a clear “city not found” message (no crash).

- TC ID: IV-12
  - Summary: Multiple emojis and punctuation around city name
  - Priority: Low
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `🤔🤔 Підкажи!!! що вдягнути... у Львові???`
  - Expected Result: Bot still extracts the intent and provides outfit advice; no crash.

- TC ID: IV-13
  - Summary: Message containing HTML-like tags
  - Priority: Low
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `<b>Що одягнути</b> в Києві?`
  - Expected Result: Bot treats it as plain text and responds normally; no formatting injection issues.

- TC ID: IV-14
  - Summary: Message containing SQL-like injection attempt
  - Priority: Low
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Київ'; DROP TABLE users; --`
  - Expected Result: Bot responds safely (either outfit advice or “city not found”); no abnormal behavior.

- TC ID: IV-15
  - Summary: Message containing URL plus a valid request
  - Priority: Low
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send message: `Ось сайт https://example.com — а що вдягнути в Києві?`
  - Expected Result: Bot ignores the URL and answers with outfit advice; no refusal or crash.

- TC ID: IV-16
  - Summary: Non-text message is ignored (sticker/photo)
  - Priority: Medium
  - Preconditions: The bot is running and accessible in Telegram
  - Steps to Reproduce:
    1. Send a sticker (or photo) to the bot.
    2. Send message: `Київ`
  - Expected Result: Bot does not respond to the sticker/photo (text-only handling), but responds normally to the subsequent city text.

