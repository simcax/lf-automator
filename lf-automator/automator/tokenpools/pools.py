"""Implements the concept of having a pool of tokens that can be used, and counted down.
The idea is to have a pool of tokens that is decreased every time a new token is given to a member,
and when the pool is empty the pool can be refilled by adding tokens to it.
"""

from automator.database.db import Database


class TokenPool:
    """Implements the concept of having a pool of tokens that can be used, and counted down."""

    def __init__(self):
        """Initialize the class."""
        self.token_count = 0
        self.current_token_count = 0
        self.db = None
        self.register_db_connection()

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
