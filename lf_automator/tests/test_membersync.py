"""Tests for the MemberTokenSync class."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from automator.membersync.sync import MemberTokenSync
from automator.tokenregistry.registry import TokenRegistry


@pytest.fixture
def mock_api_client():
    """Create a mock ForeningLet API client."""
    mock_client = Mock()
    return mock_client


@pytest.fixture
def mock_registry():
    """Create a mock TokenRegistry."""
    mock_reg = Mock(spec=TokenRegistry)
    return mock_reg


@pytest.fixture
def sample_memberlist():
    """Create sample memberlist data."""
    return {
        "members": [
            {
                "MemberUuid": "123e4567-e89b-12d3-a456-426614174000",
                "MemberField3": "TOKEN001",
                "Name": "John Doe",
            },
            {
                "MemberUuid": "223e4567-e89b-12d3-a456-426614174001",
                "MemberField3": "TOKEN002",
                "Name": "Jane Smith",
            },
            {
                "MemberUuid": "323e4567-e89b-12d3-a456-426614174002",
                "MemberField3": "",  # Empty token field
                "Name": "Bob Johnson",
            },
            {
                "MemberUuid": "423e4567-e89b-12d3-a456-426614174003",
                "MemberField3": None,  # Null token field
                "Name": "Alice Williams",
            },
            {
                "MemberUuid": "523e4567-e89b-12d3-a456-426614174004",
                "MemberField3": "   ",  # Whitespace-only token field
                "Name": "Charlie Brown",
            },
        ]
    }


def test_membersync_initialization():
    """Test MemberTokenSync initialization."""
    sync = MemberTokenSync()
    assert sync is not None
    assert sync.api_client is not None
    assert sync.registry is not None
    assert sync.max_retries == 5
    assert sync.initial_backoff == 1.0


def test_membersync_custom_initialization(mock_api_client, mock_registry):
    """Test MemberTokenSync initialization with custom parameters."""
    sync = MemberTokenSync(
        api_client=mock_api_client,
        registry=mock_registry,
        max_retries=3,
        initial_backoff=0.5,
    )
    assert sync.api_client == mock_api_client
    assert sync.registry == mock_registry
    assert sync.max_retries == 3
    assert sync.initial_backoff == 0.5


@patch("automator.membersync.sync.Memberlist")
def test_fetch_members_with_tokens(
    mock_memberlist_class, mock_api_client, sample_memberlist
):
    """Test fetching members with tokens from API."""
    # Setup mock
    mock_api_client.get_memberlist.return_value = sample_memberlist
    mock_memberlist_instance = Mock()
    mock_memberlist_instance.memberlist = sample_memberlist["members"]
    mock_memberlist_class.return_value = mock_memberlist_instance

    sync = MemberTokenSync(api_client=mock_api_client, registry=Mock())

    # Execute
    result = sync.fetch_members_with_tokens()

    # Verify
    assert len(result) == 2  # Only members with valid tokens
    assert result[0]["member_uuid"] == "123e4567-e89b-12d3-a456-426614174000"
    assert result[0]["token_number"] == "TOKEN001"
    assert result[1]["member_uuid"] == "223e4567-e89b-12d3-a456-426614174001"
    assert result[1]["token_number"] == "TOKEN002"


@patch("automator.membersync.sync.Memberlist")
def test_fetch_members_with_tokens_filters_empty(
    mock_memberlist_class, mock_api_client, sample_memberlist
):
    """Test that empty/null/whitespace token fields are filtered out."""
    mock_api_client.get_memberlist.return_value = sample_memberlist
    mock_memberlist_instance = Mock()
    mock_memberlist_instance.memberlist = sample_memberlist["members"]
    mock_memberlist_class.return_value = mock_memberlist_instance

    sync = MemberTokenSync(api_client=mock_api_client, registry=Mock())
    result = sync.fetch_members_with_tokens()

    # Should only return members with valid token numbers
    member_uuids = [m["member_uuid"] for m in result]
    assert "323e4567-e89b-12d3-a456-426614174002" not in member_uuids  # Empty
    assert "423e4567-e89b-12d3-a456-426614174003" not in member_uuids  # None
    assert "523e4567-e89b-12d3-a456-426614174004" not in member_uuids  # Whitespace


@patch("automator.membersync.sync.Memberlist")
@patch("automator.membersync.sync.time.sleep")
def test_fetch_members_with_retry_logic(
    mock_sleep, mock_memberlist_class, mock_api_client, sample_memberlist
):
    """Test retry logic with exponential backoff."""
    # Setup: fail twice, then succeed
    mock_api_client.get_memberlist.side_effect = [
        Exception("Network error"),
        Exception("Network error"),
        sample_memberlist,
    ]
    mock_memberlist_instance = Mock()
    mock_memberlist_instance.memberlist = sample_memberlist["members"]
    mock_memberlist_class.return_value = mock_memberlist_instance

    sync = MemberTokenSync(
        api_client=mock_api_client, registry=Mock(), initial_backoff=0.1
    )

    # Execute
    result = sync.fetch_members_with_tokens()

    # Verify
    assert len(result) == 2
    assert mock_api_client.get_memberlist.call_count == 3
    assert mock_sleep.call_count == 2
    # Check exponential backoff: 0.1, 0.2
    mock_sleep.assert_any_call(0.1)
    mock_sleep.assert_any_call(0.2)


@patch("automator.membersync.sync.Memberlist")
def test_fetch_members_max_retries_exceeded(mock_memberlist_class, mock_api_client):
    """Test that RuntimeError is raised after max retries."""
    mock_api_client.get_memberlist.side_effect = Exception("Network error")

    sync = MemberTokenSync(
        api_client=mock_api_client, registry=Mock(), max_retries=3, initial_backoff=0.01
    )

    # Execute and verify
    with pytest.raises(RuntimeError, match="API request failed after 3 retries"):
        sync.fetch_members_with_tokens()

    assert mock_api_client.get_memberlist.call_count == 3


def test_extract_token_number_valid():
    """Test extracting valid token numbers."""
    sync = MemberTokenSync(api_client=Mock(), registry=Mock())

    assert sync._extract_token_number({"MemberField3": "TOKEN001"}) == "TOKEN001"
    assert sync._extract_token_number({"MemberField3": "  TOKEN002  "}) == "TOKEN002"
    assert sync._extract_token_number({"MemberField3": "123"}) == "123"


def test_extract_token_number_invalid():
    """Test filtering invalid token numbers."""
    sync = MemberTokenSync(api_client=Mock(), registry=Mock())

    assert sync._extract_token_number({"MemberField3": ""}) is None
    assert sync._extract_token_number({"MemberField3": None}) is None
    assert sync._extract_token_number({"MemberField3": "   "}) is None
    assert sync._extract_token_number({"MemberField3": "A" * 51}) is None  # Too long


def test_is_valid_token_number():
    """Test token number validation."""
    sync = MemberTokenSync(api_client=Mock(), registry=Mock())

    assert sync._is_valid_token_number("TOKEN001") is True
    assert sync._is_valid_token_number("123") is True
    assert sync._is_valid_token_number("A" * 50) is True  # Max length

    assert sync._is_valid_token_number("") is False
    assert sync._is_valid_token_number("A" * 51) is False  # Too long


@patch("automator.membersync.sync.Memberlist")
def test_sync_to_registry(
    mock_memberlist_class, mock_api_client, mock_registry, sample_memberlist
):
    """Test syncing members to registry."""
    # Setup
    mock_api_client.get_memberlist.return_value = sample_memberlist
    mock_memberlist_instance = Mock()
    mock_memberlist_instance.memberlist = sample_memberlist["members"]
    mock_memberlist_class.return_value = mock_memberlist_instance

    # Mock registry to return True for new registrations
    mock_registry.register_member_token.side_effect = [True, False]  # 1 new, 1 update

    sync = MemberTokenSync(api_client=mock_api_client, registry=mock_registry)

    # Execute
    new_count = sync.sync_to_registry()

    # Verify
    assert new_count == 1
    assert mock_registry.register_member_token.call_count == 2


@patch("automator.membersync.sync.Memberlist")
def test_sync_to_registry_handles_errors(
    mock_memberlist_class, mock_api_client, mock_registry, sample_memberlist
):
    """Test that sync continues even if individual registrations fail."""
    # Setup
    mock_api_client.get_memberlist.return_value = sample_memberlist
    mock_memberlist_instance = Mock()
    mock_memberlist_instance.memberlist = sample_memberlist["members"]
    mock_memberlist_class.return_value = mock_memberlist_instance

    # Mock registry to fail on first, succeed on second
    mock_registry.register_member_token.side_effect = [
        ValueError("Database error"),
        True,
    ]

    sync = MemberTokenSync(api_client=mock_api_client, registry=mock_registry)

    # Execute - should not raise exception
    new_count = sync.sync_to_registry()

    # Verify - should have tried both and counted the successful one
    assert new_count == 1
    assert mock_registry.register_member_token.call_count == 2


def test_get_new_assignments_since(mock_registry):
    """Test getting new assignments since timestamp."""
    # Setup
    timestamp = datetime.now() - timedelta(days=1)
    expected_result = [
        {
            "member_uuid": "123e4567-e89b-12d3-a456-426614174000",
            "token_number": "TOKEN001",
            "registered_at": datetime.now(),
            "updated_at": datetime.now(),
        }
    ]
    mock_registry.get_members_registered_since.return_value = expected_result

    sync = MemberTokenSync(api_client=Mock(), registry=mock_registry)

    # Execute
    result = sync.get_new_assignments_since(timestamp)

    # Verify
    assert result == expected_result
    mock_registry.get_members_registered_since.assert_called_once_with(timestamp)
