# Bug Report

## Title
Bot does not preserve user input language in response

## Severity
Low

## Priority
Medium

## Preconditions
- Bot is running locally
- Bot is connected to Telegram
- User can send messages to the bot

## Steps to Reproduce
1. Open Telegram
2. Open the Weather Homework Bot chat
3. Send the message: `What should I wear in London today?`

## Actual Result
The bot returns a weather-based clothing recommendation, but the response is in Ukrainian.

## Expected Result
The bot should respond in English when the user sends the request in English.

## Frequency
100% (reproduced during manual testing)

## Impact
This issue affects language consistency and user experience for English-speaking users.  
The bot remains functional, but its response does not match the language of the user's request.

## Notes
The issue does not block the main functionality, but it should be fixed to improve usability and multilingual support.
