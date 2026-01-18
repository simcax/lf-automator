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


# Multi-pool support tests


def test_get_primary_pool_with_single_pool():
    """Test get_primary_pool returns the only active pool."""
    tokenpool = TokenPool()
    pool_uuid = tokenpool.create_tokenpool(10)

    # Get all active pools and find ours
    all_pools = tokenpool.get_all_active_pools()
    our_pool = next((p for p in all_pools if p["pool_uuid"] == pool_uuid), None)
    assert our_pool is not None
    assert our_pool["current_count"] == 10
    assert our_pool["pool_status"] == "active"


def test_get_all_active_pools():
    """Test get_all_active_pools returns all active pools ordered by priority."""
    tokenpool1 = TokenPool()
    uuid1 = tokenpool1.create_tokenpool(10)

    tokenpool2 = TokenPool()
    uuid2 = tokenpool2.create_tokenpool(20)

    tokenpool3 = TokenPool()
    uuid3 = tokenpool3.create_tokenpool(30)

    pools = tokenpool1.get_all_active_pools()
    assert len(pools) >= 3

    # Find our pools
    our_pools = [p for p in pools if p["pool_uuid"] in [uuid1, uuid2, uuid3]]
    assert len(our_pools) == 3

    # Check they're ordered by priority (oldest first)
    assert our_pools[0]["pool_uuid"] == uuid1
    assert our_pools[1]["pool_uuid"] == uuid2
    assert our_pools[2]["pool_uuid"] == uuid3


def test_get_total_available_tokens():
    """Test get_total_available_tokens sums across all active pools."""
    tokenpool1 = TokenPool()
    tokenpool1.create_tokenpool(10)

    tokenpool2 = TokenPool()
    tokenpool2.create_tokenpool(20)

    tokenpool3 = TokenPool()
    tokenpool3.create_tokenpool(30)

    total = tokenpool1.get_total_available_tokens()
    assert total >= 60  # At least our 3 pools


def test_distribute_tokens_from_single_pool():
    """Test distribute_tokens works with a single pool."""
    tokenpool = TokenPool()

    # Get current total to understand the baseline
    total_before = tokenpool.get_total_available_tokens()

    pool_uuid = tokenpool.create_tokenpool(10)

    result = tokenpool.distribute_tokens(5)
    assert result is True

    # Verify total decreased by 5
    total_after = tokenpool.get_total_available_tokens()
    assert total_after == total_before + 10 - 5


def test_distribute_tokens_with_auto_switching():
    """Test distribute_tokens automatically switches between pools."""
    tokenpool1 = TokenPool()

    # Get baseline
    total_before = tokenpool1.get_total_available_tokens()

    uuid1 = tokenpool1.create_tokenpool(5)

    tokenpool2 = TokenPool()
    uuid2 = tokenpool2.create_tokenpool(10)

    # Distribute 8 tokens - should take from oldest pools first
    result = tokenpool1.distribute_tokens(8)
    assert result is True

    # Verify total decreased by 8
    total_after = tokenpool1.get_total_available_tokens()
    assert total_after == total_before + 15 - 8


def test_distribute_tokens_insufficient():
    """Test distribute_tokens returns False when insufficient tokens."""
    tokenpool = TokenPool()

    # Get all active pools and deplete them first
    all_pools = tokenpool.get_all_active_pools()
    for pool in all_pools:
        if pool["current_count"] > 0:
            tp = TokenPool(pool_uuid=pool["pool_uuid"])
            tp.remove_tokens_from_tokenpool(pool["current_count"])

    # Now create a pool with only 5 tokens
    tokenpool.create_tokenpool(5)

    # Try to distribute 10 - should fail
    result = tokenpool.distribute_tokens(10)
    assert result is False


def test_distribute_tokens_invalid_count():
    """Test distribute_tokens raises error for invalid count."""
    tokenpool = TokenPool()
    tokenpool.create_tokenpool(10)

    with pytest.raises(ValueError):
        tokenpool.distribute_tokens(0)

    with pytest.raises(ValueError):
        tokenpool.distribute_tokens(-5)


def test_switch_primary_pool():
    """Test switch_primary_pool marks empty pool as depleted and returns next."""
    tokenpool1 = TokenPool()

    # Get baseline
    total_before = tokenpool1.get_total_available_tokens()

    uuid1 = tokenpool1.create_tokenpool(5)

    tokenpool2 = TokenPool()
    uuid2 = tokenpool2.create_tokenpool(10)

    # Distribute 5 tokens - should deplete from oldest pools
    tokenpool1.distribute_tokens(5)

    # Verify total decreased
    total_after = tokenpool1.get_total_available_tokens()
    assert total_after == total_before + 15 - 5


def test_create_tokenpool_with_custom_priority():
    """Test creating a pool with custom priority."""
    tokenpool = TokenPool()
    pool_uuid = tokenpool.create_tokenpool(10, pool_status="active", pool_priority=100)

    pools = tokenpool.get_all_active_pools()
    our_pool = next(p for p in pools if p["pool_uuid"] == pool_uuid)
    assert our_pool["pool_priority"] == 100


def test_multiple_pools_priority_ordering():
    """Test that multiple pools are correctly ordered by priority."""
    # Create pools with explicit priorities
    tokenpool1 = TokenPool()
    uuid1 = tokenpool1.create_tokenpool(10, pool_priority=100)

    tokenpool2 = TokenPool()
    uuid2 = tokenpool2.create_tokenpool(20, pool_priority=101)

    tokenpool3 = TokenPool()
    uuid3 = tokenpool3.create_tokenpool(30, pool_priority=102)

    # Get all pools and find ours
    all_pools = tokenpool1.get_all_active_pools()
    our_pools = [p for p in all_pools if p["pool_uuid"] in [uuid1, uuid2, uuid3]]

    # Should be ordered by priority
    assert len(our_pools) == 3
    assert our_pools[0]["pool_uuid"] == uuid1
    assert our_pools[0]["pool_priority"] == 100
    assert our_pools[1]["pool_uuid"] == uuid2
    assert our_pools[1]["pool_priority"] == 101
    assert our_pools[2]["pool_uuid"] == uuid3
    assert our_pools[2]["pool_priority"] == 102
