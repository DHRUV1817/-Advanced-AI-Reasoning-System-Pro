"""
Application configuration settings
"""
import os
from pathlib import Path
from typing import ClassVar


class AppConfig:
    """
    🎛️ CENTRALIZED APPLICATION CONFIGURATION
    """
    
    # Environment
    ENV: ClassVar[str] = os.getenv('APP_ENV', 'development')
    DEBUG: ClassVar[bool] = ENV == 'development'
    
    # Conversation Settings
    MAX_HISTORY_LENGTH: ClassVar[int] = int(os.getenv('MAX_HISTORY_LENGTH', '10'))
    MAX_CONVERSATION_STORAGE: ClassVar[int] = int(os.getenv('MAX_CONVERSATION_STORAGE', '1000'))
    
    # Model Parameters
    DEFAULT_TEMPERATURE: ClassVar[float] = float(os.getenv('DEFAULT_TEMPERATURE', '0.7'))
    MIN_TEMPERATURE: ClassVar[float] = 0.0
    MAX_TEMPERATURE: ClassVar[float] = 2.0
    
    DEFAULT_MAX_TOKENS: ClassVar[int] = int(os.getenv('DEFAULT_MAX_TOKENS', '4000'))
    MIN_TOKENS: ClassVar[int] = 100
    MAX_TOKENS: ClassVar[int] = 32000
    
    # API Settings
    REQUEST_TIMEOUT: ClassVar[int] = int(os.getenv('REQUEST_TIMEOUT', '60'))
    MAX_RETRIES: ClassVar[int] = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY: ClassVar[float] = float(os.getenv('RETRY_DELAY', '1.0'))
    
    # Cache Settings
    CACHE_SIZE: ClassVar[int] = int(os.getenv('CACHE_SIZE', '100'))
    CACHE_TTL: ClassVar[int] = int(os.getenv('CACHE_TTL', '3600'))
    ENABLE_CACHE: ClassVar[bool] = os.getenv('ENABLE_CACHE', 'true').lower() == 'true'
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: ClassVar[int] = int(os.getenv('RATE_LIMIT_REQUESTS', '50'))
    RATE_LIMIT_WINDOW: ClassVar[int] = int(os.getenv('RATE_LIMIT_WINDOW', '60'))
    ENABLE_RATE_LIMITING: ClassVar[bool] = os.getenv('ENABLE_RATE_LIMITING', 'true').lower() == 'true'
    
    # File Storage
    BASE_DIR: ClassVar[Path] = Path(__file__).parent.parent.parent
    EXPORT_DIR: ClassVar[Path] = BASE_DIR / os.getenv('EXPORT_DIR', 'exports')
    BACKUP_DIR: ClassVar[Path] = BASE_DIR / os.getenv('BACKUP_DIR', 'backups')
    LOG_DIR: ClassVar[Path] = BASE_DIR / 'logs'
    MAX_EXPORT_SIZE_MB: ClassVar[int] = 50
    
    # UI Theme
    THEME_PRIMARY: ClassVar[str] = os.getenv('THEME_PRIMARY', 'purple')
    THEME_SECONDARY: ClassVar[str] = os.getenv('THEME_SECONDARY', 'blue')
    
    # Analytics
    AUTO_SAVE_INTERVAL: ClassVar[int] = 300
    ENABLE_ANALYTICS: ClassVar[bool] = True
    ANALYTICS_BATCH_SIZE: ClassVar[int] = 10
    
    # Performance
    MAX_WORKERS: ClassVar[int] = int(os.getenv('MAX_WORKERS', '3'))
    ENABLE_PARALLEL_PROCESSING: ClassVar[bool] = True
    
    # Security
    MAX_INPUT_LENGTH: ClassVar[int] = 10000
    ENABLE_XSS_PROTECTION: ClassVar[bool] = True
    ALLOWED_EXPORT_FORMATS: ClassVar[list] = ['json', 'markdown', 'txt', 'pdf']
    
    # Feature Flags
    ENABLE_PDF_EXPORT: ClassVar[bool] = os.getenv('ENABLE_PDF_EXPORT', 'true').lower() == 'true'
    ENABLE_SELF_CRITIQUE: ClassVar[bool] = True
    ENABLE_SIDEBAR_TOGGLE: ClassVar[bool] = True
    
    @classmethod
    def validate(cls) -> bool:
        """Validates all configuration parameters"""
        # Import logger here to avoid circular import
        from src.utils.logger import logger
        
        try:
            assert cls.MIN_TEMPERATURE <= cls.DEFAULT_TEMPERATURE <= cls.MAX_TEMPERATURE
            assert cls.MIN_TOKENS <= cls.DEFAULT_MAX_TOKENS <= cls.MAX_TOKENS
            assert cls.MAX_HISTORY_LENGTH > 0
            assert cls.MAX_CONVERSATION_STORAGE >= cls.MAX_HISTORY_LENGTH
            assert cls.CACHE_SIZE > 0 and cls.CACHE_TTL > 0
            assert cls.RATE_LIMIT_REQUESTS > 0 and cls.RATE_LIMIT_WINDOW > 0
            assert cls.REQUEST_TIMEOUT > 0 and cls.MAX_RETRIES >= 0
            assert 1 <= cls.MAX_WORKERS <= 10
            assert cls.MAX_INPUT_LENGTH >= 1000
            
            logger.info("✅ Configuration validation passed")
            return True
        except AssertionError as e:
            logger.error(f"❌ Configuration validation failed: {e}")
            return False
    
    @classmethod
    def create_directories(cls) -> None:
        """Creates all required directories"""
        # Import logger here to avoid circular import
        from src.utils.logger import logger
        
        directories = [cls.EXPORT_DIR, cls.BACKUP_DIR, cls.LOG_DIR]
        
        try:
            for directory in directories:
                directory.mkdir(exist_ok=True, parents=True)
                logger.debug(f"📁 Directory ready: {directory}")
            logger.info("✅ All application directories initialized")
        except Exception as e:
            logger.error(f"❌ Failed to create directories: {e}")
            raise


# Initialize directories and validate
AppConfig.create_directories()
if not AppConfig.validate():
    raise RuntimeError("❌ Configuration validation failed")
