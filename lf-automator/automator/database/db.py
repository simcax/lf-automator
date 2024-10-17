"""Database module for the Automator"""

from psycopg2 import OperationalError, connect


class Database:
    """Database class for the Automator"""

    def __init__(self, host, port, database, user, password):
        self.connection = None
        self.cursor = None

        # Connection credentials
        self.connection_url = (
            f"host={host} port={port} dbname={database} user={user} password={password}"
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
