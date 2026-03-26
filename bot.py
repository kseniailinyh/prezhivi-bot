import html
import logging
import os

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from llm import generate_phrasebook
from prompts import SOS_PHRASES

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

START_TEXT = (
    "Привет! Я <b>Преживи</b> – твой сербский разговорник 🇷🇸\n\n"
    "Просто напиши мне бытовую ситуацию на русском, и я выдам "
    "готовые фразы на сербском.\n\n"
    "Например:\n"
    "• <i>Иду на почту забрать посылку</i>\n"
    "• <i>Хочу записаться к врачу</i>\n"
    "• <i>Нужно оплатить квитанцию в менячнице</i>\n\n"
    "Команды:\n"
    "/sos – фразы-спасатели на все случаи жизни\n"
    "/help – краткая справка"
)

HELP_TEXT = (
    "Напиши любую бытовую ситуацию на русском – "
    "я отвечу мини-разговорником на сербском.\n\n"
    "/sos – универсальные фразы-спасатели\n"
    "/start – начать сначала"
)

MAX_MESSAGE_LENGTH = 4096


async def start(update: Update, context) -> None:
    await update.message.reply_text(START_TEXT, parse_mode=ParseMode.HTML)


async def help_command(update: Update, context) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)


async def sos(update: Update, context) -> None:
    await update.message.reply_text(SOS_PHRASES, parse_mode=ParseMode.HTML)


def _sanitize_html(text: str) -> str:
    """Escape stray HTML entities while preserving allowed <b> and <i> tags."""
    # Temporarily replace allowed tags with placeholders
    replacements = {
        "<b>": "\x00b\x00", "</b>": "\x00/b\x00",
        "<i>": "\x00i\x00", "</i>": "\x00/i\x00",
    }
    for tag, placeholder in replacements.items():
        text = text.replace(tag, placeholder)
    # Escape everything else
    text = html.escape(text)
    # Restore allowed tags
    for tag, placeholder in replacements.items():
        text = text.replace(placeholder, tag)
    return text


async def _send_reply(update: Update, text: str) -> None:
    """Send a reply with HTML parse mode, falling back to plain text on error."""
    try:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    except Exception:
        logger.warning("HTML parse failed, sending as plain text")
        await update.message.reply_text(text)


async def handle_message(update: Update, context) -> None:
    user_text = update.message.text
    logger.info("Request from %s: %s", update.effective_user.id, user_text)

    await update.message.chat.send_action(ChatAction.TYPING)

    reply = await generate_phrasebook(user_text)
    reply = _sanitize_html(reply)

    # Split long messages
    if len(reply) <= MAX_MESSAGE_LENGTH:
        await _send_reply(update, reply)
    else:
        chunks: list[str] = []
        while reply:
            if len(reply) <= MAX_MESSAGE_LENGTH:
                chunks.append(reply)
                break
            split_pos = reply.rfind("\n", 0, MAX_MESSAGE_LENGTH)
            if split_pos == -1:
                split_pos = MAX_MESSAGE_LENGTH
            chunks.append(reply[:split_pos])
            reply = reply[split_pos:].lstrip("\n")

        for chunk in chunks:
            await _send_reply(update, chunk)


def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("sos", sos))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
