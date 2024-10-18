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


def test_add_tokens_to_tokenpool():
    """Test the add_tokens_to_tokenpool method."""
    tokenpool = TokenPool()
    tokenpool.create_tokenpool(10)
    tokenpool.add_tokens_to_tokenpool(5)
    assert tokenpool.get_tokenpool(tokenpool.pool_uuid) == 15
    tokenpool.add_tokens_to_tokenpool(5)
    assert tokenpool.get_tokenpool(tokenpool.pool_uuid) == 20
    tokenpool.add_tokens_to_tokenpool(5)
    assert tokenpool.get_tokenpool(tokenpool.pool_uuid) == 25
    tokenpool.add_tokens_to_tokenpool(5)
    assert tokenpool.get_tokenpool(tokenpool.pool_uuid) == 30


def test_add_tokens_to_non_existent_tokenpool():
    """Test the add_tokens_to_tokenpool method."""
    tokenpool = TokenPool()
    with pytest.raises(ValueError):
        tokenpool.add_tokens_to_tokenpool(5)


def test_get_tokenpool_fails_with_non_existent_tokenpool():
    """Test the get_tokenpool method and see it fails if the pool uuid does not exist."""
    tokenpool = TokenPool()
    with pytest.raises(ValueError):
        tokenpool.get_tokenpool("non-existent-pool-uuid")


def test_remove_tokens_from_tokenpool():
    """Test the remove_tokens_from_tokenpool method."""
    tokenpool = TokenPool()
    tokenpool.create_tokenpool(10)
    tokenpool.remove_tokens_from_tokenpool(5)
    assert tokenpool.get_tokenpool(tokenpool.pool_uuid) == 5
    tokenpool.remove_tokens_from_tokenpool(5)
    assert tokenpool.get_tokenpool(tokenpool.pool_uuid) == 0
    with pytest.raises(ValueError):
        tokenpool.remove_tokens_from_tokenpool(5)
    assert tokenpool.get_tokenpool(tokenpool.pool_uuid) == 0


def test_remove_tokens_from_non_existent_tokenpool():
    """Test the remove_tokens_from_tokenpool method."""
    tokenpool = TokenPool()
    with pytest.raises(ValueError):
        tokenpool.remove_tokens_from_tokenpool(5)


def test_remove_tokens_from_tokenpool_by_pooluuid():
    """Test tokens can be removed from a token pool by pooluuid."""
    tokenpool = TokenPool()
    tokenpool.create_tokenpool(10)
    pool_uuid = tokenpool.pool_uuid

    another_tokenpool = TokenPool(pool_uuid=pool_uuid)
    another_tokenpool.remove_tokens_from_tokenpool(5)
    assert another_tokenpool.get_tokenpool(pool_uuid) == 5
    another_tokenpool.remove_tokens_from_tokenpool(5)
    assert another_tokenpool.get_tokenpool(pool_uuid) == 0
    with pytest.raises(ValueError):
        another_tokenpool.remove_tokens_from_tokenpool(5)
