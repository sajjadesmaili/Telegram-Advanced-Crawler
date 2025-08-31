# 🤖 Telegram Advanced Crawler

A powerful and intelligent Telegram crawler that can collect messages from all your groups and channels with advanced deduplication, real-time monitoring, and comprehensive data management.

## ✨ Features

### 🔐 Smart Deduplication System
- **SHA256 Hash Generation**: Each message gets a unique hash based on `message_id + chat_id + text`
- **Duplicate Prevention**: Automatic detection and prevention of duplicate message storage
- **Database Integrity**: Ensures clean and consistent data without redundancy

### ⚡ Real-time Processing
- **Live Message Monitoring**: Instantly captures and processes new messages as they arrive
- **Event-driven Architecture**: Efficient real-time data collection with minimal resource usage
- **Automatic Storage**: New messages are immediately saved to the database

### 👥 Complete User Management
- **Contact Information**: Stores username, first_name, last_name, phone numbers
- **Message Capability**: All necessary data to send messages back to users
- **User Caching**: Optimized performance with intelligent user data caching

### 📊 Advanced Analytics
- **Message Statistics**: Total messages, daily counts, active groups
- **Search Functionality**: Powerful text search across all collected messages
- **Data Export**: JSON export with comprehensive message data

### 🗄️ Optimized Database Design
- **SQLite Backend**: Reliable local database storage
- **Indexed Tables**: Fast queries with strategic database indexing
- **Relational Structure**: Proper foreign key relationships for data integrity

## 🚀 Quick Start

### Prerequisites

```bash
pip install telethon sqlite3 asyncio
```

### 1. Get Telegram API Credentials

1. Visit [my.telegram.org](https://my.telegram.org)
2. Log in with your phone number
3. Go to "API Development Tools"
4. Create a new application
5. Note down your `api_id` and `api_hash`

### 2. Configuration

```python
# Replace with your actual credentials
API_ID = 'your_api_id'
API_HASH = 'your_api_hash'  
PHONE_NUMBER = '+1234567890'
```

### 3. Basic Usage

```python
import asyncio
from telegram_crawler import TelegramCrawlerManager

async def main():
    manager = TelegramCrawlerManager(API_ID, API_HASH, PHONE_NUMBER)
    
    # Full crawl + real-time monitoring
    await manager.full_crawl_and_monitor(initial_messages_per_chat=500)

asyncio.run(main())
```

## 📖 Detailed Usage

### Complete Message Crawling

```python
# Initialize crawler
crawler = AdvancedTelegramCrawler(API_ID, API_HASH, PHONE_NUMBER)

# Crawl all groups and channels
await crawler.crawl_all_chats(messages_per_chat=1000)

# Get statistics
stats = crawler.get_chat_statistics()
print(f"Total messages: {stats['total_messages']}")
```

### Real-time Monitoring

```python
# Start real-time message monitoring
await crawler.start_real_time_monitoring()
```

### Search Messages

```python
# Search in all chats
results = crawler.search_messages("keyword", limit=100)

# Search in specific chat
results = crawler.search_messages("keyword", chat_title="Group Name")
```

### Get Contact Information

```python
# Get user contact details for messaging
contact = crawler.get_user_contact_info(user_id=123456789)
print(f"Telegram link: {contact['telegram_link']}")
print(f"Username: {contact['username']}")
print(f"Phone: {contact['phone']}")
```

### Export Data

```python
# Export to JSON
crawler.export_to_json('telegram_backup.json')
```

## 🏗️ Database Schema

### Messages Table
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_hash TEXT UNIQUE NOT NULL,
    message_id INTEGER,
    chat_id INTEGER,
    chat_title TEXT,
    sender_id INTEGER,
    text TEXT,
    date TIMESTAMP,
    -- ... additional fields
)
```

### Users Table
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    phone TEXT,
    is_bot BOOLEAN,
    -- ... timestamps
)
```

### Chats Table
```sql
CREATE TABLE chats (
    chat_id INTEGER PRIMARY KEY,
    title TEXT,
    username TEXT,
    chat_type TEXT,
    members_count INTEGER,
    -- ... additional metadata
)
```

## 🔧 Configuration Options

### Crawling Parameters

```python
# Adjust messages per chat
await crawler.crawl_all_chats(messages_per_chat=2000)

# Set rate limiting delay
await asyncio.sleep(2)  # Between chat processing
```

### Search Parameters

```python
# Limit search results
results = crawler.search_messages("query", limit=50)

# Filter by chat
results = crawler.search_messages("query", chat_title="Specific Group")
```

## 📊 Statistics and Analytics

```python
stats = crawler.get_chat_statistics()

# Available statistics:
# - total_messages: Total collected messages
# - total_chats: Number of groups/channels
# - total_users: Unique users encountered
# - today_messages: Messages collected today
# - most_active_chats: Top 5 most active groups
```

## ⚠️ Important Considerations

### Legal and Ethical Guidelines

- **Public Content Only**: Only collect data from public channels or groups you're a member of
- **Respect Privacy**: Do not collect or share private group content without permission
- **Terms of Service**: Comply with Telegram's Terms of Service
- **Local Laws**: Follow your local data protection and privacy laws
- **Rate Limiting**: Respect Telegram's API rate limits to avoid being banned

### Best Practices

1. **Transparency**: Inform group members if you're collecting data
2. **Minimal Data**: Only collect necessary information
3. **Secure Storage**: Keep collected data secure and encrypted
4. **Regular Cleanup**: Periodically remove old or unnecessary data
5. **Consent**: Obtain consent when possible, especially for private groups

### Security Considerations

- Store API credentials securely (use environment variables)
- Regularly backup your database
- Use strong passwords for database encryption if needed
- Be cautious about sharing collected data

## 🛠️ Troubleshooting

### Common Issues

**Authentication Errors**
```bash
# Make sure your API credentials are correct
# Check if your phone number format is international (+country_code)
```

**Database Locked**
```python
# Close existing connections
crawler.close_connection()
```

**Rate Limiting**
```python
# Increase delays between requests
await asyncio.sleep(3)
```

### Performance Optimization

```python
# For large datasets, consider:
# 1. Batch processing
# 2. Database indexing
# 3. Memory management
# 4. Regular maintenance

# Example: Process in smaller batches
await crawler.crawl_chat_messages(chat_id, limit=500)
```

## 📝 Example Output

```json
{
  "export_date": "2025-08-31T10:30:00",
  "total_messages": 15420,
  "messages": [
    {
      "hash": "a1b2c3d4...",
      "message_id": 12345,
      "chat_title": "Tech Discussion Group",
      "sender_username": "@johndoe",
      "text": "Hello everyone!",
      "date": "2025-08-31 09:15:30"
    }
  ]
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚖️ Disclaimer

This tool is provided for educational and personal use only. Users are responsible for ensuring their use complies with:

- Telegram's Terms of Service
- Local privacy and data protection laws
- Ethical guidelines for data collection
- Respect for user privacy and consent

The authors are not responsible for any misuse of this tool or any legal consequences arising from its use.

## 🙋‍♂️ Support

If you encounter any issues or have questions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review [Telegram's API documentation](https://docs.telethon.dev/)
3. Open an issue on GitHub

## 🔄 Changelog

### v1.0.0
- Initial release
- Basic message crawling functionality
- Hash-based deduplication system
- Real-time monitoring
- SQLite database integration
- User contact information storage
- Search and export capabilities

---

**Made with ❤️ for the Telegram community**
