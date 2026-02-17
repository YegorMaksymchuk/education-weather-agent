"""System tests: bot handlers with fake agent, no real LLM."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from weather_agent.bot import (
    WELCOME_TEXT,
    HELP_TEXT,
    start,
    help_command,
    handle_message,
    build_application,
)


def _make_update(text: str | None = None):
    """Build a minimal Update with message and chat for handlers."""
    update = MagicMock()
    update.effective_chat = MagicMock()
    update.effective_chat.id = 12345
    if text is not None:
        update.message = MagicMock()
        update.message.text = text
        update.message.reply_text = AsyncMock()
    else:
        update.message = None
    return update


def _make_context():
    context = MagicMock()
    context.bot = MagicMock()
    context.bot.send_chat_action = AsyncMock()
    return context


@pytest.mark.system_mock
@pytest.mark.asyncio
class TestBotHandlers:
    """E2E-style tests for bot with mocked agent."""

    async def test_start_sends_welcome(self):
        update = _make_update("/start")
        context = _make_context()
        await start(update, context)
        update.message.reply_text.assert_called_once_with(WELCOME_TEXT)

    async def test_help_sends_help_text(self):
        update = _make_update("/help")
        context = _make_context()
        await help_command(update, context)
        update.message.reply_text.assert_called_once_with(HELP_TEXT)

    async def test_handle_message_calls_agent_and_replies(self):
        update = _make_update("Що одягнути в Києві?")
        context = _make_context()
        with patch("weather_agent.bot.ask_agent", return_value="Одягни куртку та шапку."):
            await handle_message(update, context)
        update.message.reply_text.assert_called_once_with("Одягни куртку та шапку.")

    async def test_handle_message_no_text_does_not_reply(self):
        update = MagicMock()
        update.message = MagicMock()
        update.message.text = ""
        update.effective_chat = None
        context = _make_context()
        await handle_message(update, context)
        update.message.reply_text.assert_not_called()

    async def test_build_application_registers_handlers(self):
        app = build_application("fake-token")
        handlers = app.handlers
        assert handlers
        # Should have command and message handlers
        all_handlers = []
        for group in handlers.values():
            all_handlers.extend(group)
        assert len(all_handlers) >= 2
