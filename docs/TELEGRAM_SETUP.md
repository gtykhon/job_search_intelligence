# Telegram Bot Setup Guide

## Step 1: Create a Telegram Bot

1. **Open Telegram** and search for `@BotFather`
2. **Start a chat** with BotFather by clicking "Start" or sending `/start`
3. **Create a new bot** by sending `/newbot`
4. **Choose a name** for your bot (e.g., "Job Search Intelligence Bot")
5. **Choose a username** for your bot (must end with "bot", e.g., "job_search_intelligence_bot")
6. **Copy the bot token** that BotFather provides (looks like `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

## Step 2: Get Your Chat ID

### Option A: Direct Message (Recommended)
1. **Start a chat** with your new bot by searching for its username
2. **Send any message** to the bot (e.g., "Hello")
3. **Use the test script** below to get your chat ID

### Option B: Group Chat
1. **Add the bot** to a group chat
2. **Send a message** mentioning the bot (e.g., "Hello @your_bot_username")
3. **Use the test script** to get the group chat ID

## Step 3: Configure Your .env File

Update your `.env` file with the bot token and chat ID:

```env
# Telegram notifications
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=your_chat_id_here
```

## Step 4: Test the Integration

Use the test script below to verify everything is working correctly.

---

## Important Notes

- **Keep your bot token secret** - never share it publicly
- **Chat ID can be negative** for group chats (this is normal)
- **The bot needs to receive at least one message** before you can get the chat ID
- **For group chats**, make sure the bot has permission to send messages

## Telegram Message Features

Your Job Search Intelligence notifications will include:
- 📊 **Rich formatting** with emojis and HTML
- ⚠️ **Priority indicators** for important alerts
- 🕒 **Timestamps** for all notifications
- 📱 **Mobile-friendly** formatting
- 🔗 **No link previews** to keep messages clean

## Privacy and Security

- **Bot only sends messages** - it cannot read your other chats
- **Messages are encrypted** in transit to Telegram servers
- **No personal data** is stored on Telegram servers by the bot
- **You control** what notifications are sent
