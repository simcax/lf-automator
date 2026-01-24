"""DailyScheduler component for managing scheduled execution of token counting workflow."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from lf_automator.automator.counttimestamp.timestamp import CountTimestampManager
from lf_automator.automator.inventoryautomator.automator import TokenInventoryAutomator

logger = logging.getLogger(__name__)


class DailyScheduler:
    """Manages scheduled execution of the daily token counting workflow using APScheduler."""

    def __init__(self, automator: TokenInventoryAutomator, schedule_config: Dict):
        """Initialize with automator instance and schedule configuration.

        Args:
            automator: TokenInventoryAutomator instance to execute
            schedule_config: Dict containing:
                - cron: Cron expression string (e.g., "0 9 * * *")
                - enabled: Boolean indicating if scheduling is enabled
        """
        self.automator = automator
        self.schedule_config = schedule_config
        self.scheduler: Optional[BackgroundScheduler] = None
        self.job_id = "daily_token_count"
        self.job_name = "Daily Token Count"

        # Get timestamp manager for execution history
        self.timestamp_manager = CountTimestampManager(db=automator.db)

        logger.info(
            f"DailyScheduler initialized with schedule: {schedule_config.get('cron', 'N/A')}"
        )

    def start(self) -> None:
        """Start the scheduler with configured schedule.

        Creates a BackgroundScheduler, configures the cron trigger,
        and starts the scheduler. The scheduler will run in the background
        and execute the daily count workflow according to the cron schedule.

        Raises:
            ValueError: If scheduler is already running or configuration is invalid
        """
        if self.scheduler is not None and self.scheduler.running:
            raise ValueError("Scheduler is already running")

        if not self.schedule_config.get("enabled", True):
            logger.info("Scheduling is disabled in configuration")
            return

        cron_expression = self.schedule_config.get("cron")
        if not cron_expression:
            raise ValueError("No cron expression provided in schedule configuration")

        try:
            # Create BackgroundScheduler
            self.scheduler = BackgroundScheduler()

            # Parse cron expression and create trigger
            cron_parts = cron_expression.split()
            if len(cron_parts) != 5:
                raise ValueError(
                    f"Invalid cron expression: {cron_expression}. Expected 5 fields."
                )

            trigger = CronTrigger.from_crontab(cron_expression)

            # Add job to scheduler
            self.scheduler.add_job(
                func=self._execute_workflow,
                trigger=trigger,
                id=self.job_id,
                name=self.job_name,
                replace_existing=True,
            )

            # Start the scheduler
            self.scheduler.start()

            next_run = self.get_next_run_time()
            logger.info(f"Scheduler started successfully. Next run: {next_run}")

        except Exception as error:
            logger.error(f"Failed to start scheduler: {error}")
            raise ValueError(f"Failed to start scheduler: {error}")

    def stop(self) -> None:
        """Stop the scheduler gracefully.

        Shuts down the scheduler, allowing any currently running jobs
        to complete before stopping.

        Raises:
            ValueError: If scheduler is not running
        """
        if self.scheduler is None or not self.scheduler.running:
            logger.warning("Scheduler is not running")
            return

        try:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped successfully")
            self.scheduler = None
        except Exception as error:
            logger.error(f"Error stopping scheduler: {error}")
            raise ValueError(f"Error stopping scheduler: {error}")

    def run_now(self) -> Dict:
        """Manually trigger an immediate execution.

        Executes the daily count workflow immediately, bypassing the schedule.
        Useful for testing and emergency runs.

        Returns:
            Execution summary dict from TokenInventoryAutomator.run_daily_count()

        Raises:
            RuntimeError: If execution fails
        """
        logger.info("Manual execution triggered")
        try:
            summary = self.automator.run_daily_count()
            logger.info(f"Manual execution completed: status={summary['status']}")
            return summary
        except Exception as error:
            logger.error(f"Manual execution failed: {error}")
            raise RuntimeError(f"Manual execution failed: {error}")

    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled execution time.

        Returns:
            Datetime of next scheduled run, or None if scheduler is not running

        Raises:
            ValueError: If scheduler is not initialized
        """
        if self.scheduler is None:
            raise ValueError("Scheduler is not initialized")

        if not self.scheduler.running:
            return None

        job = self.scheduler.get_job(self.job_id)
        if job is None:
            return None

        return job.next_run_time

    def get_execution_history(self, limit: int = 10) -> List[Dict]:
        """Get recent execution history from CountTimestampManager.

        Args:
            limit: Maximum number of records to return (default: 10)

        Returns:
            List of dicts with execution history:
                - timestamp_uuid: str
                - count_type: str
                - last_count_at: datetime
                - execution_status: str
                - tokens_distributed: int
                - metadata: dict

        Raises:
            ValueError: If database operation fails
        """
        try:
            return self.timestamp_manager.get_count_history(limit=limit)
        except Exception as error:
            logger.error(f"Error getting execution history: {error}")
            raise ValueError(f"Error getting execution history: {error}")

    def _execute_workflow(self) -> None:
        """Internal method to execute the workflow.

        This is called by the scheduler at the scheduled times.
        Wraps the automator's run_daily_count() method with logging.
        """
        logger.info("Scheduled execution starting")
        try:
            summary = self.automator.run_daily_count()
            logger.info(
                f"Scheduled execution completed: status={summary['status']}, "
                f"tokens_distributed={summary['tokens_distributed']}"
            )
        except Exception as error:
            logger.error(f"Scheduled execution failed: {error}")
            # Don't re-raise - we want the scheduler to continue running

    def __del__(self):
        """Clean up scheduler on deletion."""
        if self.scheduler is not None and self.scheduler.running:
            try:
                self.scheduler.shutdown(wait=False)
            except Exception:
                pass  # Ignore errors during cleanup
