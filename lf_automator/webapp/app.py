"""Flask application factory for the web dashboard."""

import os

from flask import Flask


def create_app() -> Flask:
    """Create and configure the Flask application.

    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # Load configuration from environment variables
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", os.urandom(32).hex())
    app.config["ACCESS_KEY"] = os.environ.get("ACCESS_KEY", "")

    # Session configuration with secure cookie settings
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production"
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Register blueprints
    from webapp.routes import bp as routes_bp

    app.register_blueprint(routes_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 8080))
    app.run(
        host="0.0.0.0", port=port, debug=os.environ.get("FLASK_ENV") == "development"
    )
