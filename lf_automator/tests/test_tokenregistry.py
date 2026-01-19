"""Tests for TokenRegistry component."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from automator.tokenregistry import TokenRegistry


@pytest.mark.integration
def test_register_member_token_new(db_connection):
    """Test registering a new member token."""
    registry = TokenRegistry(db_connection)

    member_uuid = str(uuid4())
    token_number = "TOKEN-001"

    # Should return True for new registration
    is_new = registry.register_member_token(member_uuid, token_number)
    assert is_new is True

    # Verify member exists
    assert registry.member_exists(member_uuid) is True


@pytest.mark.integration
def test_register_member_token_update(db_connection):
    """Test updating an existing member token."""
    registry = TokenRegistry(db_connection)

    member_uuid = str(uuid4())
    token_number_1 = "TOKEN-001"
    token_number_2 = "TOKEN-002"

    # First registration
    is_new = registry.register_member_token(member_uuid, token_number_1)
    assert is_new is True

    # Second registration (update)
    is_new = registry.register_member_token(member_uuid, token_number_2)
    assert is_new is False

    # Verify only one entry exists with updated token
    all_members = registry.get_all_registered_members()
    matching = [m for m in all_members if m["member_uuid"] == member_uuid]
    assert len(matching) == 1
    assert matching[0]["token_number"] == token_number_2


@pytest.mark.integration
def test_get_all_registered_members(db_connection):
    """Test getting all registered members."""
    registry = TokenRegistry(db_connection)

    # Register multiple members
    member_1 = str(uuid4())
    member_2 = str(uuid4())

    registry.register_member_token(member_1, "TOKEN-001")
    registry.register_member_token(member_2, "TOKEN-002")

    # Get all members
    all_members = registry.get_all_registered_members()

    # Should have at least our 2 members
    member_uuids = [m["member_uuid"] for m in all_members]
    assert member_1 in member_uuids
    assert member_2 in member_uuids


@pytest.mark.integration
def test_get_members_registered_since(db_connection):
    """Test filtering members by registration timestamp."""
    registry = TokenRegistry(db_connection)

    # Use a timestamp from the past (1 hour ago)
    timestamp_past = datetime.now() - timedelta(hours=1)

    # Register a member (should be after the past timestamp)
    new_member = str(uuid4())
    registry.register_member_token(new_member, "TOKEN-NEW")

    # Get members registered after the past timestamp
    recent_members = registry.get_members_registered_since(timestamp_past)

    # Should include our newly registered member
    member_uuids = [m["member_uuid"] for m in recent_members]
    assert new_member in member_uuids


@pytest.mark.integration
def test_member_exists(db_connection):
    """Test checking if member exists in registry."""
    registry = TokenRegistry(db_connection)

    member_uuid = str(uuid4())

    # Should not exist initially
    assert registry.member_exists(member_uuid) is False

    # Register member
    registry.register_member_token(member_uuid, "TOKEN-001")

    # Should exist now
    assert registry.member_exists(member_uuid) is True


@pytest.mark.integration
def test_register_member_token_idempotence(db_connection):
    """Test that registering the same member multiple times doesn't create duplicates."""
    registry = TokenRegistry(db_connection)

    member_uuid = str(uuid4())
    token_number = "TOKEN-001"

    # Register same member 5 times
    for _ in range(5):
        registry.register_member_token(member_uuid, token_number)

    # Should only have one entry
    all_members = registry.get_all_registered_members()
    matching = [m for m in all_members if m["member_uuid"] == member_uuid]
    assert len(matching) == 1
