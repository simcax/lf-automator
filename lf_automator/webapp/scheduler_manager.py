"""Scheduler manager for Flask web application.

This module manages the APScheduler background task that runs the daily
token inventory tracking workflow. It initializes the scheduler when the
Flask app starts and ensures proper cleanup on shutdown.
"""

from typing import Optional

from lf_automator.automator.config.loader import ConfigLoader
from lf_automator.automator.inventoryautomator.automator import TokenInventoryAutomator
from lf_automator.automator.scheduler.scheduler import DailyScheduler
from loguru import logger


def init_scheduler() -> Optional[DailyScheduler]:
    """Initialize and start the background scheduler.

    Loads configuration, creates the TokenInventoryAutomator and DailyScheduler
    instances, and starts the scheduler if enabled in configuration.

    Returns:
        DailyScheduler instance if successfully started, None if disabled or failed

    Raises:
        Exception: If critical initialization fails (logged but not raised)
    """
    try:
        logger.info("Initializing background scheduler...")

        # Load configuration
        config = ConfigLoader.load_config()
        logger.debug("Configuration loaded successfully")

        # Check if scheduling is enabled
        if not config.get("schedule", {}).get("enabled", True):
            logger.info("Scheduling is disabled in configuration")
            return None

        # Initialize the token inventory automator
        automator = TokenInventoryAutomator(config=config)
        logger.debug("TokenInventoryAutomator initialized")

        # Initialize the scheduler
        scheduler = DailyScheduler(
            automator=automator, schedule_config=config["schedule"]
        )
        logger.debug("DailyScheduler instance created")

        # Start the scheduler
        scheduler.start()

        next_run = scheduler.get_next_run_time()
        if next_run:
            logger.info(f"Background scheduler started. Next execution: {next_run}")
        else:
            logger.warning("Scheduler started but no next run time available")

        return scheduler

    except Exception as error:
        logger.error(f"Failed to initialize scheduler: {error}")
        # Return None instead of raising to allow app to continue
        return None


def shutdown_scheduler(scheduler: Optional[DailyScheduler]) -> None:
    """Gracefully shutdown the scheduler.

    Args:
        scheduler: DailyScheduler instance to shutdown, or None
    """
    if scheduler is None:
        logger.debug("No scheduler to shutdown")
        return

    try:
        logger.info("Shutting down background scheduler...")
        scheduler.stop()
        logger.info("Background scheduler stopped successfully")
    except Exception as error:
        logger.error(f"Error shutting down scheduler: {error}")
