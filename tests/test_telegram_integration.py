#!/usr/bin/env python3
"""
Telegram Integration Test Script
Tests Telegram bot configuration and sends test notifications
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def get_chat_id_from_bot(bot_token: str):
    """Get chat ID by checking bot updates"""
    print("\n🔍 Getting Chat ID from Bot Updates...")
    print("=" * 50)
    
    try:
        import aiohttp
        
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data['result']:
                        print("✅ Found chat updates!")
                        
                        for update in data['result'][-5:]:  # Show last 5 updates
                            if 'message' in update:
                                chat = update['message']['chat']
                                chat_id = chat['id']
                                chat_type = chat['type']
                                
                                if chat_type == 'private':
                                    user_name = f"{chat.get('first_name', '')} {chat.get('last_name', '')}".strip()
                                    print(f"  💬 Private chat with {user_name}")
                                elif chat_type in ['group', 'supergroup']:
                                    group_name = chat.get('title', 'Unknown Group')
                                    print(f"  👥 Group chat: {group_name}")
                                
                                print(f"      Chat ID: {chat_id}")
                                print(f"      Type: {chat_type}")
                                print()
                        
                        # Get the most recent chat ID
                        latest_update = data['result'][-1]
                        if 'message' in latest_update:
                            latest_chat_id = latest_update['message']['chat']['id']
                            print(f"💡 Most recent Chat ID: {latest_chat_id}")
                            print("   ⬆️ Use this in your .env file as TELEGRAM_CHAT_ID")
                            return latest_chat_id
                    else:
                        print("❌ No messages found.")
                        print("   📝 Send a message to your bot first!")
                        return None
                else:
                    error_data = await response.json()
                    print(f"❌ Telegram API error: {error_data}")
                    return None
                    
    except Exception as e:
        print(f"❌ Error getting chat ID: {e}")
        return None

async def test_telegram_send(bot_token: str, chat_id: str):
    """Test sending a message to Telegram"""
    print("\n📤 Testing Telegram Message Sending...")
    print("=" * 50)
    
    try:
        import aiohttp
        
        # Test message
        message = f"""
<b>🧪 Job Search Intelligence - Test Message</b>

This is a test notification to verify your Telegram integration is working correctly!

<b>Test Details:</b>
• Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Chat ID: {chat_id}
• Bot Token: ...{bot_token[-10:]}

<i>🎉 If you receive this message, your integration is working perfectly!</i>
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
                    data = await response.json()
                    print("✅ Test message sent successfully!")
                    print(f"   Message ID: {data['result']['message_id']}")
                    return True
                else:
                    error_data = await response.json()
                    print(f"❌ Failed to send message: {error_data}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error sending test message: {e}")
        return False

async def test_notification_manager():
    """Test the notification manager with Telegram integration"""
    print("\n🔧 Testing Notification Manager Integration...")
    print("=" * 50)
    
    try:
        from src.config import AppConfig
        from src.integrations.notifications import NotificationManager
        
        # Load configuration
        config = AppConfig()
        
        # Check Telegram configuration
        if not config.notifications.telegram_enabled:
            print("⚠️ Telegram is disabled in configuration")
            print("   Enable it in .env file: TELEGRAM_ENABLED=true")
            return False
        
        if not config.notifications.telegram_bot_token:
            print("❌ No Telegram bot token configured")
            print("   Add TELEGRAM_BOT_TOKEN to .env file")
            return False
        
        if not config.notifications.telegram_chat_id:
            print("❌ No Telegram chat ID configured")
            print("   Add TELEGRAM_CHAT_ID to .env file")
            return False
        
        print(f"✅ Telegram configuration loaded")
        print(f"   Bot Token: ...{config.notifications.telegram_bot_token[-10:]}")
        print(f"   Chat ID: {config.notifications.telegram_chat_id}")
        
        # Initialize notification manager
        notification_manager = NotificationManager(config)
        await notification_manager.initialize()
        
        # Send test notifications
        print("\n📬 Sending test notifications...")
        
        # Analysis complete notification
        await notification_manager.send_analysis_complete(
            "Profile Analysis",
            {
                'data_summary': {
                    'total_connections': 150,
                    'top_industries': ['Technology', 'Finance', 'Healthcare']
                },
                'confidence_scores': {'overall': 0.92},
                'analyzed_at': datetime.now().isoformat()
            }
        )
        
        # Insight notification
        await notification_manager.send_insight_alert(
            "Network Opportunities",
            {
                'insights': 'Identified 5 high-value connection opportunities in the Technology sector.',
                'confidence': 0.85,
                'generated_at': datetime.now().isoformat()
            }
        )
        
        print("✅ Test notifications sent successfully!")
        
        # Get stats
        stats = notification_manager.get_notification_stats()
        print(f"\n📊 Notification Stats:")
        print(f"   Total sent: {stats['total_notifications']}")
        print(f"   Channels: {', '.join([ch for ch, enabled in stats['channels_status'].items() if enabled])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Notification manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function"""
    print("Telegram Integration Test for Job Search Intelligence")
    print("=" * 60)
    
    # Check if aiohttp is available
    try:
        import aiohttp
    except ImportError:
        print("❌ aiohttp is required for Telegram integration")
        print("   Install it with: pip install aiohttp")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    telegram_enabled = os.getenv('TELEGRAM_ENABLED', 'false').lower() == 'true'
    
    print(f"🔧 Configuration Status:")
    print(f"   Telegram Enabled: {telegram_enabled}")
    print(f"   Bot Token: {'✅ Set' if bot_token else '❌ Not set'}")
    print(f"   Chat ID: {'✅ Set' if chat_id else '❌ Not set'}")
    
    # Test 1: Get Chat ID if not configured
    if bot_token and not chat_id:
        print("\n🆔 Bot token found but no chat ID configured.")
        print("   First, send a message to your bot, then this script will help find the chat ID.")
        
        input("\nPress Enter after sending a message to your bot...")
        chat_id = await get_chat_id_from_bot(bot_token)
        
        if chat_id:
            print(f"\n💡 Add this to your .env file:")
            print(f"   TELEGRAM_CHAT_ID={chat_id}")
    
    # Test 2: Basic message sending
    if bot_token and chat_id:
        success = await test_telegram_send(bot_token, chat_id)
        if not success:
            return False
    else:
        print("\n⚠️ Skipping message test - missing bot token or chat ID")
    
    # Test 3: Notification manager integration
    if telegram_enabled and bot_token and chat_id:
        success = await test_notification_manager()
        if not success:
            return False
    else:
        print("\n⚠️ Skipping notification manager test - Telegram not fully configured")
    
    print("\n" + "=" * 60)
    print("🎉 Telegram Integration Test Complete!")
    print("=" * 60)
    
    if telegram_enabled and bot_token and chat_id:
        print("✅ Your Telegram integration is fully configured and working!")
        print("   You should receive Job Search Intelligence notifications in Telegram.")
    else:
        print("📝 Next steps to complete setup:")
        if not bot_token:
            print("   1. Create a Telegram bot with @BotFather")
            print("   2. Add TELEGRAM_BOT_TOKEN to .env file")
        if not chat_id:
            print("   3. Send a message to your bot")
            print("   4. Run this script again to get chat ID")
            print("   5. Add TELEGRAM_CHAT_ID to .env file")
        if not telegram_enabled:
            print("   6. Set TELEGRAM_ENABLED=true in .env file")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
