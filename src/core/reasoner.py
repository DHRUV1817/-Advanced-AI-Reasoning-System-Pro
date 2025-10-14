"""
Advanced reasoning engine - Main business logic
"""
import time
import hashlib
from typing import Generator, List, Dict, Optional, Any, Tuple
from src.api.groq_client import GroqClientManager
from src.core.prompt_engine import PromptEngine
from src.core.conversation import ConversationManager
from src.services.cache_service import ResponseCache
from src.services.rate_limiter import RateLimiter
from src.services.export_service import ConversationExporter
from src.services.analytics_service import AnalyticsService
from src.models.metrics import ConversationMetrics
from src.models.entry import ConversationEntry
from src.config.settings import AppConfig
from src.config.constants import ReasoningMode, ModelConfig
from src.utils.logger import logger
from src.utils.decorators import handle_groq_errors, with_rate_limit
from src.utils.validators import validate_input
from src.utils.helpers import generate_session_id


class AdvancedReasoner:
    """
    🧠 ADVANCED REASONING ENGINE
    Main orchestrator for AI reasoning with caching, metrics, and export
    """
    
    def __init__(self):
        # Core components
        self.client_manager = GroqClientManager()
        self.conversation_manager = ConversationManager()
        self.prompt_engine = PromptEngine()
        
        # Services
        self.cache = ResponseCache(AppConfig.CACHE_SIZE, AppConfig.CACHE_TTL)
        self.rate_limiter = RateLimiter(AppConfig.RATE_LIMIT_REQUESTS, AppConfig.RATE_LIMIT_WINDOW)
        self.exporter = ConversationExporter()
        self.analytics = AnalyticsService()
        
        # Metrics and state
        self.metrics = ConversationMetrics()
        self.session_id = generate_session_id()
        
        logger.info(f"✅ AdvancedReasoner initialized | Session: {self.session_id[:8]}...")
    
    def _generate_cache_key(self, query: str, model: str, mode: str, 
                           temp: float, tokens: int) -> str:
        """
        🔑 GENERATE CACHE KEY
        """
        key_string = f"{query}|{model}|{mode}|{temp}|{tokens}"
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    @handle_groq_errors(max_retries=AppConfig.MAX_RETRIES, retry_delay=AppConfig.RETRY_DELAY)
    def _call_groq_api(self, messages: List[Dict], model: str, 
                       temperature: float, max_tokens: int) -> Generator[str, None, None]:
        """
        🔌 CALL GROQ API WITH STREAMING
        """
        if AppConfig.ENABLE_RATE_LIMITING:
            self.rate_limiter.acquire()
        
        client = self.client_manager.client
        
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def generate_response(
        self,
        query: str,
        history: List[Dict],
        model: str,
        reasoning_mode: ReasoningMode,
        enable_critique: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        template: str = "Custom",
        use_cache: bool = True
    ) -> Generator[str, None, None]:
        """
        🧠 GENERATE RESPONSE WITH STREAMING
        """
        # Validate input
        is_valid, error_msg = validate_input(query, AppConfig.MAX_INPUT_LENGTH)
        if not is_valid:
            yield f"❌ **Input Error:** {error_msg}"
            return
        
        start_time = time.time()
        
        # Check cache
        cache_key = self._generate_cache_key(query, model, reasoning_mode.value, temperature, max_tokens)
        
        if use_cache and AppConfig.ENABLE_CACHE:
            cached = self.cache.get(cache_key)
            if cached:
                self.metrics.update_cache_stats(hit=True)
                logger.info("✅ Cache hit - returning cached response")
                yield cached
                return
        
        self.metrics.update_cache_stats(hit=False)
        
        # Build messages
        messages = self.prompt_engine.build_messages(query, reasoning_mode, template, history)
        
        # Stream response
        full_response = ""
        try:
            for chunk in self._call_groq_api(messages, model, temperature, max_tokens):
                full_response += chunk
                yield full_response
            
            # Self-critique if enabled
            if enable_critique and AppConfig.ENABLE_SELF_CRITIQUE:
                critique_prompt = self.prompt_engine.get_self_critique_prompt(full_response)
                critique_messages = [
                    {"role": "system", "content": "You are a critical reviewer."},
                    {"role": "user", "content": critique_prompt}
                ]
                
                critique_response = ""
                for chunk in self._call_groq_api(critique_messages, model, temperature, max_tokens // 2):
                    critique_response += chunk
                
                full_response += f"\n\n---\n\n### 🔍 Self-Critique\n{critique_response}"
                yield full_response
            
            # Cache response
            if use_cache and AppConfig.ENABLE_CACHE:
                self.cache.set(cache_key, full_response)
            
            # Update metrics
            elapsed_time = time.time() - start_time
            tokens_estimate = len(full_response.split())
            
            self.metrics.update(
                tokens=tokens_estimate,
                time_taken=elapsed_time,
                depth=1,
                corrections=1 if enable_critique else 0,
                confidence=95.0
            )
            
            # Save conversation
            entry = ConversationEntry(
                user_message=query,
                assistant_response=full_response,
                model=model,
                reasoning_mode=reasoning_mode.value,
                temperature=temperature,
                max_tokens=max_tokens,
                tokens_used=tokens_estimate,
                inference_time=elapsed_time,
                critique_enabled=enable_critique,
                cache_hit=False
            )
            
            self.conversation_manager.add_conversation(entry)
            
            logger.info(f"✅ Response generated in {elapsed_time:.2f}s | Tokens: {tokens_estimate}")
            
        except Exception as e:
            self.metrics.increment_errors()
            error_msg = f"❌ **Error:** {str(e)}"
            logger.error(f"Response generation error: {e}", exc_info=True)
            yield error_msg
    
    # Convenience properties
    @property
    def conversation_history(self) -> List[ConversationEntry]:
        """Get conversation history"""
        return self.conversation_manager.get_history()
    
    @property
    def model_usage(self) -> Dict[str, int]:
        """Get model usage statistics"""
        return dict(self.conversation_manager.model_usage)
    
    @property
    def mode_usage(self) -> Dict[str, int]:
        """Get mode usage statistics"""
        return dict(self.conversation_manager.mode_usage)
    
    def clear_history(self) -> None:
        """Clear conversation history"""
        self.conversation_manager.clear_history()
    
    def export_conversation(self, format_type: str, include_metadata: bool = True) -> Tuple[str, Optional[str]]:
        """
        Export conversations
        Returns (content, filepath_string) for Gradio compatibility
        """
        return self.exporter.export(self.conversation_history, format_type, include_metadata)
    
    def export_current_chat_pdf(self) -> Optional[str]:
        """
        Export current chat as PDF
        Returns string path for Gradio compatibility
        """
        return self.exporter.export_to_pdf(self.conversation_history, include_metadata=True)
    
    def search_conversations(self, keyword: str) -> List[tuple]:
        """Search conversations"""
        return self.analytics.search_conversations(self.conversation_history, keyword)
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get analytics"""
        return self.analytics.generate_analytics(
            self.conversation_history,
            self.metrics,
            self.session_id,
            self.model_usage,
            self.mode_usage,
            self.cache.get_stats()
        )
