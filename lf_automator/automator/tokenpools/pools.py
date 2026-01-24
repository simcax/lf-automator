"""Implements the concept of having a pool of tokens that can be used, and counted down.
The idea is to have a pool of tokens that is decreased every time a new token is given to a member,
and when the pool is empty the pool can be refilled by adding tokens to it.

Enhanced with multi-pool support for automatic pool switching and priority management.
"""

from typing import Dict, List, Optional

from lf_automator.automator.database.db import Database


class TokenPool:
    """Implements the concept of having a pool of tokens that can be used, and counted down."""

    def __init__(self, pool_uuid=None):
        """Initialize the class."""
        self.token_count = 0
        self.current_token_count = 0
        self.db = None
        self.register_db_connection()
        if pool_uuid:
            self.pool_uuid = pool_uuid
            self.token_count = self.get_tokenpool(pool_uuid)
            self.current_token_count = self.token_count

    def register_db_connection(self):
        """Connect to the database."""
        self.db = Database()
        self.db.create_connection()

    def create_tokenpool(self, token_count, pool_status="active", pool_priority=None):
        """Create a token pool in the database with status and priority"""
        pool_uuid = None
        try:
            assert token_count > 0
            self.token_count = token_count
            self.current_token_count = token_count

            # If priority not specified, use timestamp-based priority (older = higher priority)
            if pool_priority is None:
                pool_priority = self._get_next_priority()

            with self.db.connection:
                with self.db.connection.cursor() as cursor:
                    cursor.execute(
                        """INSERT INTO lfautomator.accessTokenPools 
                           (startcount, currentcount, poolStatus, poolPriority) 
                           VALUES (%s, %s, %s, %s) RETURNING pooluuid""",
                        (
                            self.token_count,
                            self.current_token_count,
                            pool_status,
                            pool_priority,
                        ),
                    )
                    pool_uuid = cursor.fetchone()[0]
        except AssertionError:
            raise (ValueError("Token count must be greater than 0"))
        except Exception as error:
            raise (ValueError(f"Error creating token pool: {error}"))
        self.pool_uuid = pool_uuid
        return pool_uuid

    def get_tokenpool(self, pool_uuid):
        """Get the token count for the pool."""
        token_count = None
        try:
            with self.db.connection:
                with self.db.connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT currentcount FROM lfautomator.accessTokenPools WHERE pooluuid = %s",
                        (pool_uuid,),
                    )
                    token_count = cursor.fetchone()[0]
        except Exception as error:
            raise (ValueError(f"Error getting token pool: {error}"))
        return token_count

    def add_tokens_to_tokenpool(self, token_count):
        """Add tokens to the token pool."""
        try:
            with self.db.connection:
                with self.db.connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE lfautomator.accessTokenPools SET currentcount = currentcount + %s WHERE pooluuid = %s",
                        (token_count, self.pool_uuid),
                    )
                    # Record history entry
                    cursor.execute(
                        """INSERT INTO lfautomator.accessTokenPoolsHistory 
                           (poolUuid, accessTokenCount) 
                           VALUES (%s, %s)""",
                        (self.pool_uuid, token_count),
                    )
        except Exception as error:
            raise (ValueError(f"Error adding tokens to token pool: {error}"))
        self.current_token_count += token_count
        return self.current_token_count

    def remove_tokens_from_tokenpool(self, token_count):
        """Remove tokens from the token pool."""
        # Make sure we have enough tokens to remove
        if self.current_token_count - token_count < 0:
            raise (ValueError("Not enough tokens in the pool"))
        try:
            with self.db.connection:
                with self.db.connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE lfautomator.accessTokenPools SET currentcount = currentcount - %s WHERE pooluuid = %s",
                        (token_count, self.pool_uuid),
                    )
                    # Record the transaction in history (negative for withdrawal)
                    cursor.execute(
                        """INSERT INTO lfautomator.accessTokenPoolsHistory 
                           (poolUuid, accessTokenCount) 
                           VALUES (%s, %s)""",
                        (self.pool_uuid, -token_count),
                    )
        except Exception as error:
            raise (ValueError(f"Error removing tokens from token pool: {error}"))
        self.current_token_count -= token_count
        return self.current_token_count

    def _get_next_priority(self) -> int:
        """Get the next priority value for a new pool (max + 1)"""
        try:
            with self.db.connection:
                with self.db.connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT COALESCE(MAX(poolPriority), -1) + 1 FROM lfautomator.accessTokenPools"
                    )
                    return cursor.fetchone()[0]
        except Exception as error:
            raise ValueError(f"Error getting next priority: {error}")

    def get_primary_pool(self, cursor=None) -> Optional[Dict]:
        """Get the current primary pool (active pool with lowest priority/oldest).

        Args:
            cursor: Optional cursor to use (for nested transactions)

        Returns:
            Dict with pool info or None if no active pools with tokens exist
        """
        try:
            if cursor:
                # Use provided cursor (already in a transaction)
                cursor.execute(
                    """SELECT pooluuid, pooldate, startcount, currentcount, poolStatus, poolPriority
                       FROM lfautomator.accessTokenPools 
                       WHERE poolStatus = 'active' AND currentcount > 0
                       ORDER BY poolPriority ASC
                       LIMIT 1"""
                )
                row = cursor.fetchone()
            else:
                # Create own connection context
                with self.db.connection:
                    with self.db.connection.cursor() as cur:
                        cur.execute(
                            """SELECT pooluuid, pooldate, startcount, currentcount, poolStatus, poolPriority
                               FROM lfautomator.accessTokenPools 
                               WHERE poolStatus = 'active' AND currentcount > 0
                               ORDER BY poolPriority ASC
                               LIMIT 1"""
                        )
                        row = cur.fetchone()

            if row:
                return {
                    "pool_uuid": row[0],
                    "pool_date": row[1],
                    "start_count": row[2],
                    "current_count": row[3],
                    "pool_status": row[4],
                    "pool_priority": row[5],
                }
            return None
        except Exception as error:
            raise ValueError(f"Error getting primary pool: {error}")

    def get_all_active_pools(self) -> List[Dict]:
        """Get all active pools ordered by priority.

        Returns:
            List of dicts with pool info
        """
        try:
            with self.db.connection:
                with self.db.connection.cursor() as cursor:
                    cursor.execute(
                        """SELECT pooluuid, pooldate, startcount, currentcount, poolStatus, poolPriority
                           FROM lfautomator.accessTokenPools 
                           WHERE poolStatus = 'active'
                           ORDER BY poolPriority ASC"""
                    )
                    rows = cursor.fetchall()
                    return [
                        {
                            "pool_uuid": row[0],
                            "pool_date": row[1],
                            "start_count": row[2],
                            "current_count": row[3],
                            "pool_status": row[4],
                            "pool_priority": row[5],
                        }
                        for row in rows
                    ]
        except Exception as error:
            raise ValueError(f"Error getting active pools: {error}")

    def get_total_available_tokens(self) -> int:
        """Sum of tokens across all active pools.

        Returns:
            Total count of available tokens
        """
        try:
            with self.db.connection:
                with self.db.connection.cursor() as cursor:
                    cursor.execute(
                        """SELECT COALESCE(SUM(currentcount), 0) 
                           FROM lfautomator.accessTokenPools 
                           WHERE poolStatus = 'active'"""
                    )
                    return cursor.fetchone()[0]
        except Exception as error:
            raise ValueError(f"Error getting total available tokens: {error}")

    def distribute_tokens(self, count: int) -> bool:
        """Distribute tokens from primary pool with auto-switching logic.

        Args:
            count: Number of tokens to distribute

        Returns:
            True if successful, False if insufficient tokens
        """
        if count <= 0:
            raise ValueError("Distribution count must be positive")

        total_available = self.get_total_available_tokens()
        if total_available < count:
            return False

        remaining_to_distribute = count

        try:
            with self.db.connection:
                with self.db.connection.cursor() as cursor:
                    while remaining_to_distribute > 0:
                        # Pass cursor to avoid nested connection context
                        primary_pool = self.get_primary_pool(cursor=cursor)
                        if not primary_pool:
                            self.db.connection.rollback()
                            return False

                        pool_uuid = primary_pool["pool_uuid"]
                        available_in_pool = primary_pool["current_count"]

                        # Distribute from this pool
                        tokens_from_this_pool = min(
                            remaining_to_distribute, available_in_pool
                        )

                        cursor.execute(
                            """UPDATE lfautomator.accessTokenPools 
                               SET currentcount = currentcount - %s 
                               WHERE pooluuid = %s""",
                            (tokens_from_this_pool, pool_uuid),
                        )

                        # Record the distribution in history (negative for withdrawal)
                        cursor.execute(
                            """INSERT INTO lfautomator.accessTokenPoolsHistory 
                               (poolUuid, accessTokenCount) 
                               VALUES (%s, %s)""",
                            (pool_uuid, -tokens_from_this_pool),
                        )

                        remaining_to_distribute -= tokens_from_this_pool

                        # If pool is now empty, mark it as depleted
                        if tokens_from_this_pool == available_in_pool:
                            cursor.execute(
                                """UPDATE lfautomator.accessTokenPools 
                                   SET poolStatus = 'depleted' 
                                   WHERE pooluuid = %s""",
                                (pool_uuid,),
                            )

                return True
        except Exception as error:
            self.db.connection.rollback()
            raise ValueError(f"Error distributing tokens: {error}")
        except Exception as error:
            raise ValueError(f"Error distributing tokens: {error}")

    def switch_primary_pool(self) -> Optional[Dict]:
        """Switch to next available pool when primary is empty.

        This method marks the current primary pool as depleted and returns
        the next available active pool with tokens.

        Returns:
            New primary pool info or None if no pools available
        """
        try:
            # Get current primary pool
            current_primary = self.get_primary_pool()

            if current_primary and current_primary["current_count"] == 0:
                # Mark as depleted
                with self.db.connection:
                    with self.db.connection.cursor() as cursor:
                        cursor.execute(
                            """UPDATE lfautomator.accessTokenPools 
                               SET poolStatus = 'depleted' 
                               WHERE pooluuid = %s""",
                            (current_primary["pool_uuid"],),
                        )

            # Return the new primary pool (next in priority order)
            return self.get_primary_pool()
        except Exception as error:
            raise ValueError(f"Error switching primary pool: {error}")
