"""Playwright UI tests for token pool deposit functionality."""

import re

import pytest
from playwright.sync_api import Page, expect


def login(page: Page, base_url: str, access_key: str):
    """Helper function to log in to the application."""
    page.goto(f"{base_url}/login")
    page.fill('input[name="access_key"]', access_key)
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/")


@pytest.mark.integration
def test_deposit_updates_total_count(page: Page, flask_server: dict):
    """Test that depositing tokens updates the total count displayed in the UI.

    This test verifies that when tokens are deposited to a pool:
    1. The current count increases
    2. The total count (denominator) also increases to reflect the new capacity
    3. The UI shows "X of Y" where Y is the updated total, not the original start_count
    """
    base_url = flask_server["base_url"]
    access_key = flask_server["access_key"]

    # Login
    login(page, base_url, access_key)

    # Wait for dashboard to load
    expect(page.locator("h2")).to_contain_text("Token Pool Dashboard")

    # Find the first active pool card
    pool_cards = page.locator(".pool-card").all()
    if not pool_cards:
        pytest.skip("No pool cards found on dashboard")

    # Get the first pool card
    pool_card = pool_cards[0]

    # Extract the initial counts from the circular progress indicator
    # The format is: <span>27</span> <span>of 50</span>
    center_text = pool_card.locator(".absolute.flex.flex-col").inner_text()

    # Parse the current count and total count
    match = re.search(r"(\d+)\s+of\s+(\d+)", center_text)
    if not match:
        pytest.fail(f"Could not parse count from: {center_text}")

    initial_current = int(match.group(1))
    initial_total = int(match.group(2))

    # Click the "Deposit/Withdraw" button
    pool_card.locator("button.deposit-withdraw-btn").click()

    # Wait for modal to appear
    modal = page.locator("#depositWithdrawModal")
    expect(modal).to_be_visible()

    # Ensure "Deposit" is selected
    page.locator('input[name="transactionType"][value="deposit"]').check()

    # Enter deposit amount
    deposit_amount = 10
    page.fill("#transactionCount", str(deposit_amount))

    # Submit the form
    page.locator("#depositWithdrawForm button[type='submit']").click()

    # Wait for modal to close
    expect(modal).to_be_hidden()

    # Wait for success message
    expect(page.locator("#messageContainer")).to_contain_text("Successfully deposited")

    # Wait for the pool card to update
    page.wait_for_timeout(1000)  # Give time for the refresh

    # Get the updated counts
    updated_center_text = pool_card.locator(".absolute.flex.flex-col").inner_text()
    updated_match = re.search(r"(\d+)\s+of\s+(\d+)", updated_center_text)

    if not updated_match:
        pytest.fail(f"Could not parse updated count from: {updated_center_text}")

    updated_current = int(updated_match.group(1))
    updated_total = int(updated_match.group(2))

    # Verify the current count increased by the deposit amount
    assert (
        updated_current == initial_current + deposit_amount
    ), f"Expected current count to be {initial_current + deposit_amount}, but got {updated_current}"

    # Verify the total count also increased by the deposit amount
    # This is the bug we're testing for - the total should update, not stay at start_count
    assert (
        updated_total == initial_total + deposit_amount
    ), f"Expected total count to be {initial_total + deposit_amount}, but got {updated_total}"
