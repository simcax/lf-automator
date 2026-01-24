"""Unit tests for ConfigLoader component."""

import os
from unittest.mock import patch

from lf_automator.automator.config import ConfigLoader


class TestConfigLoader:
    """Test suite for ConfigLoader."""

    def test_load_config_returns_complete_structure(self):
        """Test that load_config returns all required configuration sections."""
        config = ConfigLoader.load_config()

        assert "threshold" in config
        assert "email" in config
        assert "schedule" in config
        assert "database" in config
        assert "api" in config

    def test_get_threshold_with_valid_value(self):
        """Test threshold loading with valid environment variable."""
        with patch.dict(os.environ, {"TOKEN_THRESHOLD": "25"}):
            threshold = ConfigLoader.get_threshold()
            assert threshold == 25

    def test_get_threshold_with_missing_value(self):
        """Test threshold loading with missing environment variable uses default."""
        with patch.dict(os.environ, {}, clear=True):
            threshold = ConfigLoader.get_threshold()
            assert threshold == ConfigLoader.DEFAULT_THRESHOLD

    def test_get_threshold_with_invalid_value(self):
        """Test threshold loading with invalid value uses default."""
        with patch.dict(os.environ, {"TOKEN_THRESHOLD": "invalid"}):
            threshold = ConfigLoader.get_threshold()
            assert threshold == ConfigLoader.DEFAULT_THRESHOLD

    def test_get_threshold_with_negative_value(self):
        """Test threshold loading with negative value uses default."""
        with patch.dict(os.environ, {"TOKEN_THRESHOLD": "-5"}):
            threshold = ConfigLoader.get_threshold()
            assert threshold == ConfigLoader.DEFAULT_THRESHOLD

    def test_get_email_config_with_valid_values(self):
        """Test email configuration loading with valid values."""
        env = {
            "ALERT_EMAIL_SENDER": "test@example.com",
            "ALERT_EMAIL_RECIPIENTS": "admin1@example.com,admin2@example.com",
            "ALERT_EMAIL_TEMPLATE": "custom_template.html",
            "SENDGRID_API_KEY": "test_api_key",
        }
        with patch.dict(os.environ, env):
            email_config = ConfigLoader.get_email_config()

            assert email_config["sender"] == "test@example.com"
            assert email_config["recipients"] == [
                "admin1@example.com",
                "admin2@example.com",
            ]
            assert email_config["template"] == "custom_template.html"
            assert email_config["api_key"] == "test_api_key"

    def test_get_email_config_with_missing_values(self):
        """Test email configuration loading with missing values uses defaults."""
        with patch.dict(os.environ, {}, clear=True):
            email_config = ConfigLoader.get_email_config()

            assert email_config["sender"] == ConfigLoader.DEFAULT_EMAIL_SENDER
            assert email_config["recipients"] == []
            assert email_config["template"] == ConfigLoader.DEFAULT_EMAIL_TEMPLATE
            assert email_config["api_key"] == ""

    def test_get_email_config_with_whitespace_recipients(self):
        """Test email configuration handles whitespace in recipient list."""
        env = {"ALERT_EMAIL_RECIPIENTS": " admin1@example.com , admin2@example.com , "}
        with patch.dict(os.environ, env):
            email_config = ConfigLoader.get_email_config()
            assert email_config["recipients"] == [
                "admin1@example.com",
                "admin2@example.com",
            ]

    def test_get_schedule_config_with_valid_cron(self):
        """Test schedule configuration with valid cron expression."""
        env = {"DAILY_COUNT_SCHEDULE": "0 8 * * *"}
        with patch.dict(os.environ, env):
            schedule_config = ConfigLoader.get_schedule_config()

            assert schedule_config["cron"] == "0 8 * * *"
            assert schedule_config["enabled"] is True

    def test_get_schedule_config_with_invalid_cron(self):
        """Test schedule configuration with invalid cron uses default."""
        env = {"DAILY_COUNT_SCHEDULE": "invalid cron"}
        with patch.dict(os.environ, env):
            schedule_config = ConfigLoader.get_schedule_config()

            assert schedule_config["cron"] == ConfigLoader.DEFAULT_SCHEDULE

    def test_get_schedule_config_with_disabled_scheduling(self):
        """Test schedule configuration when scheduling is disabled."""
        env = {"DAILY_COUNT_ENABLED": "false"}
        with patch.dict(os.environ, env):
            schedule_config = ConfigLoader.get_schedule_config()

            assert schedule_config["enabled"] is False

    def test_get_schedule_config_with_missing_values(self):
        """Test schedule configuration with missing values uses defaults."""
        with patch.dict(os.environ, {}, clear=True):
            schedule_config = ConfigLoader.get_schedule_config()

            assert schedule_config["cron"] == ConfigLoader.DEFAULT_SCHEDULE
            assert schedule_config["enabled"] is True

    def test_database_config_loading(self):
        """Test database configuration loading."""
        env = {
            "POSTGRESQL_ADDON_HOST": "testhost",
            "POSTGRESQL_ADDON_PORT": "5433",
            "POSTGRESQL_ADDON_DB": "testdb",
            "POSTGRESQL_ADDON_USER": "testuser",
            "POSTGRESQL_ADDON_PASSWORD": "testpass",
        }
        with patch.dict(os.environ, env, clear=True):
            config = ConfigLoader.load_config()
            db_config = config["database"]

            assert db_config["host"] == "testhost"
            assert db_config["port"] == 5433
            assert db_config["name"] == "testdb"
            assert db_config["username"] == "testuser"
            assert db_config["password"] == "testpass"

    def test_api_config_loading(self):
        """Test API configuration loading."""
        env = {
            "API_BASE_URL": "https://test.api.com/",
            "API_USERNAME": "testuser",
            "API_PASSWORD": "testpass",
            "API_VERSION": "version=2",
        }
        with patch.dict(os.environ, env):
            config = ConfigLoader.load_config()
            api_config = config["api"]

            assert api_config["base_url"] == "https://test.api.com/"
            assert api_config["username"] == "testuser"
            assert api_config["password"] == "testpass"
            assert api_config["version"] == "version=2"

    def test_environment_variable_precedence(self):
        """Test that environment variables take precedence over defaults."""
        env = {
            "TOKEN_THRESHOLD": "50",
            "ALERT_EMAIL_SENDER": "custom@example.com",
        }
        with patch.dict(os.environ, env):
            config = ConfigLoader.load_config()

            assert config["threshold"] == 50
            assert config["email"]["sender"] == "custom@example.com"

    def test_validation_does_not_raise_exceptions(self):
        """Test that validation logs warnings but doesn't raise exceptions."""
        # Clear all environment variables to trigger validation warnings
        with patch.dict(os.environ, {}, clear=True):
            # Should not raise any exceptions
            config = ConfigLoader.load_config()
            assert config is not None
