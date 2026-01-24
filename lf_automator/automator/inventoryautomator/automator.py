"""TokenInventoryAutomator orchestrator for daily token counting workflow."""

import logging
from datetime import datetime
from typing import Dict, Optional

from lf_automator.automator.alertmanager.alert import AlertManager
from lf_automator.automator.config.loader import ConfigLoader
from lf_automator.automator.counttimestamp.timestamp import CountTimestampManager
from lf_automator.automator.database.db import Database
from lf_automator.automator.mailer.send import Mailer
from lf_automator.automator.membersync.sync import MemberTokenSync
from lf_automator.automator.tokenpools.pools import TokenPool
from lf_automator.automator.tokenregistry.registry import TokenRegistry

logger = logging.getLogger(__name__)


class TokenInventoryAutomator:
    """Main orchestrator that coordinates the daily token counting workflow."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize with configuration dictionary.

        Args:
            config: Configuration dictionary. If None, loads from ConfigLoader.
        """
        # Load configuration
        if config is None:
            config = ConfigLoader.load_config()
        self.config = config

        # Initialize database connection
        self.db = Database()
        self.db.create_connection()

        # Initialize components
        self.registry = TokenRegistry(db=self.db)
        self.member_sync = MemberTokenSync(registry=self.registry)
        self.token_pool = TokenPool()
        self.timestamp_manager = CountTimestampManager(db=self.db)

        # Initialize mailer
        self.mailer = Mailer()
        self.mailer.sender = config["email"]["sender"]

        # Initialize alert manager
        self.alert_manager = AlertManager(
            db=self.db, mailer=self.mailer, threshold=config["threshold"]
        )

        logger.info("TokenInventoryAutomator initialized successfully")

    def run_daily_count(self) -> Dict:
        """Execute the complete daily token counting workflow.

        This is the main entry point that orchestrates all steps:
        1. Fetch and sync members from API
        2. Count new token distributions
        3. Update token pools
        4. Check threshold and send alerts
        5. Finalize count with timestamp update

        Returns:
            Summary dict with status and metrics:
                - execution_time: datetime
                - tokens_distributed: int
                - previous_total: int
                - current_total: int
                - threshold: int
                - alert_sent: bool
                - status: str ('success', 'partial', 'failed')
                - errors: List[str]
        """
        execution_time = datetime.now()
        errors = []
        tokens_distributed = 0
        alert_sent = False
        status = "success"

        logger.info("Starting daily token count workflow")

        try:
            # Step 1: Fetch and sync members
            try:
                new_registrations = self._fetch_and_sync_members()
                logger.info(f"Step 1 complete: {new_registrations} new registrations")
            except Exception as error:
                error_msg = f"Step 1 failed (fetch and sync): {error}"
                logger.error(error_msg)
                errors.append(error_msg)
                status = "partial"

            # Step 2: Count new distributions
            try:
                tokens_distributed = self._count_new_distributions()
                logger.info(
                    f"Step 2 complete: {tokens_distributed} tokens distributed since last count"
                )
            except Exception as error:
                error_msg = f"Step 2 failed (count distributions): {error}"
                logger.error(error_msg)
                errors.append(error_msg)
                status = "partial"

            # Get previous total before update
            try:
                previous_total = self.token_pool.get_total_available_tokens()
            except Exception as error:
                logger.warning(f"Could not get previous total: {error}")
                previous_total = 0

            # Step 3: Update token pools
            pool_update_success = False
            if tokens_distributed > 0:
                try:
                    pool_update_success = self._update_token_pools(tokens_distributed)
                    if pool_update_success:
                        logger.info(
                            f"Step 3 complete: Token pools updated (-{tokens_distributed})"
                        )
                    else:
                        error_msg = "Step 3 failed: Insufficient tokens in pools"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        status = "partial"
                except Exception as error:
                    error_msg = f"Step 3 failed (update pools): {error}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    status = "partial"
            else:
                logger.info("Step 3 skipped: No tokens distributed")
                pool_update_success = True  # Not a failure if nothing to update

            # Get current total after update
            try:
                current_total = self.token_pool.get_total_available_tokens()
            except Exception as error:
                logger.warning(f"Could not get current total: {error}")
                current_total = 0

            # Step 4: Check threshold and send alerts
            try:
                alert_sent = self._check_and_alert()
                if alert_sent:
                    logger.info("Step 4 complete: Threshold alert sent")
                else:
                    logger.info("Step 4 complete: No alert needed")
            except Exception as error:
                error_msg = f"Step 4 failed (check and alert): {error}"
                logger.error(error_msg)
                errors.append(error_msg)
                status = "partial"

            # Step 5: Finalize count
            try:
                self._finalize_count(tokens_distributed)
                logger.info("Step 5 complete: Count timestamp updated")
            except Exception as error:
                error_msg = f"Step 5 failed (finalize): {error}"
                logger.error(error_msg)
                errors.append(error_msg)
                status = "partial"

        except Exception as error:
            error_msg = f"Unexpected error in workflow: {error}"
            logger.error(error_msg)
            errors.append(error_msg)
            status = "failed"

        # Build summary
        summary = {
            "execution_time": execution_time,
            "tokens_distributed": tokens_distributed,
            "previous_total": previous_total,
            "current_total": current_total,
            "threshold": self.config["threshold"],
            "alert_sent": alert_sent,
            "status": status,
            "errors": errors,
        }

        # Log summary
        logger.info(
            f"Daily count workflow complete: status={status}, "
            f"tokens_distributed={tokens_distributed}, "
            f"current_total={current_total}, "
            f"alert_sent={alert_sent}"
        )

        if errors:
            logger.warning(f"Workflow completed with {len(errors)} error(s): {errors}")

        return summary

    def _fetch_and_sync_members(self) -> int:
        """Step 1: Fetch members from API and sync to registry.

        Returns:
            Number of new registrations

        Raises:
            RuntimeError: If API fetch fails
            ValueError: If registry operations fail
        """
        logger.info("Fetching members from Foreninglet API")
        new_registrations = self.member_sync.sync_to_registry()
        logger.info(f"Synced {new_registrations} new member token assignments")
        return new_registrations

    def _count_new_distributions(self) -> int:
        """Step 2: Count tokens distributed since last count.

        Returns:
            Number of tokens distributed since last count

        Raises:
            ValueError: If timestamp or registry operations fail
        """
        logger.info("Counting new token distributions")

        # Get last count timestamp
        last_count_time = self.timestamp_manager.get_last_count_timestamp()
        logger.info(f"Last count timestamp: {last_count_time}")

        # Get members registered since last count
        new_assignments = self.member_sync.get_new_assignments_since(last_count_time)

        distributed_count = len(new_assignments)
        logger.info(
            f"Found {distributed_count} new token assignments since {last_count_time}"
        )

        return distributed_count

    def _update_token_pools(self, distributed_count: int) -> bool:
        """Step 3: Update token pool inventory.

        Args:
            distributed_count: Number of tokens to distribute from pools

        Returns:
            True if successful, False if insufficient tokens

        Raises:
            ValueError: If pool operations fail
        """
        logger.info(f"Updating token pools: distributing {distributed_count} tokens")

        # Check total available tokens
        total_available = self.token_pool.get_total_available_tokens()
        logger.info(f"Total available tokens before distribution: {total_available}")

        if total_available < distributed_count:
            logger.error(
                f"Insufficient tokens: need {distributed_count}, have {total_available}"
            )
            return False

        # Distribute tokens (handles multi-pool logic and auto-switching)
        success = self.token_pool.distribute_tokens(distributed_count)

        if success:
            new_total = self.token_pool.get_total_available_tokens()
            logger.info(f"Token pools updated successfully: new total = {new_total}")
        else:
            logger.error("Failed to distribute tokens from pools")

        return success

    def _check_and_alert(self) -> bool:
        """Step 4: Check threshold and send alerts if needed.

        Returns:
            True if alert was sent, False otherwise

        Raises:
            ValueError: If alert operations fail
        """
        logger.info("Checking threshold and alert status")

        # Get current total across all pools
        current_total = self.token_pool.get_total_available_tokens()
        logger.info(
            f"Current total: {current_total}, Threshold: {self.config['threshold']}"
        )

        # Check if alert should be sent
        should_alert = self.alert_manager.check_threshold(current_total)

        if should_alert:
            logger.info("Threshold breached, sending alert")
            template_path = self.config["email"]["template"]
            alert_sent = self.alert_manager.send_threshold_alert(
                current_total, template_path
            )
            return alert_sent
        else:
            # Check if we should reset alert state (inventory replenished)
            if current_total >= self.config["threshold"]:
                alert_state = self.alert_manager.get_alert_state()
                if alert_state.get("is_active", False):
                    logger.info("Inventory replenished, resetting alert state")
                    self.alert_manager.reset_alert_state()

            logger.info("No alert needed")
            return False

    def _finalize_count(self, distributed_count: int) -> None:
        """Step 5: Update timestamp and log summary.

        Args:
            distributed_count: Number of tokens distributed in this count

        Raises:
            ValueError: If timestamp update fails
        """
        logger.info("Finalizing count operation")

        # Determine status based on whether we had any errors
        # (This is called after all steps, so we assume success if we got here)
        status = "success"

        # Update timestamp with execution details
        self.timestamp_manager.update_count_timestamp(
            tokens_distributed=distributed_count,
            status=status,
            metadata={
                "current_total": self.token_pool.get_total_available_tokens(),
                "threshold": self.config["threshold"],
            },
        )

        logger.info(
            f"Count finalized: {distributed_count} tokens distributed, "
            f"timestamp updated"
        )

    def __del__(self):
        """Clean up database connection."""
        if hasattr(self, "db") and self.db is not None:
            self.db.close()
