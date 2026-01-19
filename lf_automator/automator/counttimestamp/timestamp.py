"""CountTimestampManager component for tracking token count execution times."""

import json
from datetime import datetime
from typing import Dict, List, Optional

from automator.database.db import Database


class CountTimestampManager:
    """Tracks the last token count execution time and history."""

    def __init__(
        self, db: Optional[Database] = None, count_type: str = "daily_token_count"
    ):
        """Initialize with database connection.

        Args:
            db: Database instance. If None, creates a new connection.
            count_type: Type identifier for the count operation (default: "daily_token_count")
        """
        if db is None:
            self.db = Database()
            self.db.create_connection()
            self._owns_connection = True
        else:
            self.db = db
            self._owns_connection = False

        self.count_type = count_type

    def __del__(self):
        """Clean up database connection if we own it."""
        if self._owns_connection and self.db is not None:
            self.db.close()

    def get_last_count_timestamp(self) -> datetime:
        """Get timestamp of last successful count.

        Returns a default timestamp (epoch) if no previous count exists.

        Returns:
            Datetime of last count, or epoch (1970-01-01) if no previous count

        Raises:
            ValueError: If database operation fails
        """
        try:
            with self.db.connection:
                with self.db.connection.cursor() as cursor:
                    cursor.execute(
                        """SELECT lastCountAt FROM lfautomator.countTimestamps 
                           WHERE countType = %s""",
                        (self.count_type,),
                    )
                    row = cursor.fetchone()

                    if row:
                        return row[0]
                    else:
                        # Return epoch as default for first-time initialization
                        return datetime(1970, 1, 1)
        except Exception as error:
            raise ValueError(f"Error getting last count timestamp: {error}")

    def update_count_timestamp(
        self, tokens_distributed: int, status: str, metadata: Optional[Dict] = None
    ) -> None:
        """Update timestamp after count execution.

        Uses upsert logic to either insert a new record or update an existing one.

        Args:
            tokens_distributed: Number of tokens distributed in this count
            status: Execution status (e.g., 'success', 'partial', 'failed')
            metadata: Optional additional metadata as a dictionary

        Raises:
            ValueError: If database operation fails
        """
        try:
            # Convert metadata dict to JSON string if provided
            metadata_json = json.dumps(metadata) if metadata is not None else None

            with self.db.connection:
                with self.db.connection.cursor() as cursor:
                    # Check if record exists
                    cursor.execute(
                        "SELECT timestampUuid FROM lfautomator.countTimestamps WHERE countType = %s",
                        (self.count_type,),
                    )
                    existing = cursor.fetchone()

                    if existing:
                        # Update existing record
                        cursor.execute(
                            """UPDATE lfautomator.countTimestamps 
                               SET lastCountAt = NOW(), 
                                   executionStatus = %s, 
                                   tokensDistributed = %s,
                                   metadata = %s
                               WHERE countType = %s""",
                            (
                                status,
                                tokens_distributed,
                                metadata_json,
                                self.count_type,
                            ),
                        )
                    else:
                        # Insert new record
                        cursor.execute(
                            """INSERT INTO lfautomator.countTimestamps 
                               (countType, lastCountAt, executionStatus, tokensDistributed, metadata) 
                               VALUES (%s, NOW(), %s, %s, %s)""",
                            (
                                self.count_type,
                                status,
                                tokens_distributed,
                                metadata_json,
                            ),
                        )
        except Exception as error:
            raise ValueError(f"Error updating count timestamp: {error}")

    def get_count_history(self, limit: int = 10) -> List[Dict]:
        """Get recent count execution history.

        Note: Since the table stores only the latest count per countType,
        this returns a single record. In a production system, you might want
        a separate history table for full audit trail.

        Args:
            limit: Maximum number of records to return (default: 10)

        Returns:
            List of dicts with timestamp_uuid, count_type, last_count_at,
            execution_status, tokens_distributed, metadata

        Raises:
            ValueError: If database operation fails
        """
        try:
            with self.db.connection:
                with self.db.connection.cursor() as cursor:
                    cursor.execute(
                        """SELECT timestampUuid, countType, lastCountAt, 
                                  executionStatus, tokensDistributed, metadata 
                           FROM lfautomator.countTimestamps 
                           ORDER BY lastCountAt DESC 
                           LIMIT %s""",
                        (limit,),
                    )
                    rows = cursor.fetchall()

                    return [
                        {
                            "timestamp_uuid": str(row[0]),
                            "count_type": row[1],
                            "last_count_at": row[2],
                            "execution_status": row[3],
                            "tokens_distributed": row[4],
                            "metadata": row[5],
                        }
                        for row in rows
                    ]
        except Exception as error:
            raise ValueError(f"Error getting count history: {error}")
