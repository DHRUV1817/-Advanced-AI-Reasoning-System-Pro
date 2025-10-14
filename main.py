"""
Main application entry point
"""
from src.config.env import load_environment
from src.config.settings import AppConfig
from src.config.constants import ReasoningMode, ModelConfig
from src.ui.app import create_ui
from src.utils.logger import logger


def main():
    """
    🚀 APPLICATION ENTRY POINT
    """
    try:
        # Load environment variables
        load_environment()
        
        # Print startup information
        logger.info("="*60)
        logger.info("🚀 Starting Advanced AI Reasoning System Pro...")
        logger.info(f"🌍 Environment: {AppConfig.ENV}")
        logger.info(f"🎨 Theme: {AppConfig.THEME_PRIMARY}/{AppConfig.THEME_SECONDARY}")
        logger.info(f"🤖 Available Models: {len(ModelConfig)}")
        logger.info(f"🧠 Reasoning Modes: {len(ReasoningMode)}")
        logger.info(f"💾 Cache: {AppConfig.CACHE_SIZE} entries")
        logger.info(f"⏱️  Rate Limit: {AppConfig.RATE_LIMIT_REQUESTS} req/{AppConfig.RATE_LIMIT_WINDOW}s")
        logger.info("🎛️ Features: Collapsible Sidebar, PDF Export, Real-time Analytics")
        logger.info("="*60)
        
        # Create and launch UI
        demo = create_ui()
        demo.launch(
            share=False,
            server_name="0.0.0.0",
            server_port=7860,
            show_error=True,
            show_api=False,
            favicon_path=None,
            max_threads=AppConfig.MAX_WORKERS
        )
        
    except KeyboardInterrupt:
        logger.info("⏹️  Application stopped by user (Ctrl+C)")
    except Exception as e:
        logger.critical(f"❌ Failed to start application: {e}", exc_info=True)
        raise
    finally:
        logger.info("👋 Shutting down gracefully...")


if __name__ == "__main__":
    main()
