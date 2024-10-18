"""Implements the concept of having a pool of tokens that can be used, and counted down.
The idea is to have a pool of tokens that is decreased every time a new token is given to a member,
and when the pool is empty the pool can be refilled by adding tokens to it.
"""

from automator.database.db import Database


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

    def create_tokenpool(self, token_count):
        """Create a token pool in the database"""
        pool_uuid = None
        try:
            assert token_count > 0
            self.token_count = token_count
            self.current_token_count = token_count
            with self.db.connection:
                with self.db.connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO lfautomator.accessTokenPools (startcount, currentcount) VALUES (%s, %s) RETURNING pooluuid",
                        (self.token_count, self.current_token_count),
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
        except Exception as error:
            raise (ValueError(f"Error removing tokens from token pool: {error}"))
        self.current_token_count -= token_count
        return self.current_token_count
