"""
Telegram Messenger Module

Handles Telegram message and document sending for Job Search Intelligence
"""

import requests
import logging
from src.utils.text_sanitizer import install_ascii_logging_filter
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)
install_ascii_logging_filter(logger)

class TelegramMessenger:
    """Handles real Telegram messaging"""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    async def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send message to Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            headers = {'Content-Type': 'application/json; charset=utf-8'}
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            logger.info(f"âœ… Telegram message sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"âŒ Failed to send Telegram message: {e}")
            return False
    
    async def send_document(self, file_path: str, caption: str = "") -> bool:
        """Send document to Telegram"""
        try:
            url = f"{self.base_url}/sendDocument"
            
            with open(file_path, 'rb') as file:
                files = {'document': file}
                data = {
                    'chat_id': self.chat_id,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                
                response = requests.post(url, files=files, data=data, timeout=30)
                response.raise_for_status()
            
            logger.info(f"âœ… Telegram document sent successfully: {Path(file_path).name}")
            return True
            
        except Exception as e:
            logger.error(f"âŒ Failed to send document: {e}")
            return False
    
    def send_message_sync(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send message to Telegram (synchronous version)"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            headers = {'Content-Type': 'application/json; charset=utf-8'}
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            logger.info(f"âœ… Telegram message sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"âŒ Failed to send Telegram message: {e}")
            return False
    
    def send_document_sync(self, file_path: str, caption: str = "") -> bool:
        """Send document to Telegram (synchronous version)"""
        try:
            url = f"{self.base_url}/sendDocument"
            
            with open(file_path, 'rb') as file:
                files = {'document': file}
                data = {
                    'chat_id': self.chat_id,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                
                response = requests.post(url, files=files, data=data, timeout=30)
                response.raise_for_status()
            
            logger.info(f"âœ… Telegram document sent successfully: {Path(file_path).name}")
            return True
            
        except Exception as e:
            logger.error(f"âŒ Failed to send document: {e}")
            return False
