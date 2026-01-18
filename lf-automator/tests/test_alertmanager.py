"""Tests for AlertManager component."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from automator.alertmanager import AlertManager
from automator.database.db import Database
from automator.mailer.send import Mailer
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
def mailer():
    """Create a mock Mailer instance for testing."""
    mock_mailer = MagicMock(spec=Mailer)
    mock_mailer.sender = "test@example.com"
    mock_mailer.send_email = MagicMock(return_value=0)
    return mock_mailer


@pytest.fixture
def alert_manager(db, mailer):
    """Create an AlertManager instance for testing."""
    return AlertManager(db, mailer, threshold=10)


@pytest.fixture
def cleanup_alert_state(db):
    """Clean up alert state before and after tests."""
    with db.connection:
        with db.connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM lfautomator.alertState WHERE alertType = 'token_threshold'"
            )
    yield
    with db.connection:
        with db.connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM lfautomator.alertState WHERE alertType = 'token_threshold'"
            )


def test_check_threshold_above_threshold(alert_manager, cleanup_alert_state):
    """Test that check_threshold returns False when count is above threshold."""
    result = alert_manager.check_threshold(current_count=15)
    assert result is False


def test_check_threshold_below_threshold_not_active(alert_manager, cleanup_alert_state):
    """Test that check_threshold returns True when count is below threshold and alert not active."""
    result = alert_manager.check_threshold(current_count=5)
    assert result is True


def test_check_threshold_below_threshold_already_active(
    alert_manager, cleanup_alert_state
):
    """Test that check_threshold returns False when alert is already active."""
    # Set alert state to active
    alert_manager._update_alert_state(is_active=True)

    result = alert_manager.check_threshold(current_count=5)
    assert result is False


def test_send_threshold_alert_with_template(alert_manager, mailer, cleanup_alert_state):
    """Test sending threshold alert with template file."""
    template_path = "templates/threshold_alert.html"

    # Ensure template exists
    template_file = Path(template_path)
    assert template_file.exists(), f"Template file not found: {template_path}"

    result = alert_manager.send_threshold_alert(
        current_count=5, template_path=template_path
    )

    assert result is True
    assert mailer.send_email.called

    # Verify alert state is now active
    alert_state = alert_manager.get_alert_state()
    assert alert_state["is_active"] is True


def test_send_threshold_alert_missing_template(
    alert_manager, mailer, cleanup_alert_state
):
    """Test sending threshold alert with missing template uses fallback."""
    template_path = "templates/nonexistent_template.html"

    result = alert_manager.send_threshold_alert(
        current_count=5, template_path=template_path
    )

    assert result is True
    assert mailer.send_email.called

    # Verify fallback content was used
    call_args = mailer.send_email.call_args
    email_content = call_args[0][0]
    assert "Token Inventory Alert" in email_content
    assert "5" in email_content  # Current count
    assert "10" in email_content  # Threshold


def test_reset_alert_state(alert_manager, cleanup_alert_state):
    """Test resetting alert state after inventory replenishment."""
    # Set alert state to active
    alert_manager._update_alert_state(is_active=True)

    # Verify it's active
    alert_state = alert_manager.get_alert_state()
    assert alert_state["is_active"] is True

    # Reset alert state
    alert_manager.reset_alert_state()

    # Verify it's now inactive
    alert_state = alert_manager.get_alert_state()
    assert alert_state["is_active"] is False


def test_get_alert_state_no_record(alert_manager, cleanup_alert_state):
    """Test getting alert state when no record exists."""
    alert_state = alert_manager.get_alert_state()

    assert alert_state["alert_type"] == "token_threshold"
    assert alert_state["last_triggered"] is None
    assert alert_state["is_active"] is False
    assert alert_state["metadata"] == {}


def test_get_alert_state_with_record(alert_manager, cleanup_alert_state):
    """Test getting alert state when record exists."""
    # Create alert state
    alert_manager._update_alert_state(is_active=True)

    alert_state = alert_manager.get_alert_state()

    assert alert_state["alert_type"] == "token_threshold"
    assert alert_state["last_triggered"] is not None
    assert alert_state["is_active"] is True


def test_alert_state_persistence(alert_manager, cleanup_alert_state):
    """Test that alert state persists across multiple operations."""
    # Set to active
    alert_manager._update_alert_state(is_active=True)
    state1 = alert_manager.get_alert_state()
    assert state1["is_active"] is True

    # Set to inactive
    alert_manager._update_alert_state(is_active=False)
    state2 = alert_manager.get_alert_state()
    assert state2["is_active"] is False

    # Set back to active
    alert_manager._update_alert_state(is_active=True)
    state3 = alert_manager.get_alert_state()
    assert state3["is_active"] is True


def test_threshold_boundary_conditions(alert_manager, cleanup_alert_state):
    """Test threshold checking at boundary values."""
    # Exactly at threshold
    result = alert_manager.check_threshold(current_count=10)
    assert result is False

    # One below threshold
    result = alert_manager.check_threshold(current_count=9)
    assert result is True

    # One above threshold
    result = alert_manager.check_threshold(current_count=11)
    assert result is False

    # Zero tokens
    result = alert_manager.check_threshold(current_count=0)
    assert result is True


def test_email_template_rendering(alert_manager, mailer, cleanup_alert_state):
    """Test that email template is rendered with correct values."""
    template_path = "templates/threshold_alert.html"

    alert_manager.send_threshold_alert(current_count=3, template_path=template_path)

    # Get the email content that was sent
    call_args = mailer.send_email.call_args
    email_content = call_args[0][0]

    # Verify template variables were replaced
    assert "3" in email_content  # current_count
    assert "10" in email_content  # threshold
    assert "Token Inventory Alert" in email_content
