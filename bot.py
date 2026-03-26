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
    "Привет! Я *Преживи* – твой сербский разговорник 🇷🇸\n\n"
    "Просто напиши мне бытовую ситуацию на русском, и я выдам "
    "готовые фразы на сербском.\n\n"
    "Например:\n"
    "• _Иду на почту забрать посылку_\n"
    "• _Хочу записаться к врачу_\n"
    "• _Нужно оплатить квитанцию в менячнице_\n\n"
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
    await update.message.reply_text(START_TEXT, parse_mode=ParseMode.MARKDOWN)


async def help_command(update: Update, context) -> None:
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.MARKDOWN)


async def sos(update: Update, context) -> None:
    await update.message.reply_text(SOS_PHRASES)


async def handle_message(update: Update, context) -> None:
    user_text = update.message.text
    logger.info("Request from %s: %s", update.effective_user.id, user_text)

    await update.message.chat.send_action(ChatAction.TYPING)

    reply = await generate_phrasebook(user_text)

    # Split long messages
    if len(reply) <= MAX_MESSAGE_LENGTH:
        await update.message.reply_text(reply)
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
            await update.message.reply_text(chunk)


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
