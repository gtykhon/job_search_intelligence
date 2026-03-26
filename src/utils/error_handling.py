"""
Enhanced Error Handling System
Comprehensive error handling with context and autonomous debugging foundations
"""

import time
import traceback
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, Optional, AsyncGenerator

# Custom exceptions
class AppError(Exception):
    """Base application exception with context and retry information"""
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None, retryable: bool = False):
        super().__init__(message)
        self.error_code = error_code
        self.context = context or {}
        self.retryable = retryable
        self.timestamp = datetime.now()
        self.traceback_info = traceback.format_exc()

class ResourceError(AppError):
    """Resource-related errors (database, connections, etc.)"""
    def __init__(self, message: str, resource_type: str, resource_id: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.retryable = True  # Most resource errors are retryable

class ConfigurationError(AppError):
    """Configuration-related errors"""
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        super().__init__(message, retryable=False, **kwargs)  # Config errors usually not retryable
        self.config_key = config_key

class ProcessingError(AppError):
    """Data processing errors"""
    def __init__(self, message: str, processor: Optional[str] = None, data_id: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.processor = processor
        self.data_id = data_id

class ExternalServiceError(AppError):
    """External service communication errors"""
    def __init__(self, message: str, service_name: str, status_code: Optional[int] = None, 
                 response_body: Optional[str] = None, **kwargs):
        super().__init__(message, retryable=True, **kwargs)
        self.service_name = service_name
        self.status_code = status_code
        self.response_body = response_body

class RateLimitError(ExternalServiceError):
    """Rate limiting errors with retry information"""
    def __init__(self, service_name: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(f"Rate limit exceeded for {service_name}", service_name, **kwargs)
        self.retry_after = retry_after
        self.retryable = True

@asynccontextmanager
async def error_context(operation: str, **context) -> AsyncGenerator[None, None]:
    """
    Enhanced error context with autonomous debugging capabilities
    
    Args:
        operation: Name of the operation being performed
        **context: Additional context information
        
    Yields:
        None - context manager for operation execution
    """
    start_time = time.time()
    operation_id = f"{operation}_{int(time.time())}"
    logger = logging.getLogger(__name__)
    
    # Enhanced context with call stack information
    import inspect
    frame = inspect.currentframe()
    caller_info = {}
    if frame and frame.f_back:
        caller_info = {
            'file': frame.f_back.f_code.co_filename,
            'function': frame.f_back.f_code.co_name,
            'line': frame.f_back.f_lineno
        }
    
    full_context = {
        'operation_id': operation_id,
        'operation': operation,
        'caller_info': caller_info,
        **context
    }
    
    try:
        logger.info(f"🚀 Starting {operation}", extra=full_context)
        yield
        
        execution_time = time.time() - start_time
        logger.info(
            f"✅ Completed {operation} in {execution_time:.2f}s", 
            extra={**full_context, 'execution_time': execution_time}
        )
        
    except Exception as e:
        execution_time = time.time() - start_time
        
        # Enhanced error information
        error_info = {
            **full_context,
            'error_type': type(e).__name__,
            'error_message': str(e),
            'execution_time': execution_time,
            'traceback': traceback.format_exc()
        }
        
        # Autonomous debugging context
        if isinstance(e, AppError) and hasattr(e, 'context'):
            error_info['error_context'] = e.context
        
        logger.error(f"❌ Failed {operation} after {execution_time:.2f}s", extra=error_info)
        
        # Enhance exception with context if it's our custom exception
        if isinstance(e, AppError):
            e.context.update(error_info)
        else:
            # Wrap in our exception type
            raise ProcessingError(
                f"{operation} failed: {e}",
                context=error_info
            ) from e

def setup_error_handling():
    """Setup global error handling configuration"""
    # Configure exception handling
    import sys
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Global exception handler"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger = logging.getLogger(__name__)
        logger.critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    sys.excepthook = handle_exception
