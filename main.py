"""Entry point. Default mode: launches FastAPI backend in-process and the
Gradio UI on top of it. --no-backend skips the FastAPI process (use when
running a separate uvicorn / Next.js dev server)."""
import argparse
import asyncio
import threading
import uvicorn
from src.config.env import load_environment
from src.config.settings import AppConfig
from src.config.constants import ReasoningMode, ModelConfig
from src.ui.app import create_ui
from src.utils.logger import logger


def _start_backend_in_thread():
    """Run uvicorn in a background daemon thread so Gradio gets the main
    thread (its launcher manages signal handling there)."""
    config = uvicorn.Config(
        "src.api.server:app",
        host=AppConfig.API_HOST, port=AppConfig.API_PORT,
        log_level="warning", access_log=False,
    )
    server = uvicorn.Server(config)
    t = threading.Thread(target=lambda: asyncio.run(server.serve()), daemon=True)
    t.start()
    return server


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

        # Parse CLI arguments
        parser = argparse.ArgumentParser()
        parser.add_argument("--no-backend", action="store_true",
                            help="don't start FastAPI in-process (assume external uvicorn)")
        args = parser.parse_args()

        # Start FastAPI backend in background thread (unless disabled)
        if not args.no_backend:
            _start_backend_in_thread()

        # Create and launch Gradio UI (holds main thread)
        demo = create_ui()
        demo.launch(
            share=False,
            server_name="127.0.0.1",
            server_port=7860,
            show_error=True,
            max_threads=AppConfig.MAX_WORKERS,
            theme=getattr(demo, "_theme", None),
            css=getattr(demo, "_css", None),
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
