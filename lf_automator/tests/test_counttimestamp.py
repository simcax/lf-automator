"""Tests for CountTimestampManager component."""

from datetime import datetime

import pytest
from lf_automator.automator.counttimestamp import CountTimestampManager
from lf_automator.automator.database.db import Database
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@pytest.fixture
def db():
    """Create a database connection for testing."""
    database = Database()
    database.create_connection()
    yield database
    database.close()


@pytest.fixture
def timestamp_manager(db):
    """Create a CountTimestampManager instance for testing."""
    return CountTimestampManager(db, count_type="test_count")


def test_get_last_count_timestamp_default(timestamp_manager, db):
    """Test that get_last_count_timestamp returns epoch for first-time initialization."""
    # Clean up any existing test records
    with db.connection:
        with db.connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM lfautomator.countTimestamps WHERE countType = %s",
                ("test_count",),
            )

    timestamp = timestamp_manager.get_last_count_timestamp()
    assert timestamp == datetime(1970, 1, 1)


def test_update_count_timestamp_new(timestamp_manager, db):
    """Test updating count timestamp creates a new record."""
    # Clean up any existing test records
    with db.connection:
        with db.connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM lfautomator.countTimestamps WHERE countType = %s",
                ("test_count",),
            )

    # Update timestamp
    timestamp_manager.update_count_timestamp(
        tokens_distributed=5, status="success", metadata={"test": "data"}
    )

    # Verify record was created
    with db.connection:
        with db.connection.cursor() as cursor:
            cursor.execute(
                "SELECT tokensDistributed, executionStatus FROM lfautomator.countTimestamps WHERE countType = %s",
                ("test_count",),
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == 5
            assert row[1] == "success"


def test_update_count_timestamp_existing(timestamp_manager, db):
    """Test updating count timestamp updates an existing record."""
    # Clean up and create initial record
    with db.connection:
        with db.connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM lfautomator.countTimestamps WHERE countType = %s",
                ("test_count",),
            )
            cursor.execute(
                """INSERT INTO lfautomator.countTimestamps 
                   (countType, lastCountAt, executionStatus, tokensDistributed) 
                   VALUES (%s, NOW(), %s, %s)""",
                ("test_count", "success", 3),
            )

    # Update timestamp
    timestamp_manager.update_count_timestamp(
        tokens_distributed=7, status="partial", metadata={"updated": "true"}
    )

    # Verify record was updated (not duplicated)
    with db.connection:
        with db.connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*), tokensDistributed, executionStatus FROM lfautomator.countTimestamps WHERE countType = %s GROUP BY tokensDistributed, executionStatus",
                ("test_count",),
            )
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == 1  # Only one record
            assert row[1] == 7
            assert row[2] == "partial"


def test_get_count_history(timestamp_manager, db):
    """Test retrieving count history."""
    # Clean up and create test record
    with db.connection:
        with db.connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM lfautomator.countTimestamps WHERE countType = %s",
                ("test_count",),
            )

    # Create a count record
    timestamp_manager.update_count_timestamp(
        tokens_distributed=10, status="success", metadata={"note": "test history"}
    )

    # Get history
    history = timestamp_manager.get_count_history(limit=5)

    assert len(history) >= 1
    # Find our test record
    test_record = next((h for h in history if h["count_type"] == "test_count"), None)
    assert test_record is not None
    assert test_record["tokens_distributed"] == 10
    assert test_record["execution_status"] == "success"
    assert test_record["metadata"]["note"] == "test history"


def test_get_last_count_timestamp_after_update(timestamp_manager, db):
    """Test that get_last_count_timestamp returns the updated timestamp."""
    # Clean up
    with db.connection:
        with db.connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM lfautomator.countTimestamps WHERE countType = %s",
                ("test_count",),
            )

    # Update timestamp
    timestamp_manager.update_count_timestamp(tokens_distributed=3, status="success")

    # Get timestamp
    timestamp = timestamp_manager.get_last_count_timestamp()

    # Should be recent (within last 2 hours to account for timezone differences)
    now = datetime.now()
    time_diff = abs((now - timestamp).total_seconds())
    assert time_diff < 7200  # Less than 2 hours
