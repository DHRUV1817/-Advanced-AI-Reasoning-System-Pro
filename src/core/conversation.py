"""
Conversation management and history handling
"""
import threading
from collections import deque, defaultdict
from typing import List, Dict, Optional
from src.models.entry import ConversationEntry
from src.config.settings import AppConfig
from src.utils.logger import logger


class ConversationManager:
    """
    💬 THREAD-SAFE CONVERSATION MANAGER
    Handles conversation history with automatic size management
    """
    
    def __init__(self):
        self.conversation_history: deque = deque(maxlen=AppConfig.MAX_CONVERSATION_STORAGE)
        self.model_usage: Dict[str, int] = defaultdict(int)
        self.mode_usage: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()
    
    def add_conversation(self, entry: ConversationEntry) -> None:
        """
        ✅ ADD CONVERSATION ENTRY
        """
        with self._lock:
            self.conversation_history.append(entry)
            self.model_usage[entry.model] += 1
            self.mode_usage[entry.reasoning_mode] += 1
            logger.debug(f"💬 Added conversation: {entry.entry_id[:8]}...")
    
    def get_history(self, limit: Optional[int] = None) -> List[ConversationEntry]:
        """
        ✅ GET CONVERSATION HISTORY
        """
        with self._lock:
            if limit:
                return list(self.conversation_history)[-limit:]
            return list(self.conversation_history)
    
    def clear_history(self) -> None:
        """
        🗑️ CLEAR CONVERSATION HISTORY
        """
        with self._lock:
            self.conversation_history.clear()
            self.model_usage.clear()
            self.mode_usage.clear()
            logger.info("🗑️ Conversation history cleared")
    
    def get_recent_context(self, limit: int = 10) -> List[Dict]:
        """
        ✅ GET RECENT CONTEXT FOR API
        """
        with self._lock:
            recent = list(self.conversation_history)[-limit:]
            
            context = []
            for conv in recent:
                context.append({"role": "user", "content": conv.user_message})
                context.append({"role": "assistant", "content": conv.assistant_response})
            
            logger.debug(f"📚 Retrieved {len(context)} context messages")
            return context
    
    def get_statistics(self) -> Dict:
        """
        📊 GET CONVERSATION STATISTICS
        """
        with self._lock:
            return {
                'total_conversations': len(self.conversation_history),
                'model_usage': dict(self.model_usage),
                'mode_usage': dict(self.mode_usage),
                'max_storage': AppConfig.MAX_CONVERSATION_STORAGE
            }
    
    def __len__(self) -> int:
        """Get conversation count"""
        with self._lock:
            return len(self.conversation_history)
