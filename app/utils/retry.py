"""
Retry utilities with exponential backoff for API calls.
"""

import time
import logging
from functools import wraps
from typing import Callable, TypeVar, Tuple, Any
import requests

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Exception, ...] = (requests.exceptions.RequestException,)
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to retry a function with exponential backoff.
    
    Parameters:
    -----------
    max_retries : int
        Maximum number of retry attempts (default: 3)
    initial_delay : float
        Initial delay in seconds (default: 1.0)
    backoff_factor : float
        Multiplier for delay after each retry (default: 2.0)
    exceptions : tuple
        Tuple of exceptions to catch and retry on
        
    Returns:
    --------
    Decorated function that retries on specified exceptions
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                            f"Retrying in {delay:.2f} seconds..."
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: {e}"
                        )
            
            # If we get here, all retries failed
            raise last_exception
        
        return wrapper
    return decorator





