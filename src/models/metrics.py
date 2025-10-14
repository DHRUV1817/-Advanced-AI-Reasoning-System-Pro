"""
Conversation metrics data model
"""
from dataclasses import dataclass, field
from datetime import datetime
import threading
from typing import Dict
from src.utils.helpers import format_timestamp


@dataclass
class ConversationMetrics:
    """
    📊 ENHANCED THREAD-SAFE CONVERSATION METRICS
    """
    total_conversations: int = 0
    tokens_used: int = 0
    inference_time: float = 0.0
    reasoning_depth: int = 0
    self_corrections: int = 0
    confidence_score: float = 0.0
    session_start: str = field(default_factory=lambda: format_timestamp())
    peak_tokens: int = 0
    avg_response_time: float = 0.0
    tokens_per_second: float = 0.0
    error_count: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    
    def update(self, tokens: int, time_taken: float, depth: int = 1, 
               corrections: int = 0, confidence: float = 100.0) -> None:
        """
        ✅ THREAD-SAFE METRIC UPDATE
        """
        with self._lock:
            self.total_conversations += 1
            self.tokens_used += tokens
            self.inference_time = time_taken
            self.reasoning_depth = depth
            self.self_corrections = corrections
            self.confidence_score = confidence
            
            if tokens > self.peak_tokens:
                self.peak_tokens = tokens
            
            if self.total_conversations > 0:
                total_time = self.inference_time * self.total_conversations
                self.avg_response_time = total_time / self.total_conversations
                
                if self.avg_response_time > 0:
                    self.tokens_per_second = self.tokens_used / (self.avg_response_time * self.total_conversations)
    
    def increment_errors(self) -> None:
        """Increment error count"""
        with self._lock:
            self.error_count += 1
    
    def update_cache_stats(self, hit: bool) -> None:
        """Update cache statistics"""
        with self._lock:
            if hit:
                self.cache_hits += 1
            else:
                self.cache_misses += 1
    
    def reset(self) -> None:
        """Reset all metrics"""
        with self._lock:
            self.total_conversations = 0
            self.tokens_used = 0
            self.inference_time = 0.0
            self.reasoning_depth = 0
            self.self_corrections = 0
            self.confidence_score = 0.0
            self.peak_tokens = 0
            self.avg_response_time = 0.0
            self.tokens_per_second = 0.0
            self.error_count = 0
            self.cache_hits = 0
            self.cache_misses = 0
            self.session_start = format_timestamp()
