"""Testing the tokens pools module"""

import pytest
from automator.tokenpools.pools import TokenPool


def test_tokenpools():
    """Test the TokenPools class."""
    tokenpool = TokenPool()
    assert tokenpool is not None
    assert isinstance(tokenpool, TokenPool)


def test_tokenpool_connect_to_db():
    """Test the connect_to_db method."""
    tokenpool = TokenPool()
    assert tokenpool.db is not None
    assert tokenpool.db.connection is not None


def test_create_tokenpool_fails_with_0():
    """Test the create_tokenpool method."""
    tokenpool = TokenPool()
    with pytest.raises(ValueError):
        tokenpool.create_tokenpool(0)


def test_create_tokenpool_with_value():
    """Test the create_tokenpool method."""
    tokenpool = TokenPool()
    tokenpool.create_tokenpool(10)
    assert tokenpool.token_count == 10
    assert tokenpool.current_token_count == 10
    assert tokenpool.pool_uuid is not None


def test_get_tokenpool():
    """Test the get_tokenpool method."""
    tokenpool = TokenPool()
    tokenpool.create_tokenpool(10)
    assert tokenpool.get_tokenpool(tokenpool.pool_uuid) == 10


def test_create_tokenpool_fails_with_negative_value():
    """Test the create_tokenpool method."""
    tokenpool = TokenPool()
    with pytest.raises(ValueError):
        tokenpool.create_tokenpool(-1)
