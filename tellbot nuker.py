import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext


TOKEN = 'YOUR_TOKEN_BOT'
bot = Bot(token=TOKEN)
bot.delete_webhook()


logging.basicConfig(level=logging.INFO)


async def start(update: Update, _context: CallbackContext) -> None:
    logging.info(f"Received /start command from {update.message.chat.id}")

    keyboard = [
        [InlineKeyboardButton("ID", callback_data='id')],
        [InlineKeyboardButton("Group", callback_data='group')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text('Choose one:', reply_markup=reply_markup)


async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    for count in range(100):
        try:
            text = f"XD ID {count}" if query.data == 'id' else f"Hi Group {count}"
            await context.bot.send_message(chat_id=query.message.chat.id, text=text)
            await asyncio.sleep(0.5)
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            break


async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    logging.info("Bot is running...")
    await app.run_polling()


if __name__ == '__main__':
    asyncio.run(main())


if __name__ == '__main__':
    asyncio.run(main())
