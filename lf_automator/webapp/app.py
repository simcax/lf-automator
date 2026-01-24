"""Flask application factory for the web dashboard."""

import atexit
import os

from flask import Flask
from loguru import logger


def create_app() -> Flask:
    """Create and configure the Flask application.

    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # Load configuration from environment variables
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", os.urandom(32).hex())
    app.config["ACCESS_KEY"] = os.environ.get("ACCESS_KEY", "test")
    logger.debug(f"Access Key {app.config['ACCESS_KEY']}")

    # Session configuration with secure cookie settings
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production"
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Register blueprints
    from lf_automator.webapp.routes import bp as routes_bp

    app.register_blueprint(routes_bp)

    # Initialize and start the background scheduler
    try:
        from lf_automator.webapp.scheduler_manager import (
            init_scheduler,
            shutdown_scheduler,
        )

        scheduler = init_scheduler()
        if scheduler:
            logger.info("Background scheduler initialized successfully")
            # Register cleanup function to stop scheduler on app shutdown
            atexit.register(lambda: shutdown_scheduler(scheduler))
        else:
            logger.warning("Scheduler initialization skipped (disabled in config)")
    except Exception as error:
        logger.error(f"Failed to initialize background scheduler: {error}")
        # Don't fail app startup if scheduler fails
        logger.warning("Application will continue without background scheduler")

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 8080))
    app.run(
        host="0.0.0.0", port=port, debug=os.environ.get("FLASK_ENV") == "development"
    )
