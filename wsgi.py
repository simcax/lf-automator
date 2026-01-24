"""WSGI entry point for production deployment with gunicorn."""

from lf_automator.webapp.app import create_app

# Create the application instance
application = create_app()

if __name__ == "__main__":
    application.run()
