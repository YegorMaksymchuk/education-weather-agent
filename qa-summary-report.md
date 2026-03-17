## QA Summary Report — WeatherAgent Bot (Telegram)

### Introduction

- **Project**: WeatherAgent Bot (Telegram chatbot for weather-based outfit recommendations)
- **Testing period**: 2026-03-17 (manual execution)

### Scope of Testing

- **Test type**: Manual functional testing of chatbot behavior in Telegram
- **Covered areas**:
  - Functional testing (positive and negative scenarios)
  - Command testing (`/start`, `/help`)
  - Input validation (long messages, special characters, emojis, multiple languages)
- **Blocked coverage note**:
  - **FN-07** and **FN-08** were **BLOCKED** due to Telegram client UX constraints (the client disables the Send button for whitespace-only messages), so those exact inputs could not be submitted for validation.

### Test Results Summary

#### Execution statistics

| Metric | Count |
|---|---:|
| Total tests | 49 |
| Passed | 44 |
| Failed | 3 |
| Blocked | 2 |

#### Pass rate

- **Pass rate (excluding BLOCKED)**: \(44 / (49 - 2) = 44 / 47 = 93.62\%\)
- **Pass rate (including BLOCKED)**: \(44 / 49 = 89.80\%\)

### Detailed Findings (Found Issues)

#### Issue 1 — Agent Fails to Adhere to Its Defined Role

- **Description**: For non-weather-related queries, the bot answers the off-topic question instead of redirecting the user back to its primary purpose (weather/outfit guidance).
- **Affected test cases**: **FN-05**, **FN-06**
- **Suggested severity**: **Medium**
  - Rationale: The bot remains functional, but violates product scope and can confuse users, undermining trust and purpose.

**FN-05**
- **TC ID**: FN-05
- **Summary**: Non-weather-related question (general knowledge) is answered instead of redirecting to weather/outfit function.
- **Actual Result**: Bot answered about “Kobzar” and suggested additional questions about Shevchenko and his work.
- **Expected Result**: Bot should steer the conversation back to weather/outfit recommendations (e.g., request a city or explain its purpose).

**FN-06**
- **TC ID**: FN-06
- **Summary**: Non-weather-related request (coding) is fulfilled instead of redirecting to weather/outfit function.
- **Actual Result**: Bot generated a Python script for CSV parsing.
- **Expected Result**: Bot should decline/redirect and request a city or a weather-related query.

#### Issue 2 — Insufficient Input Validation for Missing City

- **Description**: When the user provides an incomplete request that does not specify a city, the bot inferred a default (Kyiv) rather than requesting clarification or returning a validation prompt.
- **Affected test cases**: **FN-09**
- **Suggested severity**: **Medium**
  - Rationale: Producing an assumed location can lead to incorrect advice; this is a correctness and trust issue.

**FN-09**
- **TC ID**: FN-09
- **Summary**: City prefix provided without city name is mishandled.
- **Actual Result**: Bot returned weather-related advice for **Kyiv**.
- **Expected Result**: Bot should ask the user to specify the city (or return a clear validation prompt indicating the city is missing).

### Conclusion and Recommendations

- **Overall quality**: Strong functional coverage for core weather/outfit scenarios, commands, and varied input formats/languages. Core flows are stable (high pass rate, no crashes observed in most negative scenarios).
- **Key gaps**:
  - **Role adherence**: The agent can be led into off-topic conversations (FN-05, FN-06).
  - **Input validation**: Incomplete city requests can cause incorrect assumptions (FN-09).
- **Recommendations**:
  - **Strengthen system prompt / guardrails** to enforce “weather outfit assistant only” behavior, especially for off-topic prompts (consider explicit refusal + redirection patterns).
  - **Add explicit city validation/clarification logic** (or prompt instruction) when no city is detected, preventing default-location assumptions.
  - **Add automated security/role tests** (LLM safety/system tests) to prevent regressions in scope adherence and validation behavior.

### Attachment

Attached: Full Test Case Matrix (`test-cases.md`)

