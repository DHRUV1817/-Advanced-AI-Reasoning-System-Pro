"""
Response caching service with LRU and TTL
"""
import time
import threading
from typing import Dict, Tuple, Optional, Any
from src.utils.logger import logger


class ResponseCache:
    """
    💾 THREAD-SAFE LRU CACHE WITH TTL
    """
    def __init__(self, maxsize: int = 100, ttl: int = 3600):
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.maxsize = maxsize
        self.ttl = ttl
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        ✅ GET CACHED VALUE WITH TTL CHECK
        """
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None
            
            value, timestamp = self.cache[key]
            
            # Check if expired
            if time.time() - timestamp > self.ttl:
                del self.cache[key]
                self.misses += 1
                logger.debug(f"🕐 Cache expired for key: {key[:20]}...")
                return None
            
            self.hits += 1
            logger.debug(f"✅ Cache hit for key: {key[:20]}...")
            return value
    
    def set(self, key: str, value: Any) -> None:
        """
        ✅ SET CACHE VALUE WITH LRU EVICTION
        """
        with self.lock:
            # Evict oldest if at capacity
            if len(self.cache) >= self.maxsize and key not in self.cache:
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
                del self.cache[oldest_key]
                logger.debug(f"🗑️ Evicted cache entry: {oldest_key[:20]}...")
            
            self.cache[key] = (value, time.time())
            logger.debug(f"💾 Cached response for key: {key[:20]}...")
    
    def clear(self) -> None:
        """
        🗑️ CLEAR ALL CACHE ENTRIES
        """
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
            logger.info("🗑️ Cache cleared")
    
    def get_stats(self) -> dict:
        """
        📊 GET CACHE STATISTICS
        """
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'maxsize': self.maxsize,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': f"{hit_rate:.1f}",
                'ttl': self.ttl
            }
    
    def __len__(self) -> int:
        """Get current cache size"""
        with self.lock:
            return len(self.cache)
