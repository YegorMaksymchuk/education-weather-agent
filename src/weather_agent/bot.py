"""Telegram-бот: обробник повідомлень та запуск long polling."""

import asyncio
import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from weather_agent.agent import ask_agent

logger = logging.getLogger(__name__)

WELCOME_TEXT = (
    "Привіт! Я допоможу підібрати одяг за погодою. "
    "Напиши місто або запитай, наприклад: Що одягнути в Києві?"
)

HELP_TEXT = """Я радю, що вдягнути за поточною погодою.

Приклади запитів:
• Що одягнути в Києві?
• Як одягнутися сьогодні у Львові?
• Погода в Одесі — що вдягнути?

Команди:
/start — привітання та початок спілкування
/help — ця допомога"""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробник команди /start — привітання."""
    if update.message:
        await update.message.reply_text(WELCOME_TEXT)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробник команди /help — текст допомоги."""
    if update.message:
        await update.message.reply_text(HELP_TEXT)


async def _typing_loop(
    bot,
    chat_id: int,
    done: asyncio.Event,
    interval: float = 4.0,
) -> None:
    """Періодично надсилає send_chat_action(TYPING), поки done не встановлено."""
    while not done.is_set():
        try:
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        except Exception:
            break
        try:
            await asyncio.wait_for(done.wait(), timeout=interval)
        except asyncio.TimeoutError:
            continue


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обробляє текстове повідомлення: викликає агента й відправляє відповідь."""
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    chat_id = update.effective_chat.id if update.effective_chat else None
    if not chat_id:
        return

    done = asyncio.Event()
    typing_task = asyncio.create_task(
        _typing_loop(context.bot, chat_id, done)
    )
    try:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        reply = await asyncio.to_thread(ask_agent, user_text)
    except SystemExit:
        done.set()
        typing_task.cancel()
        raise
    except Exception as e:
        logger.exception("Помилка при виклику агента: %s", e)
        reply = "Виникла помилка. Спробуйте пізніше."
    finally:
        done.set()
        typing_task.cancel()
        try:
            await typing_task
        except asyncio.CancelledError:
            pass

    await update.message.reply_text(reply)


def build_application(token: str) -> Application:
    """Збирає Application з обробниками команд та повідомлень."""
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    return app
