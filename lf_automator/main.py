#!/usr/bin/env python3
"""Main entry point for Token Inventory Tracking system.

This module provides the CLI interface for the token inventory tracking
automation system. It supports both scheduled execution and manual runs.

Usage:
    python -m lf-automator.main                    # Start scheduler
    python -m lf-automator.main --run-now          # Manual execution
    python -m lf-automator.main --status           # Check status
    python -m lf-automator.main --history          # View execution history
"""

import argparse
import logging
import signal
import sys
from datetime import datetime
from typing import Optional

from automator.config.loader import ConfigLoader
from automator.inventoryautomator.automator import TokenInventoryAutomator
from automator.scheduler.scheduler import DailyScheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# Global scheduler instance for signal handling
_scheduler: Optional[DailyScheduler] = None


def setup_signal_handlers(scheduler: DailyScheduler) -> None:
    """Set up graceful shutdown handlers for SIGINT and SIGTERM.

    Args:
        scheduler: DailyScheduler instance to stop on shutdown
    """

    def signal_handler(signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        try:
            scheduler.stop()
            logger.info("Scheduler stopped successfully")
        except Exception as error:
            logger.error(f"Error during shutdown: {error}")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def run_scheduled_mode(config: dict) -> int:
    """Run the scheduler in daemon mode.

    Args:
        config: Configuration dictionary

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    global _scheduler

    try:
        logger.info("Starting Token Inventory Tracking in scheduled mode")

        # Initialize automator
        automator = TokenInventoryAutomator(config=config)

        # Initialize scheduler
        scheduler = DailyScheduler(
            automator=automator, schedule_config=config["schedule"]
        )
        _scheduler = scheduler

        # Set up signal handlers for graceful shutdown
        setup_signal_handlers(scheduler)

        # Start scheduler
        scheduler.start()

        next_run = scheduler.get_next_run_time()
        if next_run:
            logger.info(f"Scheduler started. Next execution: {next_run}")
        else:
            logger.warning("Scheduler started but no next run time available")

        # Keep the main thread alive
        logger.info("Press Ctrl+C to stop the scheduler")
        signal.pause()  # Wait for signals

        return 0

    except Exception as error:
        logger.error(f"Failed to start scheduled mode: {error}")
        return 1


def run_manual_execution(config: dict) -> int:
    """Execute the daily count workflow immediately.

    Args:
        config: Configuration dictionary

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        logger.info("Starting manual token count execution")

        # Initialize automator
        automator = TokenInventoryAutomator(config=config)

        # Execute workflow
        summary = automator.run_daily_count()

        # Print summary
        print("\n" + "=" * 60)
        print("EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Execution Time:      {summary['execution_time']}")
        print(f"Status:              {summary['status'].upper()}")
        print(f"Tokens Distributed:  {summary['tokens_distributed']}")
        print(f"Previous Total:      {summary['previous_total']}")
        print(f"Current Total:       {summary['current_total']}")
        print(f"Threshold:           {summary['threshold']}")
        print(f"Alert Sent:          {'Yes' if summary['alert_sent'] else 'No'}")

        if summary["errors"]:
            print(f"\nErrors ({len(summary['errors'])}):")
            for error in summary["errors"]:
                print(f"  - {error}")

        print("=" * 60 + "\n")

        # Return appropriate exit code
        if summary["status"] == "success":
            return 0
        elif summary["status"] == "partial":
            logger.warning("Execution completed with errors")
            return 0  # Still return 0 for partial success
        else:
            logger.error("Execution failed")
            return 1

    except Exception as error:
        logger.error(f"Manual execution failed: {error}")
        return 1


def show_status(config: dict) -> int:
    """Show current system status.

    Args:
        config: Configuration dictionary

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        logger.info("Checking system status")

        # Initialize automator to access components
        automator = TokenInventoryAutomator(config=config)

        # Get current token pool status
        total_tokens = automator.token_pool.get_total_available_tokens()
        threshold = config["threshold"]

        # Get last execution info
        timestamp_manager = automator.timestamp_manager
        last_count = timestamp_manager.get_last_count_timestamp()

        # Get alert state
        alert_state = automator.alert_manager.get_alert_state()

        # Print status
        print("\n" + "=" * 60)
        print("SYSTEM STATUS")
        print("=" * 60)
        print(f"Current Token Total:  {total_tokens}")
        print(f"Threshold:            {threshold}")
        print(
            f"Status:               {'⚠️  BELOW THRESHOLD' if total_tokens < threshold else '✓ OK'}"
        )
        print(f"Last Count:           {last_count}")
        print(
            f"Alert Active:         {'Yes' if alert_state.get('is_active', False) else 'No'}"
        )

        if alert_state.get("last_triggered"):
            print(f"Last Alert:           {alert_state['last_triggered']}")

        print("\nConfiguration:")
        print(f"  Schedule:           {config['schedule']['cron']}")
        print(
            f"  Scheduling Enabled: {'Yes' if config['schedule']['enabled'] else 'No'}"
        )
        print(f"  Email Recipients:   {', '.join(config['email']['recipients'])}")
        print("=" * 60 + "\n")

        return 0

    except Exception as error:
        logger.error(f"Failed to get status: {error}")
        return 1


def show_history(config: dict, limit: int = 10) -> int:
    """Show execution history.

    Args:
        config: Configuration dictionary
        limit: Number of records to show

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        logger.info(f"Retrieving last {limit} execution records")

        # Initialize automator to access components
        automator = TokenInventoryAutomator(config=config)

        # Get execution history
        history = automator.timestamp_manager.get_count_history(limit=limit)

        if not history:
            print("\nNo execution history found.\n")
            return 0

        # Print history
        print("\n" + "=" * 80)
        print("EXECUTION HISTORY")
        print("=" * 80)
        print(
            f"{'Timestamp':<20} {'Status':<12} {'Tokens':<10} {'Total':<10} {'Threshold':<10}"
        )
        print("-" * 80)

        for record in history:
            timestamp = record.get("last_count_at", "N/A")
            status = record.get("execution_status", "N/A")
            tokens = record.get("tokens_distributed", 0)
            metadata = record.get("metadata", {})
            total = metadata.get("current_total", "N/A")
            threshold = metadata.get("threshold", "N/A")

            # Format timestamp
            if isinstance(timestamp, datetime):
                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            else:
                timestamp_str = str(timestamp)

            print(
                f"{timestamp_str:<20} {status:<12} {tokens:<10} {total:<10} {threshold:<10}"
            )

        print("=" * 80 + "\n")

        return 0

    except Exception as error:
        logger.error(f"Failed to get history: {error}")
        return 1


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Token Inventory Tracking System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    Start scheduler (daemon mode)
  %(prog)s --run-now          Execute count immediately
  %(prog)s --status           Show current system status
  %(prog)s --history          Show execution history
  %(prog)s --history --limit 20  Show last 20 executions
        """,
    )

    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Execute the daily count workflow immediately instead of scheduling",
    )

    parser.add_argument(
        "--status", action="store_true", help="Show current system status and exit"
    )

    parser.add_argument(
        "--history",
        action="store_true",
        help="Show execution history and exit",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of history records to show (default: 10)",
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to custom .env configuration file",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging (DEBUG)"
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Parse arguments
    args = parse_arguments()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Load configuration
    try:
        logger.info("Loading configuration...")
        config = ConfigLoader.load_config()
        logger.info("Configuration loaded successfully")
    except Exception as error:
        logger.error(f"Failed to load configuration: {error}")
        return 1

    # Execute based on mode
    try:
        if args.status:
            return show_status(config)
        elif args.history:
            return show_history(config, limit=args.limit)
        elif args.run_now:
            return run_manual_execution(config)
        else:
            return run_scheduled_mode(config)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as error:
        logger.error(f"Unexpected error: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
