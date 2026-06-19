"""Entry point. Run with: python bot.py"""

import logging
import os
import tempfile
from datetime import date

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from reminders import reminder_message
from vision import extract_cheque

logging.basicConfig(
    format="%(asctime)s  %(levelname)s  %(name)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Send me a photo of a cheque and I'll read it for you."
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Got it — reading the cheque…")

    photo = update.message.photo[-1]  # highest resolution
    file = await photo.get_file()

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        tmp_path = tmp.name

    try:
        cheque = extract_cheque(tmp_path)
    except Exception as exc:
        logger.exception("Vision extraction failed")
        await update.message.reply_text(f"Could not read the cheque: {exc}")
        return
    finally:
        os.unlink(tmp_path)

    msg = reminder_message(cheque, today=date.today())
    await update.message.reply_text(msg)


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    doc = update.message.document
    if not doc.mime_type or not doc.mime_type.startswith("image/"):
        await update.message.reply_text("Please send an image file.")
        return

    await update.message.reply_text("Got it — reading the cheque…")
    file = await doc.get_file()

    suffix = "." + (doc.file_name or "img.jpg").rsplit(".", 1)[-1]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        await file.download_to_drive(tmp.name)
        tmp_path = tmp.name

    try:
        cheque = extract_cheque(tmp_path)
    except Exception as exc:
        logger.exception("Vision extraction failed")
        await update.message.reply_text(f"Could not read the cheque: {exc}")
        return
    finally:
        os.unlink(tmp_path)

    msg = reminder_message(cheque, today=date.today())
    await update.message.reply_text(msg)


def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.IMAGE, handle_document))

    logger.info("Bot starting…")
    app.run_polling()


if __name__ == "__main__":
    main()
