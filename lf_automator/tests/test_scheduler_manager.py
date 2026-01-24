"""Tests for the scheduler manager module."""

from unittest.mock import MagicMock, patch


class TestSchedulerManager:
    """Tests for scheduler manager initialization and shutdown."""

    @patch("lf_automator.webapp.scheduler_manager.ConfigLoader.load_config")
    @patch("lf_automator.webapp.scheduler_manager.TokenInventoryAutomator")
    @patch("lf_automator.webapp.scheduler_manager.DailyScheduler")
    def test_init_scheduler_success(
        self, mock_scheduler_class, mock_automator_class, mock_config_loader
    ):
        """Test successful scheduler initialization."""
        from lf_automator.webapp.scheduler_manager import init_scheduler

        # Mock configuration
        mock_config = {
            "schedule": {"enabled": True, "cron": "0 9 * * *"},
            "threshold": 10,
        }
        mock_config_loader.return_value = mock_config

        # Mock automator
        mock_automator = MagicMock()
        mock_automator_class.return_value = mock_automator

        # Mock scheduler
        mock_scheduler = MagicMock()
        mock_scheduler.get_next_run_time.return_value = "2026-01-21 09:00:00"
        mock_scheduler_class.return_value = mock_scheduler

        # Initialize scheduler
        result = init_scheduler()

        # Verify scheduler was created and started
        assert result == mock_scheduler
        mock_scheduler_class.assert_called_once_with(
            automator=mock_automator, schedule_config=mock_config["schedule"]
        )
        mock_scheduler.start.assert_called_once()

    @patch("lf_automator.webapp.scheduler_manager.ConfigLoader.load_config")
    def test_init_scheduler_disabled(self, mock_config_loader):
        """Test scheduler initialization when disabled in config."""
        from lf_automator.webapp.scheduler_manager import init_scheduler

        # Mock configuration with scheduling disabled
        mock_config = {"schedule": {"enabled": False, "cron": "0 9 * * *"}}
        mock_config_loader.return_value = mock_config

        # Initialize scheduler
        result = init_scheduler()

        # Verify scheduler was not created
        assert result is None

    @patch("lf_automator.webapp.scheduler_manager.ConfigLoader.load_config")
    def test_init_scheduler_handles_errors(self, mock_config_loader):
        """Test scheduler initialization handles errors gracefully."""
        from lf_automator.webapp.scheduler_manager import init_scheduler

        # Mock configuration to raise an error
        mock_config_loader.side_effect = Exception("Configuration error")

        # Initialize scheduler - should not raise, returns None
        result = init_scheduler()

        # Verify scheduler was not created
        assert result is None

    def test_shutdown_scheduler_success(self):
        """Test successful scheduler shutdown."""
        from lf_automator.webapp.scheduler_manager import shutdown_scheduler

        # Mock scheduler
        mock_scheduler = MagicMock()

        # Shutdown scheduler
        shutdown_scheduler(mock_scheduler)

        # Verify stop was called
        mock_scheduler.stop.assert_called_once()

    def test_shutdown_scheduler_with_none(self):
        """Test shutdown with None scheduler."""
        from lf_automator.webapp.scheduler_manager import shutdown_scheduler

        # Should not raise an error
        shutdown_scheduler(None)

    def test_shutdown_scheduler_handles_errors(self):
        """Test shutdown handles errors gracefully."""
        from lf_automator.webapp.scheduler_manager import shutdown_scheduler

        # Mock scheduler that raises error on stop
        mock_scheduler = MagicMock()
        mock_scheduler.stop.side_effect = Exception("Shutdown error")

        # Should not raise an error
        shutdown_scheduler(mock_scheduler)
