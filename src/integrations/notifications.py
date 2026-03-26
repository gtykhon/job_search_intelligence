"""
Notification Manager
Multi-channel notification system for Job Search Intelligence
"""

import asyncio
import json
import logging
import smtplib
import aiohttp
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from ..config import AppConfig
from ..utils.error_handling import error_context, ProcessingError

logger = logging.getLogger(__name__)

class NotificationManager:
    """
    Simplified notification manager
    Currently supports console notifications with email support planned
    """
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.notification_history = []
        self.max_history = 100
        
    async def initialize(self):
        """Initialize notification manager"""
        async with error_context("notification_manager_initialization"):
            try:
                # Test console notifications
                await self._send_console_notification({
                    'title': 'Job Search Intelligence - System Startup',
                    'message': 'Job Search Intelligence notification system is now active.',
                    'priority': 'normal',
                    'type': 'system_startup',
                    'timestamp': datetime.now().isoformat()
                })
                
                logger.info("âœ… Notification Manager initialized")
                
            except Exception as e:
                raise ProcessingError(
                    f"Failed to initialize Notification Manager: {e}",
                    processor="notification_manager"
                ) from e
    
    async def send_analysis_complete(self, analysis_type: str, results: Dict[str, Any]):
        """Send notification when analysis is complete"""
        message = self._format_analysis_notification(analysis_type, results)
        await self._send_notification(
            title=f"LinkedIn Analysis Complete: {analysis_type}",
            message=message,
            priority="normal",
            notification_type="analysis_complete"
        )
    
    async def send_error_alert(self, error_type: str, error_details: Dict[str, Any]):
        """Send error alert notification"""
        message = self._format_error_notification(error_type, error_details)
        await self._send_notification(
            title=f"Job Search Intelligence Error: {error_type}",
            message=message,
            priority="high",
            notification_type="error_alert"
        )
    
    async def send_insight_alert(self, insight_type: str, insights: Dict[str, Any]):
        """Send notification for new insights"""
        message = self._format_insight_notification(insight_type, insights)
        await self._send_notification(
            title=f"New LinkedIn Insight: {insight_type}",
            message=message,
            priority="normal",
            notification_type="insight_alert"
        )
    
    async def send_performance_alert(self, metrics: Dict[str, Any]):
        """Send performance monitoring alert"""
        message = self._format_performance_notification(metrics)
        await self._send_notification(
            title="Job Search Intelligence Performance Alert",
            message=message,
            priority="medium",
            notification_type="performance_alert"
        )
    
    async def send_notification(self, title: str, message: str, priority: str = "normal", 
                               notification_type: str = "general"):
        """Public method to send notifications"""
        await self._send_notification(title, message, priority, notification_type)
    
    async def _send_notification(self, title: str, message: str, priority: str = "normal", 
                               notification_type: str = "general"):
        """Send notification through configured channels"""
        notification = {
            'id': f"notif_{int(datetime.now().timestamp())}",
            'title': title,
            'message': message,
            'priority': priority,
            'type': notification_type,
            'timestamp': datetime.now().isoformat(),
            'channels_sent': []
        }
        
        # Console notification (always enabled)
        await self._send_console_notification(notification)
        notification['channels_sent'].append('console')
        
        # Email notification (if enabled and configured)
        if (self.config.notifications.email_enabled and 
            self.config.notifications.email_smtp_server and 
            self.config.notifications.email_recipients):
            try:
                success = await self._send_email_notification(notification)
                if success:
                    notification['channels_sent'].append('email')
            except Exception as e:
                logger.warning(f"âš ï¸ Email notification failed: {e}")
        
        # Telegram notification (if enabled and configured)
        if (self.config.notifications.telegram_enabled and 
            self.config.notifications.telegram_bot_token and 
            self.config.notifications.telegram_chat_id):
            try:
                success = await self._send_telegram_notification(notification)
                if success:
                    notification['channels_sent'].append('telegram')
            except Exception as e:
                logger.warning(f"âš ï¸ Telegram notification failed: {e}")
        
        # Store notification in history
        self._add_to_history(notification)
        
        logger.info(f"ðŸ“¢ Notification sent via {', '.join(notification['channels_sent'])}: {title}")
    
    async def _send_console_notification(self, notification: Dict[str, Any]):
        """Send console notification with emoji formatting"""
        priority_emojis = {
            'low': 'ðŸ’¡',
            'normal': 'ðŸ“Š',
            'medium': 'âš ï¸',
            'high': 'ðŸš¨',
            'critical': 'ðŸ’¥'
        }
        
        emoji = priority_emojis.get(notification['priority'], 'ðŸ“¢')
        timestamp = datetime.fromisoformat(notification['timestamp']).strftime('%H:%M:%S')
        
        print(f"\n{emoji} [{timestamp}] {notification['title']}")
        print(f"   {notification['message']}")
        if notification['priority'] in ['high', 'critical']:
            print(f"   Priority: {notification['priority'].upper()}")
        print()
    
    async def _send_email_notification(self, notification: Dict[str, Any]) -> bool:
        """Send email notification (basic implementation)"""
        try:
            # Import here to avoid issues if email modules aren't available
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config.notifications.email_username
            msg['To'] = ', '.join(self.config.notifications.email_recipients)
            msg['Subject'] = f"[Job Search Intelligence] {notification['title']}"

            # Text body
            text_body = f"""
{notification['title']}
Priority: {notification['priority']}
Time: {notification['timestamp']}

{notification['message']}

---
Job Search Intelligence
            """

            msg.attach(MIMEText(text_body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.config.notifications.email_smtp_server, 
                            self.config.notifications.email_smtp_port) as server:
                server.starttls()  # Always use TLS for security
                
                if self.config.notifications.email_username:
                    server.login(
                        self.config.notifications.email_username,
                        self.config.notifications.email_password
                    )
                
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            logger.warning(f"âš ï¸ Failed to send email notification: {e}")
            return False
    
    async def _send_telegram_notification(self, notification: Dict[str, Any]) -> bool:
        """Send Telegram notification via Bot API"""
        try:
            bot_token = self.config.notifications.telegram_bot_token
            chat_id = self.config.notifications.telegram_chat_id
            
            # Format message for Telegram
            message = self._format_telegram_message(notification)
            
            # Telegram Bot API URL
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            # Payload
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML',  # Enable HTML formatting
                'disable_web_page_preview': True
            }
            
            # Send request
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logger.debug(f"âœ… Telegram notification sent successfully")
                        return True
                    else:
                        error_text = await response.text()
                        logger.warning(f"âš ï¸ Telegram API error {response.status}: {error_text}")
                        return False
                        
        except Exception as e:
            logger.warning(f"âš ï¸ Failed to send Telegram notification: {e}")
            return False
    
    def _format_analysis_notification(self, analysis_type: str, results: Dict[str, Any]) -> str:
        """Format analysis completion notification"""
        summary = results.get('data_summary', {})
        total_connections = summary.get('total_connections', 0)
        confidence = results.get('confidence_scores', {}).get('overall', 0)
        
        return f"""
LinkedIn {analysis_type} analysis completed successfully!

ðŸ“Š Results Summary:
â€¢ Total connections analyzed: {total_connections}
â€¢ Analysis confidence: {confidence:.1%}
â€¢ Top industries: {', '.join(summary.get('top_industries', [])[:3])}
â€¢ Analysis timestamp: {results.get('analyzed_at', 'Unknown')}

The analysis results are now available in your Job Search Intelligence dashboard.
        """.strip()
    
    def _format_error_notification(self, error_type: str, error_details: Dict[str, Any]) -> str:
        """Format error alert notification"""
        return f"""
Job Search Intelligence encountered an error:

ðŸš¨ Error Type: {error_type}
ðŸ“ Location: {error_details.get('location', 'Unknown')}
â° Time: {error_details.get('timestamp', datetime.now().isoformat())}

Details: {error_details.get('message', 'No additional details available')}

Please check the logs for more information and consider restarting the analysis if needed.
        """.strip()
    
    def _format_insight_notification(self, insight_type: str, insights: Dict[str, Any]) -> str:
        """Format insight notification"""
        insight_text = insights.get('insights', 'New insights are available')
        confidence = insights.get('confidence', 0)
        
        return f"""
New LinkedIn insights available!

ðŸ’¡ Insight Type: {insight_type}
ðŸŽ¯ Confidence: {confidence:.1%}
ðŸ“ˆ Generated: {insights.get('generated_at', 'Recently')}

Key Insights:
{insight_text[:500]}{'...' if len(insight_text) > 500 else ''}

Review the full insights in your Job Search Intelligence dashboard.
        """.strip()
    
    def _format_performance_notification(self, metrics: Dict[str, Any]) -> str:
        """Format performance monitoring notification"""
        return f"""
Job Search Intelligence Performance Update:

âš¡ System Status: {metrics.get('status', 'Unknown')}
ðŸ”„ Active Operations: {metrics.get('active_operations', 0)}
ðŸ’¾ Database Health: {metrics.get('database_status', 'Unknown')}
ðŸ• Uptime: {metrics.get('uptime', 'Unknown')}

{metrics.get('message', 'System is operating normally.')}
        """.strip()
    
    def _format_telegram_message(self, notification: Dict[str, Any]) -> str:
        """Format message for Telegram with HTML formatting (UTF-8 safe)"""
        priority_emojis = {
            'low': '\U0001F7E2',       # 🟢
            'normal': '\u2139\uFE0F',  # ℹ️
            'medium': '\u26A0\uFE0F',  # ⚠️
            'high': '\U0001F6A8',       # 🚨
            'critical': '\U0001F6D1'    # 🛑
        }
        emoji = priority_emojis.get(notification.get('priority','normal'), '\u2139\uFE0F')
        timestamp = datetime.fromisoformat(notification['timestamp']).strftime('%H:%M:%S')
        title = f"<b>{emoji} {notification['title']}</b>"
        message_content = notification.get('message','')
        priority_text = ""
        if notification.get('priority') in ['high', 'critical']:
            priority_text = f"\n<i>Priority: {notification['priority'].upper()}</i>"
        footer = f"\n\n<i>\u23F0 {timestamp} | Job Search Intelligence</i>"
        full_message = f"{title}\n\n{message_content}{priority_text}{footer}".strip()
        if len(full_message) > 4000:
            max_content_length = 4000 - len(title) - len(priority_text) - len(footer) - 10
            truncated_content = (message_content[:max_content_length] + '...') if max_content_length>0 else ''
            full_message = f"{title}\n\n{truncated_content}{priority_text}{footer}".strip()
        return full_message
    
    def _add_to_history(self, notification: Dict[str, Any]):
        """Add notification to history"""
        self.notification_history.append(notification)
        
        # Maintain history size
        if len(self.notification_history) > self.max_history:
            self.notification_history = self.notification_history[-self.max_history:]
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        if not self.notification_history:
            return {
                'total_notifications': 0,
                'channels_status': {
                    'console': True,
                    'email': self.config.notifications.email_enabled,
                    'telegram': self.config.notifications.telegram_enabled
                }
            }
        
        # Calculate statistics
        total = len(self.notification_history)
        by_priority = {}
        by_type = {}
        by_channel = {}
        
        for notif in self.notification_history:
            priority = notif['priority']
            notif_type = notif['type']
            channels = notif['channels_sent']
            
            by_priority[priority] = by_priority.get(priority, 0) + 1
            by_type[notif_type] = by_type.get(notif_type, 0) + 1
            
            for channel in channels:
                by_channel[channel] = by_channel.get(channel, 0) + 1
        
        return {
            'total_notifications': total,
            'by_priority': by_priority,
            'by_type': by_type,
            'by_channel': by_channel,
            'channels_status': {
                'console': True,
                'email': self.config.notifications.email_enabled,
                'telegram': self.config.notifications.telegram_enabled
            }
        }
    
    async def cleanup(self):
        """Cleanup notification manager"""
        try:
            # Send shutdown notification
            await self._send_notification(
                title="Job Search Intelligence - System Shutdown",
                message="Job Search Intelligence notification system is shutting down.",
                priority="normal",
                notification_type="system_shutdown"
            )
            
            logger.info("ðŸ§¹ Notification Manager cleanup complete")
            
        except Exception as e:
            logger.warning(f"âš ï¸ Notification cleanup warning: {e}")
