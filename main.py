import asyncio
import json
import sqlite3
import hashlib
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import PeerChannel, PeerChat, PeerUser, User, Chat, Channel
import logging

# تنظیمات لاگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedTelegramCrawler:
    def __init__(self, api_id, api_hash, phone_number):
        """
        مقداردهی کرولر تلگرام پیشرفته
        
        Args:
            api_id: شناسه API از my.telegram.org
            api_hash: هش API از my.telegram.org  
            phone_number: شماره تلفن حساب تلگرام
        """
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.client = TelegramClient('telegram_session', api_id, api_hash)
        
        # ایجاد دیتابیس
        self.setup_database()
        
        # کش برای اطلاعات کاربران (برای بهبود عملکرد)
        self.user_cache = {}
    
    def setup_database(self):
        """ایجاد جداول دیتابیس با ساختار بهینه"""
        self.conn = sqlite3.connect('telegram_advanced.db', check_same_thread=False)
        cursor = self.conn.cursor()
        
        # جدول کاربران (برای ذخیره اطلاعات ارسال‌کنندگان)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                is_bot BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول پیام‌ها با هش یکتا
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_hash TEXT UNIQUE NOT NULL,
                message_id INTEGER,
                chat_id INTEGER,
                chat_title TEXT,
                chat_username TEXT,
                sender_id INTEGER,
                sender_username TEXT,
                sender_first_name TEXT,
                sender_last_name TEXT,
                text TEXT,
                date TIMESTAMP,
                reply_to_message_id INTEGER,
                forward_from_chat_id INTEGER,
                media_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users (user_id)
            )
        ''')
        
        # جدول گروه‌ها/کانال‌ها
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                chat_id INTEGER PRIMARY KEY,
                title TEXT,
                username TEXT,
                chat_type TEXT,
                members_count INTEGER,
                description TEXT,
                invite_link TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ایندکس‌ها برای بهبود عملکرد
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_hash ON messages(message_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_id ON messages(chat_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sender_id ON messages(sender_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date ON messages(date)')
        
        self.conn.commit()
        logger.info("دیتابیس با موفقیت راه‌اندازی شد")
    
    def generate_message_hash(self, message_id, chat_id, text):
        """ایجاد هش یکتا برای هر پیام"""
        hash_input = f"{message_id}_{chat_id}_{text}"
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    
    def message_exists(self, message_hash):
        """بررسی وجود پیام در دیتابیس"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM messages WHERE message_hash = ? LIMIT 1', (message_hash,))
        return cursor.fetchone() is not None
    
    async def start_client(self):
        """شروع کلاینت تلگرام"""
        await self.client.start(phone=self.phone_number)
        logger.info("کلاینت تلگرام با موفقیت متصل شد")
        
        # دریافت اطلاعات خود کاربر
        me = await self.client.get_me()
        logger.info(f"وارد شده به عنوان: {me.first_name} (@{me.username})")
    
    async def save_user_info(self, user):
        """ذخیره یا بروزرسانی اطلاعات کاربر"""
        if not user or not hasattr(user, 'id'):
            return
            
        user_id = user.id
        
        # چک کش
        if user_id in self.user_cache:
            return self.user_cache[user_id]
        
        cursor = self.conn.cursor()
        
        user_data = {
            'user_id': user_id,
            'username': getattr(user, 'username', None),
            'first_name': getattr(user, 'first_name', None),
            'last_name': getattr(user, 'last_name', None),
            'phone': getattr(user, 'phone', None),
            'is_bot': getattr(user, 'bot', False)
        }
        
        cursor.execute('''
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, phone, is_bot, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            user_data['user_id'],
            user_data['username'],
            user_data['first_name'],
            user_data['last_name'],
            user_data['phone'],
            user_data['is_bot']
        ))
        
        self.conn.commit()
        
        # اضافه به کش
        self.user_cache[user_id] = user_data
        return user_data
    
    async def save_chat_info(self, chat):
        """ذخیره اطلاعات گروه/کانال"""
        cursor = self.conn.cursor()
        
        chat_data = {
            'chat_id': chat.id,
            'title': getattr(chat, 'title', None),
            'username': getattr(chat, 'username', None),
            'chat_type': type(chat).__name__,
            'members_count': getattr(chat, 'participants_count', 0),
            'description': getattr(chat, 'about', None)
        }
        
        # تلاش برای دریافت لینک دعوت (اگر مجاز باشیم)
        invite_link = None
        try:
            if hasattr(chat, 'username') and chat.username:
                invite_link = f"https://t.me/{chat.username}"
            else:
                # برای گروه‌های خصوصی، لینک دعوت دریافت کنیم
                exported_invite = await self.client.get_permissions(chat)
                if exported_invite:
                    invite_link = "private_group"
        except:
            pass
        
        cursor.execute('''
            INSERT OR REPLACE INTO chats 
            (chat_id, title, username, chat_type, members_count, description, invite_link, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            chat_data['chat_id'],
            chat_data['title'],
            chat_data['username'],
            chat_data['chat_type'],
            chat_data['members_count'],
            chat_data['description'],
            invite_link
        ))
        
        self.conn.commit()
        return chat_data
    
    async def save_message(self, message, chat_info=None):
        """ذخیره پیام با بررسی تکراری بودن"""
        if not message or not message.text:
            return False
        
        # ایجاد هش پیام
        message_hash = self.generate_message_hash(
            message.id, 
            message.chat_id if hasattr(message, 'chat_id') else message.peer_id.channel_id,
            message.text
        )
        
        # بررسی وجود پیام
        if self.message_exists(message_hash):
            logger.debug(f"پیام با هش {message_hash[:8]}... قبلاً ذخیره شده")
            return False
        
        # دریافت اطلاعات فرستنده
        sender_info = None
        if message.sender_id:
            try:
                sender = await self.client.get_entity(message.sender_id)
                sender_info = await self.save_user_info(sender)
            except Exception as e:
                logger.warning(f"خطا در دریافت اطلاعات فرستنده {message.sender_id}: {e}")
        
        # دریافت اطلاعات چت (اگر ارائه نشده)
        if not chat_info:
            try:
                chat = await self.client.get_entity(message.peer_id)
                chat_info = await self.save_chat_info(chat)
            except Exception as e:
                logger.warning(f"خطا در دریافت اطلاعات چت: {e}")
                chat_info = {'title': 'Unknown', 'username': None}
        
        # تشخیص نوع رسانه
        media_type = None
        if message.media:
            media_type = type(message.media).__name__
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO messages 
            (message_hash, message_id, chat_id, chat_title, chat_username, 
             sender_id, sender_username, sender_first_name, sender_last_name,
             text, date, reply_to_message_id, forward_from_chat_id, media_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            message_hash,
            message.id,
            message.chat_id if hasattr(message, 'chat_id') else message.peer_id.channel_id,
            chat_info.get('title'),
            chat_info.get('username'),
            message.sender_id,
            sender_info.get('username') if sender_info else None,
            sender_info.get('first_name') if sender_info else None,
            sender_info.get('last_name') if sender_info else None,
            message.text,
            message.date,
            getattr(message, 'reply_to_msg_id', None),
            getattr(message.forward, 'from_id', None) if message.forward else None,
            media_type
        ))
        
        self.conn.commit()
        logger.info(f"پیام جدید ذخیره شد: {message.text[:50]}...")
        return True
    
    async def get_all_chats(self):
        """دریافت تمام گروه‌ها و کانال‌های کاربر"""
        chats = []
        
        async for dialog in self.client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:  # فقط گروه‌ها و کانال‌ها
                chat_info = await self.save_chat_info(dialog.entity)
                chats.append(chat_info)
        
        logger.info(f"تعداد {len(chats)} گروه/کانال پیدا شد")
        return chats
    
    async def crawl_chat_messages(self, chat_id, limit=1000):
        """کرول پیام‌های یک گروه/کانال خاص"""
        new_messages_count = 0
        
        try:
            chat = await self.client.get_entity(chat_id)
            chat_info = await self.save_chat_info(chat)
            
            logger.info(f"شروع کرول پیام‌ها از: {chat_info['title']}")
            
            async for message in self.client.iter_messages(chat_id, limit=limit):
                if message.text:  # فقط پیام‌های متنی
                    is_new = await self.save_message(message, chat_info)
                    if is_new:
                        new_messages_count += 1
            
            logger.info(f"تعداد {new_messages_count} پیام جدید از {chat_info['title']} ذخیره شد")
            
        except Exception as e:
            logger.error(f"خطا در کرول چت {chat_id}: {e}")
        
        return new_messages_count
    
    async def crawl_all_chats(self, messages_per_chat=1000):
        """کرول تمام گروه‌ها و کانال‌ها"""
        await self.start_client()
        
        # دریافت لیست گروه‌ها
        chats = await self.get_all_chats()
        
        total_new_messages = 0
        
        # کرول پیام‌ها از هر گروه
        for i, chat in enumerate(chats, 1):
            logger.info(f"[{i}/{len(chats)}] در حال پردازش: {chat['title']}")
            
            new_count = await self.crawl_chat_messages(chat['chat_id'], messages_per_chat)
            total_new_messages += new_count
            
            # توقف کوتاه برای جلوگیری از rate limiting
            await asyncio.sleep(1)
        
        logger.info(f"کرول کامل شد! تعداد کل پیام‌های جدید: {total_new_messages}")
        return total_new_messages
    
    def setup_real_time_listener(self):
        """تنظیم listener برای دریافت پیام‌های جدید به صورت real-time"""
        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            try:
                if event.text:  # فقط پیام‌های متنی
                    # بررسی اینکه از گروه یا کانال است
                    if hasattr(event.message.peer_id, 'channel_id') or hasattr(event.message.peer_id, 'chat_id'):
                        is_new = await self.save_message(event.message)
                        if is_new:
                            logger.info(f"پیام real-time جدید: {event.text[:50]}...")
            except Exception as e:
                logger.error(f"خطا در پردازش پیام real-time: {e}")
    
    async def start_real_time_monitoring(self):
        """شروع نظارت real-time بر پیام‌های جدید"""
        await self.start_client()
        self.setup_real_time_listener()
        
        logger.info("نظارت real-time شروع شد. برای توقف Ctrl+C بزنید")
        await self.client.run_until_disconnected()
    
    def get_chat_statistics(self):
        """دریافت آمار کلی"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # تعداد کل پیام‌ها
        cursor.execute('SELECT COUNT(*) FROM messages')
        stats['total_messages'] = cursor.fetchone()[0]
        
        # تعداد کل گروه‌ها
        cursor.execute('SELECT COUNT(*) FROM chats')
        stats['total_chats'] = cursor.fetchone()[0]
        
        # تعداد کل کاربران
        cursor.execute('SELECT COUNT(*) FROM users')
        stats['total_users'] = cursor.fetchone()[0]
        
        # پیام‌های امروز
        cursor.execute('SELECT COUNT(*) FROM messages WHERE DATE(created_at) = DATE("now")')
        stats['today_messages'] = cursor.fetchone()[0]
        
        # فعال‌ترین گروه‌ها
        cursor.execute('''
            SELECT chat_title, COUNT(*) as message_count 
            FROM messages 
            GROUP BY chat_id, chat_title 
            ORDER BY message_count DESC 
            LIMIT 5
        ''')
        stats['most_active_chats'] = cursor.fetchall()
        
        return stats
    
    def search_messages(self, query, chat_title=None, limit=100):
        """جستجو در پیام‌ها"""
        cursor = self.conn.cursor()
        
        if chat_title:
            cursor.execute('''
                SELECT m.*, c.title as chat_title, u.username as sender_username
                FROM messages m
                LEFT JOIN chats c ON m.chat_id = c.chat_id
                LEFT JOIN users u ON m.sender_id = u.user_id
                WHERE m.text LIKE ? AND c.title LIKE ?
                ORDER BY m.date DESC
                LIMIT ?
            ''', (f'%{query}%', f'%{chat_title}%', limit))
        else:
            cursor.execute('''
                SELECT m.*, c.title as chat_title, u.username as sender_username
                FROM messages m
                LEFT JOIN chats c ON m.chat_id = c.chat_id
                LEFT JOIN users u ON m.sender_id = u.user_id
                WHERE m.text LIKE ?
                ORDER BY m.date DESC
                LIMIT ?
            ''', (f'%{query}%', limit))
        
        return cursor.fetchall()
    
    def get_user_contact_info(self, user_id):
        """دریافت اطلاعات تماس کاربر"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT user_id, username, first_name, last_name, phone
            FROM users 
            WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        if result:
            contact_info = {
                'user_id': result[0],
                'username': f"@{result[1]}" if result[1] else None,
                'full_name': f"{result[2] or ''} {result[3] or ''}".strip(),
                'phone': result[4],
                'telegram_link': f"tg://user?id={result[0]}"
            }
            return contact_info
        return None
    
    def export_to_json(self, filename='telegram_advanced_data.json'):
        """صادر کردن داده‌ها به فایل JSON"""
        cursor = self.conn.cursor()
        
        # دریافت تمام داده‌ها
        cursor.execute('''
            SELECT 
                m.message_hash,
                m.message_id,
                m.chat_id,
                c.title as chat_title,
                c.username as chat_username,
                m.sender_id,
                u.username as sender_username,
                u.first_name as sender_first_name,
                u.last_name as sender_last_name,
                m.text,
                m.date,
                m.created_at
            FROM messages m
            LEFT JOIN chats c ON m.chat_id = c.chat_id
            LEFT JOIN users u ON m.sender_id = u.user_id
            ORDER BY m.date DESC
        ''')
        
        messages = cursor.fetchall()
        
        # تبدیل به فرمت JSON
        data = {
            'export_date': datetime.now().isoformat(),
            'total_messages': len(messages),
            'messages': []
        }
        
        for msg in messages:
            data['messages'].append({
                'hash': msg[0],
                'message_id': msg[1],
                'chat_id': msg[2],
                'chat_title': msg[3],
                'chat_username': msg[4],
                'sender_id': msg[5],
                'sender_username': msg[6],
                'sender_name': f"{msg[7] or ''} {msg[8] or ''}".strip(),
                'text': msg[9],
                'date': str(msg[10]),
                'created_at': str(msg[11])
            })
        
        # ذخیره در فایل
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"داده‌ها در فایل {filename} صادر شد")
    
    def close_connection(self):
        """بستن اتصال دیتابیس"""
        if self.conn:
            self.conn.close()

# کلاس مدیریت اجرای مختلط
class TelegramCrawlerManager:
    def __init__(self, api_id, api_hash, phone_number):
        self.crawler = AdvancedTelegramCrawler(api_id, api_hash, phone_number)
    
    async def full_crawl_and_monitor(self, initial_messages_per_chat=1000):
        """اجرای کامل: کرول اولیه + نظارت real-time"""
        try:
            logger.info("=== شروع کرول کامل ===")
            
            # مرحله 1: کرول اولیه
            total_new = await self.crawler.crawl_all_chats(initial_messages_per_chat)
            
            # نمایش آمار
            stats = self.crawler.get_chat_statistics()
            logger.info(f"آمار کلی: {stats}")
            
            # مرحله 2: شروع نظارت real-time
            logger.info("=== شروع نظارت Real-time ===")
            await self.crawler.start_real_time_monitoring()
            
        except KeyboardInterrupt:
            logger.info("کرولر توسط کاربر متوقف شد")
        except Exception as e:
            logger.error(f"خطای غیرمنتظره: {e}")
        finally:
            self.crawler.close_connection()
    
    async def search_and_export_demo(self):
        """نمایش قابلیت‌های جستجو و صادرات"""
        await self.crawler.start_client()
        
        # نمایش آمار
        stats = self.crawler.get_chat_statistics()
        print("\n=== آمار کلی ===")
        for key, value in stats.items():
            if key != 'most_active_chats':
                print(f"{key}: {value}")
        
        print("\n=== فعال‌ترین گروه‌ها ===")
        for chat_name, msg_count in stats['most_active_chats']:
            print(f"- {chat_name}: {msg_count} پیام")
        
        # جستجوی نمونه
        sample_results = self.crawler.search_messages("سلام", limit=5)
        print(f"\n=== نمونه جستجو برای 'سلام' ({len(sample_results)} نتیجه) ===")
        for result in sample_results[:3]:
            print(f"- {result[4]}: {result[10][:100]}...")
        
        # صادرات
        self.crawler.export_to_json()
        
        self.crawler.close_connection()

# نحوه استفاده
async def main():
    # مقادیر خود را وارد کنید
    API_ID = 'your_api_id'  # از my.telegram.org
    API_HASH = 'your_api_hash'  # از my.telegram.org
    PHONE_NUMBER = '+989xxxxxxxxx'  # شماره تلفن شما
    
    manager = TelegramCrawlerManager(API_ID, API_HASH, PHONE_NUMBER)
    
    # انتخاب حالت اجرا
    mode = input("حالت اجرا را انتخاب کنید:\n1. کرول کامل + نظارت real-time\n2. نمایش آمار و صادرات\nشماره: ")
    
    if mode == "1":
        await manager.full_crawl_and_monitor(initial_messages_per_chat=500)
    elif mode == "2":
        await manager.search_and_export_demo()
    else:
        print("حالت نامعتبر!")

if __name__ == "__main__":
    asyncio.run(main())
