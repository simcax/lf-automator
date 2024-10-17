"""Database module for the Automator"""

import os

from psycopg2 import OperationalError, connect


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
            "host": os.environ.get("DB_HOST"),
            "port": os.environ.get("DB_PORT"),
            "database": os.environ.get("DB_NAME"),
            "user": os.environ.get("DB_USERNAME"),
            "password": os.environ.get("DB_PASSWORD"),
            "connection_url": os.environ.get("DB_CONN"),
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
