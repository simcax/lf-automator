"""Tests for the database functionality"""

from pathlib import Path


def test_database_connection(db_connection):
    """Test the database connection."""

    assert db_connection.connection is not None
    assert db_connection.cursor is not None
    db_connection.close()
    assert db_connection.connection is None
    assert db_connection.cursor is None


def test_database_tables_exist(db_connection):
    """Test that the database tables exists and are loaded from the migration script."""
    # First load the migration file
    # parent_parent_dir = Path(__file__).parent.parent
    migration_file = (
        Path(__file__).parent.parent
        / "db-automator/migrations/V001_20241013143045__carstenskov.sql"
    )
    with open(migration_file, "r") as file:
        migration_script = file.read()
    # Now find a table name in the migration script
    table_name = None
    for line in migration_script.split("\n"):
        if "CREATE TABLE" in line:
            table_name = (
                line.split("EXISTS")[1].strip().split(" ")[0].lower().split(".")[1]
            )
            break
    assert table_name is not None
    # Now test that the table exists in the database

    db = db_connection

    with db.cursor as cursor:
        cursor.execute(
            "SELECT * \
                        FROM pg_catalog.pg_tables \
                        WHERE schemaname != 'pg_catalog' AND \
                        schemaname != 'information_schema';"
        )
        rows = cursor.fetchall()
        table_names = [row[1] for row in rows]
        assert table_name in table_names
        assert cursor.fetchall() is not None
    db.close()
