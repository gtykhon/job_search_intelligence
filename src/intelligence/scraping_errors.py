"""
Simplified error handling for job scraping
"""
from typing import Optional


class ScrapingError(Exception):
    """Base exception for scraping errors"""
    def __init__(self, message: str, url: Optional[str] = None):
        self.message = message
        self.url = url
        super().__init__(self.message)


class ExternalServiceError(Exception):
    """Exception for external service failures"""
    pass
