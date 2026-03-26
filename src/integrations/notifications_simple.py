"""
Notification Manager
Multi-channel notification system for Job Search Intelligence
"""

import asyncio
import json
import logging
import smtplib
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
                
                logger.info("✅ Notification Manager initialized")
                
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
                logger.warning(f"⚠️ Email notification failed: {e}")
        
        # Store notification in history
        self._add_to_history(notification)
        
        logger.info(f"📢 Notification sent via {', '.join(notification['channels_sent'])}: {title}")
    
    async def _send_console_notification(self, notification: Dict[str, Any]):
        """Send console notification with emoji formatting"""
        priority_emojis = {
            'low': '💡',
            'normal': '📊',
            'medium': '⚠️',
            'high': '🚨',
            'critical': '💥'
        }
        
        emoji = priority_emojis.get(notification['priority'], '📢')
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
            from email.mime.text import MimeText
            from email.mime.multipart import MimeMultipart
            
            # Create message
            msg = MimeMultipart()
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
            
            msg.attach(MimeText(text_body, 'plain'))
            
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
            logger.warning(f"⚠️ Failed to send email notification: {e}")
            return False
    
    def _format_analysis_notification(self, analysis_type: str, results: Dict[str, Any]) -> str:
        """Format analysis completion notification"""
        summary = results.get('data_summary', {})
        total_connections = summary.get('total_connections', 0)
        confidence = results.get('confidence_scores', {}).get('overall', 0)
        
        return f"""
LinkedIn {analysis_type} analysis completed successfully!

📊 Results Summary:
• Total connections analyzed: {total_connections}
• Analysis confidence: {confidence:.1%}
• Top industries: {', '.join(summary.get('top_industries', [])[:3])}
• Analysis timestamp: {results.get('analyzed_at', 'Unknown')}

The analysis results are now available in your Job Search Intelligence dashboard.
        """.strip()
    
    def _format_error_notification(self, error_type: str, error_details: Dict[str, Any]) -> str:
        """Format error alert notification"""
        return f"""
Job Search Intelligence encountered an error:

🚨 Error Type: {error_type}
📍 Location: {error_details.get('location', 'Unknown')}
⏰ Time: {error_details.get('timestamp', datetime.now().isoformat())}

Details: {error_details.get('message', 'No additional details available')}

Please check the logs for more information and consider restarting the analysis if needed.
        """.strip()
    
    def _format_insight_notification(self, insight_type: str, insights: Dict[str, Any]) -> str:
        """Format insight notification"""
        insight_text = insights.get('insights', 'New insights are available')
        confidence = insights.get('confidence', 0)
        
        return f"""
New LinkedIn insights available!

💡 Insight Type: {insight_type}
🎯 Confidence: {confidence:.1%}
📈 Generated: {insights.get('generated_at', 'Recently')}

Key Insights:
{insight_text[:500]}{'...' if len(insight_text) > 500 else ''}

Review the full insights in your Job Search Intelligence dashboard.
        """.strip()
    
    def _format_performance_notification(self, metrics: Dict[str, Any]) -> str:
        """Format performance monitoring notification"""
        return f"""
Job Search Intelligence Performance Update:

⚡ System Status: {metrics.get('status', 'Unknown')}
🔄 Active Operations: {metrics.get('active_operations', 0)}
💾 Database Health: {metrics.get('database_status', 'Unknown')}
🕐 Uptime: {metrics.get('uptime', 'Unknown')}

{metrics.get('message', 'System is operating normally.')}
        """.strip()
    
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
                    'email': self.config.notifications.email_enabled
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
                'email': self.config.notifications.email_enabled
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
            
            logger.info("🧹 Notification Manager cleanup complete")
            
        except Exception as e:
            logger.warning(f"⚠️ Notification cleanup warning: {e}")
