import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext
from telegram.constants import ChatType
import os
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("Please set the TELEGRAM_BOT_TOKEN environment variable")

async def start(update: Update, context: CallbackContext) -> None:
    if update.message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await update.message.reply_text("This command can only be used in groups.")
        return
    
    keyboard = [[InlineKeyboardButton("♱ Nuke Group ♱", callback_data='Nuke')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Ready to nuke? Press the button!", reply_markup=reply_markup)

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    chat_member = await context.bot.get_chat_member(query.message.chat.id, query.from_user.id)
    if chat_member.status not in ['administrator', 'creator']:
        await query.message.reply_text("Only administrators can use this feature.")
        return

    if query.data == 'Nuke':
        chat_id = query.message.chat.id
        
        bot_member = await context.bot.get_chat_member(chat_id, context.bot.id)
        if bot_member.status != 'administrator' or not bot_member.can_delete_messages or not bot_member.can_restrict_members:
            await query.message.reply_text("The bot must be an administrator with permissions to delete messages and restrict users.")
            return

        try:
            status_msg = await query.message.reply_text("🚀 Starting nuke operation...")
            
            deleted_count = 0
            latest_msg_id = query.message.message_id
            
            for message_id in range(latest_msg_id, max(1, latest_msg_id - 100), -1):
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                    deleted_count += 1
                    await asyncio.sleep(0.1)  
                except Exception:
                    continue  
            
            await status_msg.edit_text(f"✅ {deleted_count} messages deleted. Banning users...")
            
            banned_count = 0
            async for member in context.bot.get_chat_members(chat_id):
                if not member.user.is_bot and member.status not in ['administrator', 'creator']:
                    try:
                        await context.bot.ban_chat_member(chat_id=chat_id, user_id=member.user.id)
                        banned_count += 1
                        await asyncio.sleep(0.5)  
                    except Exception:
                        continue
            
            await status_msg.edit_text(f"✅ {deleted_count} messages deleted and {banned_count} users banned. Sending nuke messages...")
            
            for count in range(10):  
                try:
                    await context.bot.send_message(chat_id=chat_id, text=f"💥 Group Nuke! Number {count+1} 💥")
                    await asyncio.sleep(1)  
                except Exception as send_error:
                    logger.error(f"Error sending message: {send_error}")
                    break
            
            await status_msg.edit_text("✅ Nuke operation completed successfully.")
            
        except Exception as overall_error:
            logger.error(f"Error in nuke operation: {overall_error}")
            await query.message.reply_text(f"Error in nuke operation: {overall_error}")
    else:
        await query.message.reply_text("Invalid button.")

async def main():
    """Start the bot."""
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))

    logger.info("Bot is running...")
    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())

if __name__ == '__main__':

    asyncio.run(main())
