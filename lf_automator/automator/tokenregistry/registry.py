"""TokenRegistry component for managing member token assignments."""

from datetime import datetime
from typing import Dict, List, Optional

from lf_automator.automator.database.db import Database


class TokenRegistry:
    """Manages the persistent record of member token assignments."""

    def __init__(self, db: Optional[Database] = None):
        """Initialize with database connection.

        Args:
            db: Database instance. If None, creates a new connection.
        """
        if db is None:
            self.db = Database()
            self.db.create_connection()
            self._owns_connection = True
        else:
            self.db = db
            self._owns_connection = False

    def __del__(self):
        """Clean up database connection if we own it."""
        if self._owns_connection and self.db is not None:
            self.db.close()

    def register_member_token(self, member_uuid: str, token_number: str) -> bool:
        """Register or update a member's token assignment.

        Uses upsert logic to either insert a new record or update an existing one.

        Args:
            member_uuid: UUID of the member
            token_number: Token number assigned to the member

        Returns:
            True if new registration, False if update

        Raises:
            ValueError: If database operation fails
        """
        from loguru import logger

        try:
            with self.db.connection:
                with self.db.connection.cursor() as cursor:
                    # Check if member already exists
                    cursor.execute(
                        "SELECT registryUuid FROM lfautomator.memberTokenRegistry WHERE memberUuid = %s",
                        (member_uuid,),
                    )
                    existing = cursor.fetchone()

                    if existing:
                        # Update existing record
                        cursor.execute(
                            """UPDATE lfautomator.memberTokenRegistry 
                               SET tokenNumber = %s, updatedAt = NOW() 
                               WHERE memberUuid = %s""",
                            (token_number, member_uuid),
                        )
                        logger.debug(
                            f"  → Updated registry: {member_uuid} = token {token_number}"
                        )
                        return False
                    else:
                        # Insert new record
                        cursor.execute(
                            """INSERT INTO lfautomator.memberTokenRegistry 
                               (memberUuid, tokenNumber, registeredAt, updatedAt) 
                               VALUES (%s, %s, NOW(), NOW())""",
                            (member_uuid, token_number),
                        )
                        logger.debug(
                            f"  → Inserted into registry: {member_uuid} = token {token_number}"
                        )
                        return True
        except Exception as error:
            raise ValueError(f"Error registering member token: {error}")

    def get_members_registered_since(self, timestamp: datetime) -> List[Dict]:
        """Get all members who received tokens after the given timestamp.

        Args:
            timestamp: Datetime to filter by

        Returns:
            List of dicts with member_uuid, token_number, registered_at, updated_at

        Raises:
            ValueError: If database operation fails
        """
        try:
            with self.db.connection:
                with self.db.connection.cursor() as cursor:
                    cursor.execute(
                        """SELECT memberUuid, tokenNumber, registeredAt, updatedAt 
                           FROM lfautomator.memberTokenRegistry 
                           WHERE registeredAt > %s 
                           ORDER BY registeredAt ASC""",
                        (timestamp,),
                    )
                    rows = cursor.fetchall()

                    return [
                        {
                            "member_uuid": str(row[0]),
                            "token_number": row[1],
                            "registered_at": row[2],
                            "updated_at": row[3],
                        }
                        for row in rows
                    ]
        except Exception as error:
            raise ValueError(
                f"Error getting members registered since timestamp: {error}"
            )

    def get_all_registered_members(self) -> List[Dict]:
        """Get all members in the registry.

        Returns:
            List of dicts with member_uuid, token_number, registered_at, updated_at

        Raises:
            ValueError: If database operation fails
        """
        try:
            with self.db.connection:
                with self.db.connection.cursor() as cursor:
                    cursor.execute(
                        """SELECT memberUuid, tokenNumber, registeredAt, updatedAt 
                           FROM lfautomator.memberTokenRegistry 
                           ORDER BY registeredAt ASC"""
                    )
                    rows = cursor.fetchall()

                    return [
                        {
                            "member_uuid": str(row[0]),
                            "token_number": row[1],
                            "registered_at": row[2],
                            "updated_at": row[3],
                        }
                        for row in rows
                    ]
        except Exception as error:
            raise ValueError(f"Error getting all registered members: {error}")

    def member_exists(self, member_uuid: str) -> bool:
        """Check if a member is already in the registry.

        Args:
            member_uuid: UUID of the member to check

        Returns:
            True if member exists, False otherwise

        Raises:
            ValueError: If database operation fails
        """
        try:
            with self.db.connection:
                with self.db.connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT COUNT(*) FROM lfautomator.memberTokenRegistry WHERE memberUuid = %s",
                        (member_uuid,),
                    )
                    count = cursor.fetchone()[0]
                    return count > 0
        except Exception as error:
            raise ValueError(f"Error checking if member exists: {error}")
