"""
Conversation entry data model
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
import uuid
from typing import Optional
from src.utils.helpers import format_timestamp


@dataclass
class ConversationEntry:
    """
    💬 ENHANCED CONVERSATION ENTRY WITH METADATA
    """
    user_message: str
    assistant_response: str
    model: str
    reasoning_mode: str
    timestamp: str = field(default_factory=lambda: format_timestamp())
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    temperature: float = 0.7
    max_tokens: int = 4000
    tokens_used: int = 0
    inference_time: float = 0.0
    reasoning_depth: int = 1
    confidence_score: float = 100.0
    critique_enabled: bool = False
    cache_hit: bool = False
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)
    
    def __str__(self) -> str:
        return (f"ConversationEntry(id={self.entry_id[:8]}, "
                f"model={self.model}, mode={self.reasoning_mode})")
