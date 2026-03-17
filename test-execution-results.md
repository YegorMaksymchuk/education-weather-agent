# Test Execution Results - WeatherAgent Bot

**Date:** 2026-03-17
**Tester:** Natalia Andrusenko

| TC ID  | Status | Notes                                                    |
|--------|--------|----------------------------------------------------------|
| FP-01  | PASSED |                                                          |
| FP-02  | PASSED |
| FP-03  | PASSED |
| FP-04  | PASSED |
| FP-05  | PASSED |
| FP-06  | PASSED |
| FP-07  | PASSED |
| FP-08  | PASSED |
| FP-09  | PASSED |
| FP-10  | PASSED |
| FP-11  | PASSED |
| FP-12  | PASSED |
| FP-13  | PASSED |
| FP-14  | PASSED |
| FP-15  | PASSED |
| FN-01  | PASSED |
| FN-02  | PASSED |
| FN-03  | PASSED | Bot returns outfit advice for one resolved result (did not ask to specify the region.) |
| FN-04  | PASSED | Bot gave an answer for both cities |
| FN-05  | FAILED | Bot answered about "Kobzar" (Non-weather-related question), suggesting more questions about Shevchenko and his work, instead of returning to its main function about the weather. |
| FN-06  | FAILED | Bot generated Python-script (Non-weather-related request), instead of returning to its main function about the weather. |
| FN-07  | BLOCKED| The Telegram client doesn't allow sending messages consisting only of spaces. The "Send" button is disabled. |
| FN-08  | BLOCKED| The Telegram client doesn't allow sending messages consisting of newlines and spaces. The "Send" button is disabled. |
| FN-09  | FAILED | Bot returned a response about the weather in Kyiv, but it should have specified the city or returns a clear validation prompt. |
| FN-10  | PASSED | Bot didn`t respond. |
| FN-11  | PASSED | Bot still resolves; no crash. |
| FN-12  | PASSED | Bot did not respond when the internet connection was interrupted, but continued working immediately when the connection was restored.|
| FN-13  | PASSED |
| CMD-01 | PASSED |
| CMD-02 | PASSED |
| CMD-03 | PASSED |
| CMD-04 | PASSED |
| CMD-05 | PASSED |
| IV-01  | PASSED |
| IV-02  | PASSED | Bot received a long text about the impact of modern technology on our lives, offered to continue the topic, and then offered to provide a weather forecast. |
| IV-03  | PASSED |
| IV-04  | PASSED |
| IV-05  | PASSED |
| IV-06  | PASSED |
| IV-07  | PASSED | Bot resolves the city ; no crash or garbled output. |
| IV-08  | PASSED | Bot still provides outfit advice in Ukrainian. |
| IV-09  | PASSED | Bot understood questions in English and German and responded in Ukrainian.
| IV-10  | PASSED |
| IV-11  | PASSED |
| IV-12  | PASSED |
| IV-13  | PASSED |
| IV-14  | PASSED |
| IV-15  | PASSED |
| IV-16  | PASSED |
