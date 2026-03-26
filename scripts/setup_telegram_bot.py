#!/usr/bin/env python3
"""
Interactive Telegram Bot Setup Assistant
Helps you create and configure a Telegram bot for Job Search Intelligence notifications
"""

import os
import asyncio
import sys
from pathlib import Path

def print_header():
    print("🤖 Telegram Bot Setup Assistant")
    print("=" * 50)
    print("This assistant will help you set up Telegram notifications")
    print("for your Job Search Intelligence.")
    print()

def create_bot_instructions():
    """Display instructions for creating a Telegram bot"""
    print("📋 Step 1: Create Your Telegram Bot")
    print("-" * 30)
    print()
    print("1. Open Telegram on your phone or computer")
    print("2. Search for '@BotFather' and start a chat")
    print("3. Send the command: /newbot")
    print("4. Choose a name for your bot (e.g., 'Job Search Intelligence Bot')")
    print("5. Choose a username ending with 'bot' (e.g., 'linkedin_intel_bot')")
    print("6. BotFather will give you a bot token that looks like:")
    print("   123456789:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
    print()
    print("🔑 IMPORTANT: Keep your bot token secret!")
    print()

def get_bot_token():
    """Get bot token from user"""
    print("💬 Please enter your bot token:")
    print("(Paste the token that @BotFather gave you)")
    print()
    
    while True:
        token = input("Bot Token: ").strip()
        
        if not token:
            print("❌ Token cannot be empty. Please try again.")
            continue
        
        # Basic validation
        if ':' not in token or len(token) < 20:
            print("❌ This doesn't look like a valid bot token.")
            print("   Bot tokens should contain ':' and be quite long.")
            print("   Please check and try again.")
            continue
        
        return token

def chat_instructions():
    """Display instructions for getting chat ID"""
    print("\n📱 Step 2: Get Your Chat ID")
    print("-" * 30)
    print()
    print("1. Find your bot in Telegram (search for the username you created)")
    print("2. Start a chat with your bot")
    print("3. Send any message to your bot (e.g., 'Hello')")
    print("4. Come back here and we'll find your chat ID automatically")
    print()

async def get_chat_id(bot_token: str):
    """Get chat ID from bot updates"""
    print("🔍 Looking for your chat ID...")
    
    try:
        import aiohttp
        
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data['result']:
                        # Find the most recent private chat
                        for update in reversed(data['result']):
                            if 'message' in update:
                                chat = update['message']['chat']
                                if chat['type'] == 'private':
                                    chat_id = str(chat['id'])
                                    user_name = f"{chat.get('first_name', '')} {chat.get('last_name', '')}".strip()
                                    print(f"✅ Found chat with {user_name}")
                                    print(f"   Chat ID: {chat_id}")
                                    return chat_id
                        
                        print("❌ No private messages found.")
                        return None
                    else:
                        print("❌ No messages found. Please send a message to your bot first.")
                        return None
                else:
                    error_data = await response.json()
                    print(f"❌ Error: {error_data.get('description', 'Unknown error')}")
                    return None
                    
    except ImportError:
        print("❌ aiohttp module is required. Install it with: pip install aiohttp")
        return None
    except Exception as e:
        print(f"❌ Error getting chat ID: {e}")
        return None

def update_env_file(bot_token: str, chat_id: str):
    """Update .env file with Telegram configuration"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("❌ .env file not found. Please make sure you're in the project directory.")
        return False
    
    try:
        # Read current content
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Update or add Telegram settings
        updated_lines = []
        settings_updated = {
            'TELEGRAM_ENABLED': False,
            'TELEGRAM_BOT_TOKEN': False,
            'TELEGRAM_CHAT_ID': False
        }
        
        for line in lines:
            if line.startswith('TELEGRAM_ENABLED='):
                updated_lines.append('TELEGRAM_ENABLED=true\n')
                settings_updated['TELEGRAM_ENABLED'] = True
            elif line.startswith('TELEGRAM_BOT_TOKEN='):
                updated_lines.append(f'TELEGRAM_BOT_TOKEN={bot_token}\n')
                settings_updated['TELEGRAM_BOT_TOKEN'] = True
            elif line.startswith('TELEGRAM_CHAT_ID='):
                updated_lines.append(f'TELEGRAM_CHAT_ID={chat_id}\n')
                settings_updated['TELEGRAM_CHAT_ID'] = True
            elif line.startswith('# TELEGRAM_BOT_TOKEN='):
                updated_lines.append(f'TELEGRAM_BOT_TOKEN={bot_token}\n')
                settings_updated['TELEGRAM_BOT_TOKEN'] = True
            elif line.startswith('# TELEGRAM_CHAT_ID='):
                updated_lines.append(f'TELEGRAM_CHAT_ID={chat_id}\n')
                settings_updated['TELEGRAM_CHAT_ID'] = True
            else:
                updated_lines.append(line)
        
        # Add missing settings
        if not settings_updated['TELEGRAM_ENABLED']:
            updated_lines.append('\nTELEGRAM_ENABLED=true\n')
        if not settings_updated['TELEGRAM_BOT_TOKEN']:
            updated_lines.append(f'TELEGRAM_BOT_TOKEN={bot_token}\n')
        if not settings_updated['TELEGRAM_CHAT_ID']:
            updated_lines.append(f'TELEGRAM_CHAT_ID={chat_id}\n')
        
        # Write back to file
        with open(env_file, 'w') as f:
            f.writelines(updated_lines)
        
        print("✅ .env file updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error updating .env file: {e}")
        return False

async def test_setup(bot_token: str, chat_id: str):
    """Test the setup by sending a message"""
    print("\n📤 Testing your setup...")
    
    try:
        import aiohttp
        
        message = """
🎉 <b>Telegram Integration Successful!</b>

Your Job Search Intelligence is now connected to Telegram!

You'll receive notifications here for:
• 📊 Analysis completions
• 💡 AI-generated insights  
• ⚠️ System alerts
• 🚨 Error notifications

<i>Setup completed successfully! 🚀</i>
        """.strip()
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    print("✅ Test message sent successfully!")
                    print("   Check your Telegram to see the welcome message.")
                    return True
                else:
                    error_data = await response.json()
                    print(f"❌ Failed to send test message: {error_data}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error sending test message: {e}")
        return False

async def main():
    """Main setup assistant"""
    print_header()
    
    # Step 1: Bot creation instructions
    create_bot_instructions()
    
    # Get bot token
    bot_token = get_bot_token()
    
    # Step 2: Chat instructions  
    chat_instructions()
    
    input("Press Enter after you've sent a message to your bot...")
    
    # Get chat ID
    chat_id = await get_chat_id(bot_token)
    
    if not chat_id:
        print("\n❌ Could not find your chat ID.")
        print("   Please make sure you've sent a message to your bot and try again.")
        return False
    
    # Update .env file
    print(f"\n💾 Updating .env file...")
    success = update_env_file(bot_token, chat_id)
    
    if not success:
        print("\n⚠️ Could not update .env file automatically.")
        print("   Please add these lines to your .env file manually:")
        print(f"   TELEGRAM_ENABLED=true")
        print(f"   TELEGRAM_BOT_TOKEN={bot_token}")
        print(f"   TELEGRAM_CHAT_ID={chat_id}")
        return False
    
    # Test the setup
    await test_setup(bot_token, chat_id)
    
    print("\n" + "=" * 50)
    print("🎉 Telegram Integration Setup Complete!")
    print("=" * 50)
    print()
    print("✅ Your bot is configured and ready to send notifications")
    print("✅ Your .env file has been updated")
    print("✅ Test message sent successfully")
    print()
    print("🚀 Next steps:")
    print("   • Run your Job Search Intelligence")
    print("   • You'll receive notifications in Telegram")
    print("   • Check the notification settings in your config")
    print()
    print("📋 Your configuration:")
    print(f"   Bot Token: ...{bot_token[-10:]}")
    print(f"   Chat ID: {chat_id}")
    print(f"   Status: Enabled")
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
