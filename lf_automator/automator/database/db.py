"""Database module for the Automator"""

import os

from psycopg2 import InterfaceError, OperationalError, connect


class Database:
    """Database class for the Automator"""

    def __init__(self):
        self.connection = None
        self.cursor = None
        self.creds = self.db_credentials_from_env()

        # Connection credentials
        self.connection_url = (
            f"host={self.creds.get('host')} port={self.creds.get('port')} "
            f"dbname={self.creds.get('database')} user={self.creds.get('user')} "
            f"password={self.creds.get('password')}"
        )

    def create_connection(self):
        """Connect to the database"""
        try:
            self.connection = connect(dsn=self.connection_url)
            self.cursor = self.connection.cursor()
        except OperationalError as error:
            print(f"Error connecting to the database: {error}")
            self.connection = None
            self.cursor = None

    def ensure_connection(self):
        """Ensure database connection is alive, reconnect if necessary.

        This method checks if the connection is still valid and reconnects
        if it has been closed or is in an invalid state.
        """
        try:
            # Check if connection exists and is not closed
            if self.connection is None or self.connection.closed:
                print("Database connection is closed, reconnecting...")
                self.create_connection()
                return

            # Check if cursor exists and is not closed
            if self.cursor is None or self.cursor.closed:
                print("Database cursor is closed, recreating...")
                self.cursor = self.connection.cursor()
                return

            # Test the connection with a simple query
            self.cursor.execute("SELECT 1")
            self.cursor.fetchone()
        except (OperationalError, InterfaceError) as error:
            print(f"Database connection test failed, reconnecting: {error}")
            # Close any existing connection
            try:
                if self.cursor is not None and not self.cursor.closed:
                    self.cursor.close()
                if self.connection is not None and not self.connection.closed:
                    self.connection.close()
            except Exception:
                pass  # Ignore errors during cleanup

            # Reconnect
            self.create_connection()

    def close(self):
        """Close the database connection"""
        if self.connection is not None:
            self.cursor.close()
            self.connection.close()
            self.connection = None
            self.cursor = None

    def execute(self, query):
        """Execute a query"""
        if self.cursor is not None:
            self.cursor.execute(query)
            return self.cursor.fetchall()
        return None

    def db_credentials_from_env(self):
        """Fixture to get the database credentials from the environment."""
        creds = {
            "host": os.environ.get("POSTGRESQL_ADDON_HOST"),
            "port": os.environ.get("POSTGRESQL_ADDON_PORT"),
            "database": os.environ.get("POSTGRESQL_ADDON_DB"),
            "user": os.environ.get("POSTGRESQL_ADDON_USER"),
            "password": os.environ.get("POSTGRESQL_ADDON_PASSWORD"),
            "connection_url": os.environ.get("POSTGRESQL_ADDON_URI"),
        }
        return creds

    def db_connection(self):
        db_credentials = self.db_credentials()
        db = Database(
            host=db_credentials.get("host"),
            port=db_credentials.get("port"),
            database=db_credentials.get("database"),
            user=db_credentials.get("user"),
            password=db_credentials.get("password"),
        )
        db.create_connection()
        return db
