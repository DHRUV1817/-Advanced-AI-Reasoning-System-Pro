"""
Token bucket rate limiting service
"""
import time
import threading
from collections import deque
from src.utils.logger import logger


class RateLimiter:
    """
    ⏱️ TOKEN BUCKET RATE LIMITER
    """
    def __init__(self, max_requests: int = 50, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
        self.lock = threading.Lock()
    
    def acquire(self) -> bool:
        """
        ✅ ACQUIRE RATE LIMIT TOKEN
        Returns True if request is allowed, False otherwise
        """
        with self.lock:
            current_time = time.time()
            
            # Remove expired requests
            while self.requests and current_time - self.requests[0] > self.window_seconds:
                self.requests.popleft()
            
            # Check if under limit
            if len(self.requests) < self.max_requests:
                self.requests.append(current_time)
                logger.debug(f"✅ Rate limit check passed ({len(self.requests)}/{self.max_requests})")
                return True
            
            # Calculate wait time
            wait_time = self.window_seconds - (current_time - self.requests[0])
            logger.warning(f"⏳ Rate limit exceeded. Wait {wait_time:.1f}s")
            
            # Wait and retry
            time.sleep(wait_time + 0.1)
            self.requests.popleft()
            self.requests.append(time.time())
            return True
    
    def get_stats(self) -> dict:
        """
        📊 GET RATE LIMITER STATISTICS
        """
        with self.lock:
            current_time = time.time()
            
            # Remove expired
            while self.requests and current_time - self.requests[0] > self.window_seconds:
                self.requests.popleft()
            
            return {
                'current_requests': len(self.requests),
                'max_requests': self.max_requests,
                'window_seconds': self.window_seconds,
                'remaining': self.max_requests - len(self.requests)
            }
    
    def reset(self) -> None:
        """
        🔄 RESET RATE LIMITER
        """
        with self.lock:
            self.requests.clear()
            logger.info("🔄 Rate limiter reset")
