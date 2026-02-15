"""AlertManager class for token inventory threshold monitoring and email alerts."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict

from ..database.db import Database
from ..mailer.send import Mailer

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages threshold monitoring and email notifications for token inventory."""

    def __init__(self, db: Database, mailer: Mailer, threshold: int):
        """Initialize AlertManager with database, mailer, and threshold value.

        Args:
            db: Database instance for alert state persistence
            mailer: Mailer instance for sending email alerts
            threshold: Minimum token count that triggers alerts
        """
        self.db = db
        self.mailer = mailer
        self.threshold = threshold
        self._ensure_alert_table()

    def _ensure_alert_table(self):
        """Ensure the alertState table exists."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS lfautomator.alertState (
            alertUuid UUID NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
            alertType VARCHAR(50) NOT NULL,
            lastTriggered TIMESTAMP,
            isActive BOOLEAN DEFAULT FALSE,
            metadata JSONB
        );
        """
        try:
            # Ensure connection is alive before executing queries
            self.db.ensure_connection()

            with self.db.connection:
                with self.db.connection.cursor() as cursor:
                    cursor.execute(create_table_query)
            logger.debug("Alert state table ensured")
        except Exception as e:
            logger.error(f"Error creating alertState table: {e}")
            try:
                if self.db.connection and not self.db.connection.closed:
                    self.db.connection.rollback()
            except Exception:
                pass  # Ignore errors during rollback

    def check_threshold(self, current_count: int) -> bool:
        """Check if current count is below threshold and alert should be sent.

        Args:
            current_count: Current total token count across all pools

        Returns:
            True if alert should be sent, False otherwise
        """
        if current_count >= self.threshold:
            return False

        # Check if alert is already active
        alert_state = self.get_alert_state()

        # Send alert only if not already active
        return not alert_state.get("is_active", False)

    def send_threshold_alert(self, current_count: int, template_path: str) -> bool:
        """Send threshold alert email using template.

        Args:
            current_count: Current total token count
            template_path: Path to email template file

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Load and render template
            template_file = Path(template_path)
            if not template_file.exists():
                logger.error(f"Template file not found: {template_path}")
                # Use fallback plain text format
                email_content = self._generate_fallback_email(current_count)
            else:
                with open(template_file, "r") as f:
                    template_content = f.read()
                email_content = template_content.format(
                    current_count=current_count, threshold=self.threshold
                )

            # Send email
            self.mailer.send_email(email_content, self.mailer.sender)

            # Update alert state to active
            self._update_alert_state(is_active=True)

            logger.info(
                f"Threshold alert sent: current_count={current_count}, threshold={self.threshold}"
            )
            return True

        except Exception as e:
            logger.error(f"Error sending threshold alert: {e}")
            return False

    def _generate_fallback_email(self, current_count: int) -> str:
        """Generate fallback plain text email content.

        Args:
            current_count: Current total token count

        Returns:
            Plain text email content
        """
        return f"""
        <h2>Token Inventory Alert</h2>
        <p>The token inventory has fallen below the threshold.</p>
        <p><strong>Current Token Count:</strong> {current_count}</p>
        <p><strong>Threshold:</strong> {self.threshold}</p>
        <p>Please order more tokens to maintain adequate inventory.</p>
        """

    def reset_alert_state(self) -> None:
        """Reset alert state when inventory is replenished above threshold."""
        try:
            self._update_alert_state(is_active=False)
            logger.info("Alert state reset after inventory replenishment")
        except Exception as e:
            logger.error(f"Error resetting alert state: {e}")

    def get_alert_state(self) -> Dict:
        """Get current alert state.

        Returns:
            Dictionary with alert state information:
            - alert_type: Type of alert (e.g., 'token_threshold')
            - last_triggered: Timestamp of last alert
            - is_active: Whether alert is currently active
            - metadata: Additional alert metadata
        """
        query = """
        SELECT alertType, lastTriggered, isActive, metadata
        FROM lfautomator.alertState
        WHERE alertType = 'token_threshold'
        LIMIT 1;
        """

        try:
            # Ensure connection is alive before executing queries
            self.db.ensure_connection()

            with self.db.connection:
                with self.db.connection.cursor() as cursor:
                    cursor.execute(query)
                    row = cursor.fetchone()

            if row:
                return {
                    "alert_type": row[0],
                    "last_triggered": row[1],
                    "is_active": row[2],
                    "metadata": row[3] or {},
                }
            else:
                # No alert state exists yet
                return {
                    "alert_type": "token_threshold",
                    "last_triggered": None,
                    "is_active": False,
                    "metadata": {},
                }

        except Exception as e:
            logger.error(f"Error getting alert state: {e}")
            return {
                "alert_type": "token_threshold",
                "last_triggered": None,
                "is_active": False,
                "metadata": {},
            }

    def _update_alert_state(self, is_active: bool) -> None:
        """Update alert state in database.

        Args:
            is_active: Whether alert should be marked as active
        """
        # Check if alert state exists
        check_query = """
        SELECT alertUuid FROM lfautomator.alertState
        WHERE alertType = 'token_threshold'
        LIMIT 1;
        """

        try:
            # Ensure connection is alive before executing queries
            self.db.ensure_connection()

            with self.db.connection:
                with self.db.connection.cursor() as cursor:
                    cursor.execute(check_query)
                    result = cursor.fetchone()

                    if result:
                        # Update existing record
                        update_query = """
                        UPDATE lfautomator.alertState
                        SET isActive = %s, lastTriggered = %s
                        WHERE alertType = 'token_threshold';
                        """
                        cursor.execute(update_query, (is_active, datetime.now()))
                    else:
                        # Insert new record
                        insert_query = """
                        INSERT INTO lfautomator.alertState (alertType, isActive, lastTriggered)
                        VALUES ('token_threshold', %s, %s);
                        """
                        cursor.execute(insert_query, (is_active, datetime.now()))

        except Exception as e:
            logger.error(f"Error updating alert state: {e}")
            try:
                if self.db.connection and not self.db.connection.closed:
                    self.db.connection.rollback()
            except Exception:
                pass  # Ignore errors during rollback
            raise
