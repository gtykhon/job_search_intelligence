#!/usr/bin/env python3
"""
Enhanced Job Search Intelligence with Telegram Notifications
Demonstrates AI insights delivery via Telegram
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def demo_telegram_insights():
    """Demonstrate Job Search Intelligence with Telegram notifications"""
    
    print("🤖 Job Search Intelligence with Telegram Integration Demo")
    print("=" * 60)
    
    try:
        from src.config import AppConfig
        from src.integrations.notifications import NotificationManager
        
        # Load configuration
        config = AppConfig()
        
        # Check Telegram status
        if config.notifications.telegram_enabled:
            print("✅ Telegram notifications: ENABLED")
            print(f"   Bot token: ...{config.notifications.telegram_bot_token[-10:] if config.notifications.telegram_bot_token else 'Not set'}")
            print(f"   Chat ID: {config.notifications.telegram_chat_id}")
        else:
            print("⚠️ Telegram notifications: DISABLED")
            print("   Run 'python setup_telegram_bot.py' to enable")
        
        # Initialize notification manager
        print("\n🔧 Initializing notification system...")
        notification_manager = NotificationManager(config)
        await notification_manager.initialize()
        
        # Simulate Job Search Intelligence workflow with Telegram notifications
        print("\n📊 Starting Job Search Intelligence Analysis...")
        
        # 1. Analysis start notification
        await notification_manager.send_notification(
            title="🚀 LinkedIn Analysis Started",
            message="Profile and network analysis has begun. This may take a few minutes...",
            priority="normal",
            notification_type="analysis_start"
        )
        
        # Simulate some processing time
        await asyncio.sleep(2)
        
        # 2. Progress notification
        await notification_manager.send_notification(
            title="⏳ Analysis Progress Update",
            message="Phase 1 complete: Profile data extracted (50 connections analyzed)\nPhase 2 starting: AI insight generation...",
            priority="normal",
            notification_type="analysis_progress"
        )
        
        await asyncio.sleep(2)
        
        # 3. AI insights notification
        ai_insights = """
🧠 AI Analysis Results:

📈 Network Strength: 85% (Excellent)
• Strong connections in Technology and Finance sectors
• 23% mutual connections with industry leaders
• Optimal posting frequency detected

💡 Growth Opportunities:
• Expand connections in Healthcare sector (+15% potential reach)
• Engage more with Content Creators (2x engagement potential)
• Consider posting on Tuesday/Thursday for maximum visibility

🎯 Action Items:
1. Connect with 5 Healthcare professionals this week
2. Comment on 3 posts from top Content Creators
3. Share industry insights on Tuesday mornings

Confidence Score: 92%
        """
        
        await notification_manager.send_insight_alert(
            "AI Network Analysis",
            {
                'insights': ai_insights,
                'confidence': 0.92,
                'generated_at': datetime.now().isoformat()
            }
        )
        
        await asyncio.sleep(2)
        
        # 4. Analysis completion notification
        await notification_manager.send_analysis_complete(
            "Full Network Analysis",
            {
                'data_summary': {
                    'total_connections': 147,
                    'top_industries': ['Technology', 'Finance', 'Healthcare', 'Education'],
                    'engagement_rate': 0.23,
                    'network_score': 85
                },
                'confidence_scores': {'overall': 0.92},
                'analyzed_at': datetime.now().isoformat(),
                'analysis_duration': '5 minutes'
            }
        )
        
        # 5. Performance notification
        await notification_manager.send_performance_alert({
            'status': 'Healthy',
            'active_operations': 0,
            'database_status': 'Optimal',
            'uptime': '2 hours 15 minutes',
            'message': 'All systems operating at peak performance. Ready for next analysis.'
        })
        
        print("\n📬 Demo notifications sent!")
        
        # Show notification statistics
        stats = notification_manager.get_notification_stats()
        print(f"\n📊 Notification Statistics:")
        print(f"   Total sent: {stats['total_notifications']}")
        print(f"   Channels active: {[ch for ch, enabled in stats['channels_status'].items() if enabled]}")
        
        if 'by_channel' in stats:
            print(f"   Distribution: {stats['by_channel']}")
        
        print("\n🎉 Demo completed successfully!")
        
        if config.notifications.telegram_enabled:
            print("   Check your Telegram for the notifications! 📱")
        else:
            print("   Set up Telegram to receive notifications on your phone! 📱")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main demo function"""
    
    # Set up logging to be less verbose for demo
    logging.basicConfig(level=logging.WARNING)
    
    try:
        success = await demo_telegram_insights()
        
        if success:
            print("\n" + "=" * 60)
            print("✅ Job Search Intelligence + Telegram Integration Demo Complete!")
            print("=" * 60)
            print()
            print("🚀 What's Next?")
            print("   • Run the full Job Search Intelligence")
            print("   • Receive real insights in Telegram")
            print("   • Customize notification preferences")
            print("   • Set up automated analysis schedules")
            
        return success
        
    except KeyboardInterrupt:
        print("\n⏹️ Demo cancelled by user.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
