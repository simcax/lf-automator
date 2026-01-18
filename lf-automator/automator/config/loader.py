"""Configuration loader for token inventory tracking."""

import os
from typing import Dict

from dotenv import load_dotenv


class ConfigLoader:
    """Loads and validates configuration from environment variables and files."""

    # Default configuration values
    DEFAULT_THRESHOLD = 10
    DEFAULT_SCHEDULE = "0 9 * * *"  # 9 AM daily
    DEFAULT_EMAIL_SENDER = "noreply@lejrefitness.dk"
    DEFAULT_EMAIL_TEMPLATE = "templates/threshold_alert.html"

    @staticmethod
    def load_config() -> Dict:
        """Load configuration from environment and files.

        Returns validated configuration dictionary with all required settings.
        Loads from .env file if present, then reads environment variables.
        Uses safe defaults for missing values and logs warnings.

        Returns:
            Dict containing validated configuration with keys:
                - threshold: int
                - email_sender: str
                - email_recipients: List[str]
                - email_template: str
                - schedule: str (cron format)
                - database: Dict with connection settings
                - api: Dict with Foreninglet API settings
        """
        # Load .env file if present
        load_dotenv()

        config = {
            "threshold": ConfigLoader.get_threshold(),
            "email": ConfigLoader.get_email_config(),
            "schedule": ConfigLoader.get_schedule_config(),
            "database": ConfigLoader._get_database_config(),
            "api": ConfigLoader._get_api_config(),
        }

        # Validate configuration at startup
        ConfigLoader._validate_config(config)

        return config

    @staticmethod
    def get_threshold() -> int:
        """Get token threshold value with default fallback.

        Returns:
            Token threshold as integer. Defaults to 10 if not configured
            or if configured value is invalid.
        """
        threshold_str = os.getenv("TOKEN_THRESHOLD")

        if threshold_str is None:
            return ConfigLoader.DEFAULT_THRESHOLD

        try:
            threshold = int(threshold_str)
            if threshold < 0:
                print(
                    f"Warning: TOKEN_THRESHOLD must be non-negative, using default {ConfigLoader.DEFAULT_THRESHOLD}"
                )
                return ConfigLoader.DEFAULT_THRESHOLD
            return threshold
        except ValueError:
            print(
                f"Warning: Invalid TOKEN_THRESHOLD value '{threshold_str}', using default {ConfigLoader.DEFAULT_THRESHOLD}"
            )
            return ConfigLoader.DEFAULT_THRESHOLD

    @staticmethod
    def get_email_config() -> Dict:
        """Get email configuration with validation.

        Returns:
            Dict containing:
                - sender: Email sender address
                - recipients: List of recipient email addresses
                - template: Path to email template file
                - api_key: SendGrid API key

        Validates that required fields are present and properly formatted.
        Uses defaults where appropriate.
        """
        sender = os.getenv("ALERT_EMAIL_SENDER", ConfigLoader.DEFAULT_EMAIL_SENDER)

        # Parse recipients from comma-separated list
        recipients_str = os.getenv("ALERT_EMAIL_RECIPIENTS", "")
        recipients = [r.strip() for r in recipients_str.split(",") if r.strip()]

        if not recipients:
            print(
                "Warning: No ALERT_EMAIL_RECIPIENTS configured, alerts will not be sent"
            )

        template = os.getenv(
            "ALERT_EMAIL_TEMPLATE", ConfigLoader.DEFAULT_EMAIL_TEMPLATE
        )

        api_key = os.getenv("SENDGRID_API_KEY", "")
        if not api_key:
            print("Warning: SENDGRID_API_KEY not configured, email sending will fail")

        return {
            "sender": sender,
            "recipients": recipients,
            "template": template,
            "api_key": api_key,
        }

    @staticmethod
    def get_schedule_config() -> Dict:
        """Get scheduling configuration with cron parsing.

        Returns:
            Dict containing:
                - cron: Cron expression string (e.g., "0 9 * * *")
                - enabled: Boolean indicating if scheduling is enabled

        Validates cron format and provides safe defaults.
        """
        cron = os.getenv("DAILY_COUNT_SCHEDULE", ConfigLoader.DEFAULT_SCHEDULE)

        # Basic cron validation (5 fields separated by spaces)
        cron_parts = cron.split()
        if len(cron_parts) != 5:
            print(
                f"Warning: Invalid cron format '{cron}', using default {ConfigLoader.DEFAULT_SCHEDULE}"
            )
            cron = ConfigLoader.DEFAULT_SCHEDULE

        # Check if scheduling is explicitly disabled
        enabled = os.getenv("DAILY_COUNT_ENABLED", "true").lower() in (
            "true",
            "1",
            "yes",
        )

        return {
            "cron": cron,
            "enabled": enabled,
        }

    @staticmethod
    def _get_database_config() -> Dict:
        """Get database configuration from environment.

        Returns:
            Dict containing database connection settings:
                - host, port, name, username, password
        """
        return {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "name": os.getenv("DB_NAME", "lfautomator"),
            "username": os.getenv("DB_USERNAME", ""),
            "password": os.getenv("DB_PASSWORD", ""),
        }

    @staticmethod
    def _get_api_config() -> Dict:
        """Get Foreninglet API configuration from environment.

        Returns:
            Dict containing API settings:
                - base_url, username, password, version
        """
        return {
            "base_url": os.getenv("API_BASE_URL", ""),
            "username": os.getenv("API_USERNAME", ""),
            "password": os.getenv("API_PASSWORD", ""),
            "version": os.getenv("API_VERSION", "version=1"),
        }

    @staticmethod
    def _validate_config(config: Dict) -> None:
        """Validate configuration values at startup.

        Args:
            config: Configuration dictionary to validate

        Logs warnings for missing or invalid required configuration.
        Does not raise exceptions to allow graceful degradation.
        """
        # Validate threshold
        if config["threshold"] < 0:
            print("Warning: Threshold cannot be negative")

        # Validate email configuration
        if not config["email"]["recipients"]:
            print("Warning: No email recipients configured")

        if not config["email"]["api_key"]:
            print("Warning: SendGrid API key not configured")

        # Validate database configuration
        if not config["database"]["username"] or not config["database"]["password"]:
            print("Warning: Database credentials not fully configured")

        # Validate API configuration
        if (
            not config["api"]["base_url"]
            or not config["api"]["username"]
            or not config["api"]["password"]
        ):
            print("Warning: Foreninglet API credentials not fully configured")

        # Validate schedule
        if config["schedule"]["enabled"] and not config["schedule"]["cron"]:
            print("Warning: Scheduling enabled but no cron expression configured")
