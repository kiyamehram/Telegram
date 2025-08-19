import asyncio
import random
import time
import json
import csv
import os
from datetime import datetime
from telethon import TelegramClient, events, functions, types
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SelfBot:
    def __init__(self):
        self.user_code = input("Please enter user code: ")
        self.phone_number = input("Please enter phone number: ")
        self.client = None
        self.spam_tasks = []
        self.mute_list = set()
        self.reaction_spam_tasks = []
        self.logging_chats = set()
        self.auto_save_tasks = []
        
        Path("sessions").mkdir(exist_ok=True)
        Path("logs").mkdir(exist_ok=True)
        Path("saved_files").mkdir(exist_ok=True)
        
    async def connect(self):
        try:
            self.client = TelegramClient(
                session=f'sessions/{self.user_code}',
                api_id=2040,  # Public API ID
                api_hash='b18441a1ff607e10a989891a5462e627'  # Public API Hash
            )
            
            await self.client.start(phone=self.phone_number)
            logger.info("Successfully connected!")
            
            self.client.add_event_handler(self.handle_incoming_message, events.NewMessage)
            
            return True
            
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    async def handle_incoming_message(self, event):
        try:
            chat_id = event.chat_id
            sender_id = event.message.sender_id
            
            if sender_id in self.mute_list:
                await event.message.delete()
                logger.info(f"Deleted message from muted user: {sender_id}")
                return
            
            if chat_id in self.logging_chats:
                await self.log_message(event.message)
                
        except Exception as e:
            logger.error(f"Error handling incoming message: {e}")

    async def log_message(self, message):
        try:
            chat_id = message.chat_id
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            log_file = f"logs/chat_{chat_id}_{datetime.now().strftime('%Y%m%d')}.csv"
            
            file_exists = os.path.isfile(log_file)
            
            with open(log_file, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['timestamp', 'message_id', 'sender_id', 'message_text', 'media_type', 'file_path']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                if not file_exists:
                    writer.writeheader()
                
                file_path = None
                media_type = None
                
                if message.media:
                    file_path = await self.save_media(message, chat_id, timestamp)
                    media_type = type(message.media).__name__
                
                writer.writerow({
                    'timestamp': datetime.now().isoformat(),
                    'message_id': message.id,
                    'sender_id': message.sender_id,
                    'message_text': message.text or '',
                    'media_type': media_type,
                    'file_path': file_path or ''
                })
            
            logger.info(f"Logged message {message.id} from chat {chat_id}")
            
        except Exception as e:
            logger.error(f"Error logging message: {e}")

    async def save_media(self, message, chat_id, timestamp):
        try:
            if isinstance(message.media, (MessageMediaPhoto, MessageMediaDocument)):
                file_name = f"chat_{chat_id}_{message.id}_{timestamp}"
                file_path = await message.download_media(file=f"saved_files/{file_name}")
                return file_path
        except Exception as e:
            logger.error(f"Error saving media: {e}")
        return None

    async def start_chat_logging(self, chat_id):
        try:
            self.logging_chats.add(chat_id)
            logger.info(f"Started logging chat: {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Error starting chat logging: {e}")
            return False

    async def stop_chat_logging(self, chat_id):
        try:
            if chat_id in self.logging_chats:
                self.logging_chats.remove(chat_id)
                logger.info(f"Stopped logging chat: {chat_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error stopping chat logging: {e}")
            return False

    async def show_logged_chats(self):
        if not self.logging_chats:
            print("No chats are being logged")
            return
        
        print("Logged chats:")
        for chat_id in self.logging_chats:
            try:
                chat = await self.client.get_entity(chat_id)
                chat_name = getattr(chat, 'title', getattr(chat, 'username', f'ID: {chat_id}'))
                print(f"ID: {chat_id} | Name: {chat_name}")
            except:
                print(f"ID: {chat_id} | Name: Unknown")

    async def export_chat_logs(self, chat_id, format_type='csv'):
        try:
            log_file = f"logs/chat_{chat_id}_*.csv"
            files = [f for f in os.listdir('logs') if f.startswith(f'chat_{chat_id}_')]
            
            if not files:
                print(f"No logs found for chat {chat_id}")
                return False
            
            export_data = []
            for file in files:
                with open(f"logs/{file}", 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    export_data.extend(list(reader))
            
            if format_type.lower() == 'json':
                export_file = f"logs/chat_{chat_id}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(export_file, 'w', encoding='utf-8') as jsonfile:
                    json.dump(export_data, jsonfile, ensure_ascii=False, indent=2)
            else:
                export_file = f"logs/chat_{chat_id}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                with open(export_file, 'w', newline='', encoding='utf-8') as csvfile:
                    if export_data:
                        writer = csv.DictWriter(csvfile, fieldnames=export_data[0].keys())
                        writer.writeheader()
                        writer.writerows(export_data)
            
            logger.info(f"Exported logs to: {export_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting logs: {e}")
            return False

    async def timed_file_save(self, chat_id, interval_minutes=60):
        try:
            while True:
                await asyncio.sleep(interval_minutes * 60)
                
                messages = await self.client.get_messages(chat_id, limit=50)
                media_messages = [msg for msg in messages if msg.media]
                
                for message in media_messages:
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    await self.save_media(message, chat_id, timestamp)
                
                logger.info(f"Auto-saved {len(media_messages)} files from chat {chat_id}")
                
        except asyncio.CancelledError:
            logger.info(f"Stopped auto-save for chat {chat_id}")
        except Exception as e:
            logger.error(f"Error in timed file save: {e}")

    async def start_timed_save(self, chat_id, interval_minutes):
        try:
            task = asyncio.create_task(self.timed_file_save(chat_id, interval_minutes))
            self.auto_save_tasks.append((chat_id, task))
            logger.info(f"Started timed file saving for chat {chat_id} every {interval_minutes} minutes")
            return True
        except Exception as e:
            logger.error(f"Error starting timed save: {e}")
            return False

    async def stop_timed_save(self, chat_id):
        try:
            for i, (cid, task) in enumerate(self.auto_save_tasks):
                if cid == chat_id:
                    task.cancel()
                    self.auto_save_tasks.pop(i)
                    logger.info(f"Stopped timed file saving for chat {chat_id}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error stopping timed save: {e}")
            return False

    async def join_via_invite(self, invite_link):
        try:
            if 't.me/' in invite_link:
                invite_hash = invite_link.split('/')[-1]
                await self.client(ImportChatInviteRequest(invite_hash))
                logger.info(f"Successfully joined group: {invite_link}")
                return True
        except Exception as e:
            logger.error(f"Error joining group: {e}")
            return False

    async def spam_messages(self, chat_id, messages, delay=1, count=10):
        try:
            for i in range(count):
                message = random.choice(messages) if isinstance(messages, list) else messages
                await self.client.send_message(chat_id, f"{message} ({i+1})")
                logger.info(f"Message {i+1} sent to {chat_id}")
                await asyncio.sleep(delay)
        except Exception as e:
            logger.error(f"Error sending spam: {e}")

    async def reaction_spam(self, chat_id, message_id, reactions, delay=2, count=20):
        try:
            for i in range(count):
                reaction = random.choice(reactions) if isinstance(reactions, list) else reactions
                await self.client.send_reaction(chat_id, message_id, reaction)
                logger.info(f"Reaction {i+1} sent: {reaction}")
                await asyncio.sleep(delay)
        except Exception as e:
            logger.error(f"Error sending reactions: {e}")

    async def group_nuke(self, group_id, messages, nuke_count=50):
        try:
            tasks = []
            for i in range(nuke_count):
                message = random.choice(messages) if isinstance(messages, list) else messages
                task = asyncio.create_task(
                    self.client.send_message(
                        group_id, 
                        f"💣 NUKE ATTACK {i+1}\n{message}"
                    )
                )
                tasks.append(task)
                await asyncio.sleep(0.1)
            
            await asyncio.gather(*tasks)
            logger.info(f"Nuke attack on group {group_id} completed!")
            
        except Exception as e:
            logger.error(f"Error in nuke attack: {e}")

    async def get_chat_info(self, chat_id):
        try:
            chat = await self.client.get_entity(chat_id)
            return chat
        except Exception as e:
            logger.error(f"Error getting chat info: {e}")
            return None

    async def leave_chat(self, chat_id):
        try:
            await self.client(functions.messages.LeaveChatRequest(chat_id=chat_id))
            logger.info(f"Left chat: {chat_id}")
        except Exception as e:
            logger.error(f"Error leaving chat: {e}")

    async def delete_messages(self, chat_id, message_ids):
        try:
            await self.client.delete_messages(chat_id, message_ids)
            logger.info(f"Deleted {len(message_ids)} messages")
        except Exception as e:
            logger.error(f"Error deleting messages: {e}")

    async def mute_user(self, user_id):
        try:
            self.mute_list.add(user_id)
            logger.info(f"User {user_id} added to mute list")
            return True
        except Exception as e:
            logger.error(f"Error muting user: {e}")
            return False

    async def unmute_user(self, user_id):
        try:
            if user_id in self.mute_list:
                self.mute_list.remove(user_id)
                logger.info(f"User {user_id} removed from mute list")
                return True
            return False
        except Exception as e:
            logger.error(f"Error unmuting user: {e}")
            return False

    async def show_muted_users(self):
        if not self.mute_list:
            print("No users are muted")
            return
        
        print("Muted users:")
        for user_id in self.mute_list:
            try:
                user = await self.client.get_entity(user_id)
                print(f"ID: {user_id} | Name: {user.first_name if user.first_name else 'Unknown'}")
            except:
                print(f"ID: {user_id} | Name: Unknown")

    async def run_spam_task(self, target, messages, delay, count):
        task = asyncio.create_task(
            self.spam_messages(target, messages, delay, count)
        )
        self.spam_tasks.append(task)
        return task

    async def run_reaction_spam_task(self, chat_id, message_id, reactions, delay, count):
        task = asyncio.create_task(
            self.reaction_spam(chat_id, message_id, reactions, delay, count)
        )
        self.reaction_spam_tasks.append(task)
        return task

    async def stop_all_spam(self):
        for task in self.spam_tasks + self.reaction_spam_tasks:
            task.cancel()
        
        self.spam_tasks.clear()
        self.reaction_spam_tasks.clear()
        logger.info("All spam tasks stopped")

    async def stop_all_auto_save(self):
        for chat_id, task in self.auto_save_tasks:
            task.cancel()
        self.auto_save_tasks.clear()
        logger.info("All auto-save tasks stopped")

    def show_menu(self):
        print("\n" + "="*70)
        print("🛡️ Telegram Self Bot - Main Menu")
        print("="*70)
        print("1. Send spam to user/group")
        print("2. Reaction spam on message")
        print("3. Nuke attack on group")
        print("4. Join group with invite link")
        print("5. Get chat information")
        print("6. Leave chat")
        print("7. Delete messages")
        print("8. Mute user (auto-delete DMs)")
        print("9. Unmute user")
        print("10. Show muted users")
        print("11. Start chat logging")
        print("12. Stop chat logging")
        print("13. Show logged chats")
        print("14. Export chat logs")
        print("15. Start timed file save")
        print("16. Stop timed file save")
        print("17. Stop all spam tasks")
        print("18. Stop all auto-save tasks")
        print("19. Exit")
        print("="*70)

    async def handle_choice(self, choice):
        try:
            if choice == '1':
                target = input("Target chat ID: ")
                messages = input("Messages (comma separated): ").split(',')
                delay = float(input("Delay between messages (seconds): "))
                count = int(input("Number of messages: "))
                await self.run_spam_task(target, messages, delay, count)

            elif choice == '2':
                chat_id = input("Chat ID: ")
                message_id = int(input("Message ID: "))
                reactions = input("Reactions (comma separated, e.g. 👍,❤️,🔥): ").split(',')
                delay = float(input("Delay between reactions (seconds): "))
                count = int(input("Number of reactions: "))
                await self.run_reaction_spam_task(chat_id, message_id, reactions, delay, count)

            elif choice == '3':
                group_id = input("Group ID: ")
                message = input("Attack message: ")
                count = int(input("Attack count: "))
                await self.group_nuke(group_id, message, count)

            elif choice == '4':
                invite_link = input("Invite link: ")
                await self.join_via_invite(invite_link)

            elif choice == '5':
                chat_id = input("Chat ID: ")
                info = await self.get_chat_info(chat_id)
                if info:
                    print(f"Chat info: {info}")

            elif choice == '6':
                chat_id = input("Chat ID: ")
                await self.leave_chat(chat_id)

            elif choice == '7':
                chat_id = input("Chat ID: ")
                msg_ids = list(map(int, input("Message IDs (comma separated): ").split(',')))
                await self.delete_messages(chat_id, msg_ids)

            elif choice == '8':
                user_id = int(input("User ID to mute: "))
                await self.mute_user(user_id)

            elif choice == '9':
                user_id = int(input("User ID to unmute: "))
                await self.unmute_user(user_id)

            elif choice == '10':
                await self.show_muted_users()

            elif choice == '11':
                chat_id = int(input("Chat ID to start logging: "))
                await self.start_chat_logging(chat_id)

            elif choice == '12':
                chat_id = int(input("Chat ID to stop logging: "))
                await self.stop_chat_logging(chat_id)

            elif choice == '13':
                await self.show_logged_chats()

            elif choice == '14':
                chat_id = int(input("Chat ID to export logs: "))
                format_type = input("Export format (csv/json): ").lower() or 'csv'
                await self.export_chat_logs(chat_id, format_type)

            elif choice == '15':
                chat_id = int(input("Chat ID for auto-save: "))
                interval = int(input("Interval in minutes: "))
                await self.start_timed_save(chat_id, interval)

            elif choice == '16':
                chat_id = int(input("Chat ID to stop auto-save: "))
                await self.stop_timed_save(chat_id)

            elif choice == '17':
                await self.stop_all_spam()

            elif choice == '18':
                await self.stop_all_auto_save()

            elif choice == '19':
                return False
                
            else:
                print("⚠️ Invalid choice!")
                
            return True
            
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return True

    async def main(self):
        if await self.connect():
            print("Bot is running! Incoming messages from muted users will be auto-deleted.")
            
            while True:
                self.show_menu()
                choice = input("Please select an option: ")
                
                if not await self.handle_choice(choice):
                    break
                
                await asyncio.sleep(1)

if __name__ == "__main__":
    bot = SelfBot()
    asyncio.run(bot.main())
