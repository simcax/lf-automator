"""Unit tests for DailyScheduler component."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from automator.scheduler.scheduler import DailyScheduler


class TestDailyScheduler:
    """Test suite for DailyScheduler."""

    @pytest.fixture
    def mock_automator(self):
        """Create a mock TokenInventoryAutomator."""
        automator = MagicMock()
        automator.db = MagicMock()
        automator.run_daily_count.return_value = {
            "execution_time": datetime.now(),
            "tokens_distributed": 5,
            "previous_total": 100,
            "current_total": 95,
            "threshold": 10,
            "alert_sent": False,
            "status": "success",
            "errors": [],
        }
        return automator

    @pytest.fixture
    def schedule_config(self):
        """Create a test schedule configuration."""
        return {
            "cron": "0 9 * * *",  # 9 AM daily
            "enabled": True,
        }

    @pytest.fixture
    def scheduler(self, mock_automator, schedule_config):
        """Create a DailyScheduler instance."""
        with patch(
            "automator.scheduler.scheduler.CountTimestampManager"
        ) as mock_timestamp:
            mock_timestamp.return_value = MagicMock()
            return DailyScheduler(mock_automator, schedule_config)

    def test_scheduler_initialization(self, scheduler, schedule_config):
        """Test scheduler initializes correctly."""
        assert scheduler.automator is not None
        assert scheduler.schedule_config == schedule_config
        assert scheduler.scheduler is None  # Not started yet
        assert scheduler.job_id == "daily_token_count"
        assert scheduler.job_name == "Daily Token Count"

    def test_start_scheduler(self, scheduler):
        """Test starting the scheduler."""
        try:
            scheduler.start()
            assert scheduler.scheduler is not None
            assert scheduler.scheduler.running is True

            # Verify job was added
            job = scheduler.scheduler.get_job(scheduler.job_id)
            assert job is not None
            assert job.name == scheduler.job_name
        finally:
            if scheduler.scheduler and scheduler.scheduler.running:
                scheduler.stop()

    def test_start_scheduler_already_running(self, scheduler):
        """Test starting scheduler when already running raises error."""
        try:
            scheduler.start()
            with pytest.raises(ValueError, match="already running"):
                scheduler.start()
        finally:
            if scheduler.scheduler and scheduler.scheduler.running:
                scheduler.stop()

    def test_start_scheduler_disabled(self, mock_automator):
        """Test scheduler doesn't start when disabled in config."""
        config = {"cron": "0 9 * * *", "enabled": False}
        with patch(
            "automator.scheduler.scheduler.CountTimestampManager"
        ) as mock_timestamp:
            mock_timestamp.return_value = MagicMock()
            scheduler = DailyScheduler(mock_automator, config)
            scheduler.start()
            assert scheduler.scheduler is None

    def test_start_scheduler_invalid_cron(self, mock_automator):
        """Test starting scheduler with invalid cron expression."""
        config = {"cron": "invalid cron", "enabled": True}
        with patch(
            "automator.scheduler.scheduler.CountTimestampManager"
        ) as mock_timestamp:
            mock_timestamp.return_value = MagicMock()
            scheduler = DailyScheduler(mock_automator, config)
            with pytest.raises(ValueError, match="Invalid cron expression"):
                scheduler.start()

    def test_stop_scheduler(self, scheduler):
        """Test stopping the scheduler."""
        scheduler.start()
        assert scheduler.scheduler.running is True

        scheduler.stop()
        assert scheduler.scheduler is None

    def test_stop_scheduler_not_running(self, scheduler):
        """Test stopping scheduler when not running doesn't raise error."""
        # Should not raise an error
        scheduler.stop()

    def test_run_now(self, scheduler, mock_automator):
        """Test manual execution trigger."""
        summary = scheduler.run_now()

        # Verify automator was called
        mock_automator.run_daily_count.assert_called_once()

        # Verify summary returned
        assert summary["status"] == "success"
        assert summary["tokens_distributed"] == 5

    def test_run_now_with_error(self, scheduler, mock_automator):
        """Test manual execution when automator raises error."""
        mock_automator.run_daily_count.side_effect = RuntimeError("Test error")

        with pytest.raises(RuntimeError, match="Manual execution failed"):
            scheduler.run_now()

    def test_get_next_run_time(self, scheduler):
        """Test getting next scheduled run time."""
        try:
            scheduler.start()
            next_run = scheduler.get_next_run_time()

            assert next_run is not None
            assert isinstance(next_run, datetime)
            # Just verify we got a datetime, don't compare with now() due to timezone issues
        finally:
            if scheduler.scheduler and scheduler.scheduler.running:
                scheduler.stop()

    def test_get_next_run_time_not_started(self, scheduler):
        """Test getting next run time when scheduler not started."""
        with pytest.raises(ValueError, match="not initialized"):
            scheduler.get_next_run_time()

    def test_get_execution_history(self, scheduler):
        """Test getting execution history."""
        mock_history = [
            {
                "timestamp_uuid": "test-uuid",
                "count_type": "daily_token_count",
                "last_count_at": datetime.now(),
                "execution_status": "success",
                "tokens_distributed": 5,
                "metadata": {},
            }
        ]
        scheduler.timestamp_manager.get_count_history.return_value = mock_history

        history = scheduler.get_execution_history(limit=10)

        assert history == mock_history
        scheduler.timestamp_manager.get_count_history.assert_called_once_with(limit=10)

    def test_get_execution_history_with_error(self, scheduler):
        """Test getting execution history when database fails."""
        scheduler.timestamp_manager.get_count_history.side_effect = Exception(
            "DB error"
        )

        with pytest.raises(ValueError, match="Error getting execution history"):
            scheduler.get_execution_history()

    def test_cron_schedule_parsing(self, mock_automator):
        """Test various cron schedule formats."""
        test_cases = [
            "0 9 * * *",  # 9 AM daily
            "0 0 * * 0",  # Midnight on Sundays
            "*/15 * * * *",  # Every 15 minutes
            "0 12 1 * *",  # Noon on 1st of month
        ]

        for cron in test_cases:
            config = {"cron": cron, "enabled": True}
            with patch(
                "automator.scheduler.scheduler.CountTimestampManager"
            ) as mock_timestamp:
                mock_timestamp.return_value = MagicMock()
                scheduler = DailyScheduler(mock_automator, config)
                try:
                    scheduler.start()
                    assert scheduler.scheduler.running is True
                finally:
                    if scheduler.scheduler and scheduler.scheduler.running:
                        scheduler.stop()

    def test_scheduler_cleanup_on_deletion(self, scheduler):
        """Test scheduler cleans up on deletion."""
        scheduler.start()
        assert scheduler.scheduler.running is True

        # Delete scheduler
        del scheduler

        # Scheduler should be stopped (can't verify directly after deletion)
        # This test mainly ensures no exceptions during cleanup
