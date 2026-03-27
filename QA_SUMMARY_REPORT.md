# QA Summary Report

## Project
Education Weather Agent

## Test Type
Manual Testing

## Environment
- OS: Windows
- Interface: Telegram Bot
- Execution mode: local run via `python main.py`

## Scope
The following functionality was covered during testing:
- bot startup
- `/start` command
- `/help` command
- valid weather and clothing requests
- short city-name input
- invalid city handling
- prompt injection resistance
- English input handling
- non-target and unclear input handling

## Test Execution Summary
- Total test cases: 12
- Passed: 11
- Failed: 1
- Blocked: 0

## Test Results Overview
The bot was successfully launched locally and connected to Telegram.  
Basic commands worked correctly.  
The bot correctly handled normal weather-related requests, city-only input, invalid city names, prompt injection attempts, and unclear input such as greetings or numeric values.

One defect was identified during testing:
- when the user sent a request in English, the bot returned the answer in Ukrainian instead of English.

## Defects Found
1. Bot does not preserve user input language in response.

## Conclusion
The main functionality of the Education Weather Agent works correctly.  
The bot starts successfully, responds to commands, provides clothing recommendations based on weather, handles invalid city names gracefully, and resists prompt injection attempts.

At the same time, one issue was found in language consistency.  
For English-language input, the bot responded in Ukrainian.  
This does not break the core functionality, but it negatively affects usability for English-speaking users.

Overall result: the application is stable for basic manual testing, with one minor functional/usability issue identified.
