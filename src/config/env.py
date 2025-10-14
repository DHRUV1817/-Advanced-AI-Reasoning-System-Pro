"""
Environment variable loader
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from src.utils.logger import logger


def load_environment() -> None:
    """
    Load environment variables from .env file
    """
    env_path = Path('.env')
    
    if env_path.exists():
        load_dotenv(env_path)
        logger.info("✅ Environment variables loaded from .env")
    else:
        logger.warning("⚠️ No .env file found. Using default configuration.")
    
    # Validate required environment variables
    required_vars = ['GROQ_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            "Please create a .env file with these variables."
        )
    
    logger.info("✅ All required environment variables validated")
