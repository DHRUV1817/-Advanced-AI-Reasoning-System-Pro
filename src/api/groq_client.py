"""
Groq API client manager with singleton pattern
"""
import os
import threading
from typing import Optional
from groq import Groq
from src.utils.logger import logger
from src.config.settings import AppConfig


class GroqClientManager:
    """
    🔌 SINGLETON GROQ CLIENT MANAGER
    Thread-safe singleton pattern for API client
    """
    _instance: Optional['GroqClientManager'] = None
    _lock = threading.Lock()
    _client: Optional[Groq] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._initialize_client()
                    self._initialized = True
    
    def _initialize_client(self) -> None:
        """
        🔧 INITIALIZE GROQ CLIENT
        """
        api_key = os.getenv('GROQ_API_KEY')
        
        if not api_key:
            logger.error("❌ GROQ_API_KEY not found in environment variables")
            raise EnvironmentError(
                "GROQ_API_KEY not set. Please add it to your .env file:\n"
                "GROQ_API_KEY=your_api_key_here"
            )
        
        try:
            self._client = Groq(
                api_key=api_key,
                timeout=AppConfig.REQUEST_TIMEOUT
            )
            logger.info("✅ Groq client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Groq client: {e}")
            raise
    
    @property
    def client(self) -> Groq:
        """
        ✅ GET GROQ CLIENT INSTANCE
        """
        if self._client is None:
            raise RuntimeError("Groq client not initialized")
        return self._client
    
    def health_check(self) -> bool:
        """
        🏥 HEALTH CHECK
        """
        try:
            if self._client is None:
                logger.warning("⚠️ Health check failed: Client not initialized")
                return False
            
            logger.debug("✅ Health check passed")
            return True
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
            return False
    
    def reset(self) -> None:
        """
        🔄 RESET CLIENT (FOR TESTING)
        """
        with self._lock:
            self._client = None
            self._initialized = False
            logger.info("🔄 Groq client reset")
