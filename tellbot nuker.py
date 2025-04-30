from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext
import asyncio

TOKEN = 'YOUR_BOT_TOKEN'  # Replace with your bot token

async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("ID", callback_data='id')],
        [InlineKeyboardButton("Group", callback_data='group')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Choose one:', reply_markup=reply_markup)

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'id':
        for count in range(100):
            try:
                await context.bot.send_message(chat_id=query.message.chat.id, text=f"Hi ID {count}")
                await asyncio.sleep(0.5)  # Use asyncio.sleep for non-blocking delay
            except Exception as e:
                print(f"Error sending message: {e}")
                break

    elif query.data == 'group':
        for count in range(100):
            try:
                await context.bot.send_message(chat_id=query.message.chat.id, text=f"Hi Group {count}")
                await asyncio.sleep(0.5)  # Use asyncio.sleep for non-blocking delay
            except Exception as e:
                print(f"Error sending message: {e}")
                break

async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    print("Bot is running...")
    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
