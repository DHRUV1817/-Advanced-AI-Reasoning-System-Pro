"""
Utility decorators for error handling and timing
"""
import time
from functools import wraps
from typing import Callable, Any
import groq
from src.utils.logger import logger


def handle_groq_errors(max_retries: int = 3, retry_delay: float = 1.0) -> Callable:
    """
    🛡️ GROQ API ERROR HANDLER WITH EXPONENTIAL BACKOFF
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                    
                except groq.RateLimitError as e:
                    last_exception = e
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(f"⏳ Rate limit hit. Waiting {wait_time:.1f}s... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    
                except groq.APIConnectionError as e:
                    last_exception = e
                    wait_time = retry_delay * (2 ** attempt)
                    logger.warning(f"🔌 Connection error. Retrying in {wait_time:.1f}s... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    
                except groq.AuthenticationError as e:
                    logger.error(f"🔑 Authentication failed: {e}")
                    raise ValueError("Invalid GROQ_API_KEY. Please check your API key.") from e
                    
                except groq.BadRequestError as e:
                    logger.error(f"❌ Invalid request: {e}")
                    raise ValueError(f"Invalid request parameters: {str(e)}") from e
                    
                except Exception as e:
                    last_exception = e
                    logger.error(f"❌ Unexpected error: {e}", exc_info=True)
                    if attempt == max_retries - 1:
                        break
                    time.sleep(retry_delay * (2 ** attempt))
            
            error_msg = f"Failed after {max_retries} attempts: {str(last_exception)}"
            logger.error(error_msg)
            raise Exception(error_msg) from last_exception
        
        return wrapper
    return decorator


def with_rate_limit(rate_limiter):
    """
    ⏱️ RATE LIMITING DECORATOR
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            rate_limiter.acquire()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def timer_decorator(func: Callable) -> Callable:
    """
    ⏱️ TIMING DECORATOR
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        logger.debug(f"⏱️ {func.__name__} took {elapsed_time:.2f}s")
        return result
    return wrapper
