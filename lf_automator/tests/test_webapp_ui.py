"""Playwright UI tests for the Flask web application.

Feature: web-dashboard, Property 1: Authentication flow (example test)
"""

import os
import re
import threading
import time

import pytest
from loguru import logger
from playwright.sync_api import Page, expect

from lf_automator.automator.tokenpools.pools import TokenPool
from lf_automator.webapp.app import create_app


@pytest.fixture(scope="module")
def flask_server():
    """Start Flask server in a background thread for Playwright tests."""
    # Set up test environment
    test_access_key = "test-playwright-access-key-uuid-12345"
    os.environ["ACCESS_KEY"] = test_access_key
    os.environ["SECRET_KEY"] = "test-secret-key-for-playwright"
    os.environ["FLASK_ENV"] = "development"

    app = create_app()
    port = 8081  # Use different port to avoid conflicts

    # Start Flask server in background thread
    def run_server():
        app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False)

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Wait for server to start
    time.sleep(2)

    base_url = f"http://127.0.0.1:{port}"

    yield {"base_url": base_url, "access_key": test_access_key}

    # Cleanup
    del os.environ["ACCESS_KEY"]
    del os.environ["SECRET_KEY"]
    del os.environ["FLASK_ENV"]


class TestAuthenticationFlow:
    """Tests for authentication flow using Playwright.

    Feature: web-dashboard, Property 1: Authentication flow (example test)
    Validates: Requirements 2.1, 2.2, 2.3, 2.5
    """

    def test_login_with_valid_access_key_grants_access(
        self, page: Page, flask_server: dict
    ):
        """Test that login with valid access key grants access to dashboard.

        Validates: Requirements 2.1, 2.2
        """
        base_url = flask_server["base_url"]
        valid_key = flask_server["access_key"]

        # Navigate to login page
        page.goto(f"{base_url}/login")

        # Verify we're on the login page
        expect(page).to_have_url(f"{base_url}/login")

        # Find and fill the access key input
        access_key_input = page.locator('input[name="access_key"]')
        expect(access_key_input).to_be_visible()
        access_key_input.fill(valid_key)

        # Submit the form
        submit_button = page.locator('button[type="submit"]')
        submit_button.click()

        # Wait for navigation to dashboard
        page.wait_for_url(f"{base_url}/")

        # Verify we're redirected to dashboard
        expect(page).to_have_url(f"{base_url}/")

        # Verify dashboard content is visible (not redirected back to login)
        # The dashboard should have some content indicating successful authentication
        expect(page.locator("body")).to_be_visible()

    def test_login_with_invalid_access_key_shows_error(
        self, page: Page, flask_server: dict
    ):
        """Test that login with invalid access key shows error message.

        Validates: Requirements 2.2, 2.3
        """
        base_url = flask_server["base_url"]
        invalid_key = "wrong-invalid-access-key-12345"

        # Navigate to login page
        page.goto(f"{base_url}/login")

        # Fill in invalid access key
        access_key_input = page.locator('input[name="access_key"]')
        access_key_input.fill(invalid_key)

        # Submit the form
        submit_button = page.locator('button[type="submit"]')
        submit_button.click()

        # Wait for page to reload/respond
        page.wait_for_load_state("networkidle")

        # Verify we're still on the login page
        expect(page).to_have_url(f"{base_url}/login")

        # Verify error message is displayed
        error_message = page.locator("text=/Invalid access key/i")
        expect(error_message).to_be_visible()

    def test_session_persistence_across_page_navigations(
        self, page: Page, flask_server: dict
    ):
        """Test that authentication session persists across page navigations.

        Validates: Requirements 2.5
        """
        base_url = flask_server["base_url"]
        valid_key = flask_server["access_key"]

        # First, login with valid credentials
        page.goto(f"{base_url}/login")
        access_key_input = page.locator('input[name="access_key"]')
        access_key_input.fill(valid_key)
        submit_button = page.locator('button[type="submit"]')
        submit_button.click()

        # Wait for navigation to dashboard
        page.wait_for_url(f"{base_url}/")
        expect(page).to_have_url(f"{base_url}/")

        # Navigate to login page again
        page.goto(f"{base_url}/login")

        # Since we're already authenticated, we might be redirected to dashboard
        # or we might see the login page. Let's check if we can access dashboard
        page.goto(f"{base_url}/")

        # Verify we can still access the dashboard without re-authenticating
        expect(page).to_have_url(f"{base_url}/")
        expect(page.locator("body")).to_be_visible()

        # Navigate away and back to verify session persists
        page.goto(f"{base_url}/login")
        page.goto(f"{base_url}/")

        # Should still be able to access dashboard
        expect(page).to_have_url(f"{base_url}/")

    def test_unauthenticated_access_redirects_to_login(
        self, page: Page, flask_server: dict
    ):
        """Test that unauthenticated access to dashboard redirects to login.

        Validates: Requirements 2.1
        """
        base_url = flask_server["base_url"]

        # Try to access dashboard without authentication
        page.goto(f"{base_url}/")

        # Should be redirected to login page
        page.wait_for_url(f"{base_url}/login")
        expect(page).to_have_url(f"{base_url}/login")

        # Verify login form is visible
        access_key_input = page.locator('input[name="access_key"]')
        expect(access_key_input).to_be_visible()

    def test_empty_access_key_shows_error(self, page: Page, flask_server: dict):
        """Test that submitting empty access key shows error message.

        Validates: Requirements 2.3
        """
        base_url = flask_server["base_url"]

        # Navigate to login page
        page.goto(f"{base_url}/login")

        # Remove the 'required' attribute to test server-side validation
        page.evaluate(
            "document.querySelector('input[name=\"access_key\"]').removeAttribute('required')"
        )

        # Submit form with empty access key
        submit_button = page.locator('button[type="submit"]')
        submit_button.click()

        # Wait for page to reload/respond
        page.wait_for_load_state("networkidle")

        # Verify we're still on the login page
        expect(page).to_have_url(f"{base_url}/login")

        # Verify error message is displayed
        error_message = page.locator("text=/Invalid access key/i")
        expect(error_message).to_be_visible()


class TestTokenPoolDisplay:
    """Tests for token pool display using Playwright.

    Feature: web-dashboard, Property 1: Token pool display completeness
    Validates: Requirements 3.2, 3.3, 3.4, 3.5
    """

    def test_token_pool_display_completeness(
        self, page: Page, flask_server: dict, db_connection
    ):
        """Test that all token pools are displayed with complete information.

        Property 1: Token pool display completeness
        For any token pool in the database, when displayed on the dashboard,
        the UI should show the pool name, current token count, pool state,
        and last updated timestamp.

        Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
        """
        base_url = flask_server["base_url"]
        valid_key = flask_server["access_key"]

        # Seed database with test pools in different states
        test_pools = []

        # Create pool 1: Normal state (>10 tokens)
        pool1 = TokenPool()
        pool1_uuid = pool1.create_tokenpool(
            token_count=50, pool_status="active", pool_priority=1
        )
        test_pools.append(
            {
                "uuid": pool1_uuid,
                "current_count": 50,
                "start_count": 50,
                "state": "normal",
                "status": "active",
            }
        )

        # Create pool 2: Warning state (6-10 tokens)
        pool2 = TokenPool()
        pool2_uuid = pool2.create_tokenpool(
            token_count=8, pool_status="active", pool_priority=2
        )
        test_pools.append(
            {
                "uuid": pool2_uuid,
                "current_count": 8,
                "start_count": 8,
                "state": "warning",
                "status": "active",
            }
        )

        # Create pool 3: Critical state (<=5 tokens)
        pool3 = TokenPool()
        pool3_uuid = pool3.create_tokenpool(
            token_count=3, pool_status="active", pool_priority=3
        )
        test_pools.append(
            {
                "uuid": pool3_uuid,
                "current_count": 3,
                "start_count": 3,
                "state": "critical",
                "status": "active",
            }
        )

        try:
            # Login to access dashboard
            page.goto(f"{base_url}/login")
            access_key_input = page.locator('input[name="access_key"]')
            access_key_input.fill(valid_key)
            submit_button = page.locator('button[type="submit"]')
            submit_button.click()

            # Wait for navigation to dashboard
            page.wait_for_url(f"{base_url}/")

            # Verify all pools are displayed
            pool_cards = page.locator(".pool-card")
            expect(pool_cards).to_have_count(len(test_pools))

            # Verify each pool shows complete information
            for i, test_pool in enumerate(test_pools):
                pool_card = pool_cards.nth(i)

                # Verify pool name/identifier is displayed
                pool_uuid_short = test_pool["uuid"][:8]
                pool_name = pool_card.locator(f"text=/Pool #{pool_uuid_short}/i")
                expect(pool_name).to_be_visible()

                # Verify current count is displayed in the circular progress indicator
                current_count_value = pool_card.locator(".text-3xl.font-bold")
                expect(current_count_value).to_be_visible()
                expect(current_count_value).to_have_text(
                    str(test_pool["current_count"])
                )

                # Verify state indicator is displayed with correct state
                if test_pool["state"] == "critical":
                    # Check for state in the details section
                    state_text = pool_card.locator("text=/critical/i")
                    expect(state_text).to_be_visible()
                elif test_pool["state"] == "warning":
                    state_text = pool_card.locator("text=/warning/i")
                    expect(state_text).to_be_visible()
                else:  # normal
                    state_text = pool_card.locator("text=/normal/i")
                    expect(state_text).to_be_visible()

                # Verify timestamp is displayed
                timestamp_label = pool_card.locator("text=/Last Updated:/i")
                expect(timestamp_label).to_be_visible()

                # Verify status is displayed in the Status detail box
                # Look for the status in the grid details section, not the badge
                status_detail = pool_card.locator(".bg-gray-50.rounded-lg.p-3").filter(
                    has_text="Status"
                )
                status_value = status_detail.locator(".font-semibold")
                # The status is stored as lowercase in the database
                expect(status_value).to_have_text(test_pool["status"])

        finally:
            # Cleanup: Delete test pools
            for test_pool in test_pools:
                try:
                    with db_connection.connection:
                        with db_connection.connection.cursor() as cursor:
                            cursor.execute(
                                "DELETE FROM lfautomator.accessTokenPools WHERE pooluuid = %s",
                                (test_pool["uuid"],),
                            )
                except Exception as e:
                    logger.error(f"Error cleaning up test pool: {e}")

    def test_visual_state_indicators(
        self, page: Page, flask_server: dict, db_connection
    ):
        """Test that pools in different states display correct color indicators.

        Validates: Requirements 4.1, 4.2, 4.3
        """
        base_url = flask_server["base_url"]
        valid_key = flask_server["access_key"]

        # Seed database with test pools in different states
        test_pools = []

        # Create pool 1: Normal state (>10 tokens) - should be green
        pool1 = TokenPool()
        pool1_uuid = pool1.create_tokenpool(
            token_count=50, pool_status="active", pool_priority=1
        )
        test_pools.append(
            {
                "uuid": pool1_uuid,
                "state": "normal",
                "expected_color": "bg-green-100",
                "expected_text_color": "text-green-800",
                "expected_border": "border-green-300",
            }
        )

        # Create pool 2: Warning state (6-10 tokens) - should be yellow
        pool2 = TokenPool()
        pool2_uuid = pool2.create_tokenpool(
            token_count=8, pool_status="active", pool_priority=2
        )
        test_pools.append(
            {
                "uuid": pool2_uuid,
                "state": "warning",
                "expected_color": "bg-yellow-100",
                "expected_text_color": "text-yellow-800",
                "expected_border": "border-yellow-300",
            }
        )

        # Create pool 3: Critical state (<=5 tokens) - should be red
        pool3 = TokenPool()
        pool3_uuid = pool3.create_tokenpool(
            token_count=3, pool_status="active", pool_priority=3
        )
        test_pools.append(
            {
                "uuid": pool3_uuid,
                "state": "critical",
                "expected_color": "bg-red-100",
                "expected_text_color": "text-red-800",
                "expected_border": "border-red-300",
            }
        )

        try:
            # Login to access dashboard
            page.goto(f"{base_url}/login")
            access_key_input = page.locator('input[name="access_key"]')
            access_key_input.fill(valid_key)
            submit_button = page.locator('button[type="submit"]')
            submit_button.click()

            # Wait for navigation to dashboard
            page.wait_for_url(f"{base_url}/")

            # Verify all pools are displayed
            pool_cards = page.locator(".pool-card")
            expect(pool_cards).to_have_count(len(test_pools))

            # Verify each pool has correct color indicators
            for i, test_pool in enumerate(test_pools):
                pool_card = pool_cards.nth(i)

                # Find the state text in the details section (not a badge)
                # The state is displayed in the "State" detail box with capitalize
                state_text = pool_card.locator(
                    f"text={test_pool['state'].capitalize()}"
                )

                # Verify the state text is visible
                expect(state_text).to_be_visible()

                # Verify the circular progress indicator has the correct color
                # The progress circle uses different colors based on state
                if test_pool["state"] == "critical":
                    # Check for red color in the SVG circle
                    progress_circle = pool_card.locator("circle.text-red-500")
                    expect(progress_circle).to_be_visible()
                elif test_pool["state"] == "warning":
                    # Check for orange color in the SVG circle
                    progress_circle = pool_card.locator("circle.text-orange-500")
                    expect(progress_circle).to_be_visible()
                else:  # normal
                    # Check for green color in the SVG circle
                    progress_circle = pool_card.locator("circle.text-green-500")
                    expect(progress_circle).to_be_visible()

        finally:
            # Cleanup: Delete test pools
            for test_pool in test_pools:
                try:
                    with db_connection.connection:
                        with db_connection.connection.cursor() as cursor:
                            cursor.execute(
                                "DELETE FROM lfautomator.accessTokenPools WHERE pooluuid = %s",
                                (test_pool["uuid"],),
                            )
                except Exception as e:
                    logger.error(f"Error cleaning up test pool: {e}")


class TestNewPoolCreation:
    """Tests for new pool creation functionality using Playwright.

    Feature: web-dashboard, Property 2: Valid pool registration creates database entry
    Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.6
    """

    def test_new_pool_button_opens_modal(self, page: Page, flask_server: dict):
        """Test that clicking the New Pool button opens a modal dialog.

        Validates: Requirements 8.1
        """
        base_url = flask_server["base_url"]
        valid_key = flask_server["access_key"]

        # Login to access dashboard
        page.goto(f"{base_url}/login")
        access_key_input = page.locator('input[name="access_key"]')
        access_key_input.fill(valid_key)
        submit_button = page.locator('button[type="submit"]')
        submit_button.click()

        # Wait for navigation to dashboard
        page.wait_for_url(f"{base_url}/")

        # Click the New Pool button
        new_pool_button = page.locator("#newPoolButton")
        expect(new_pool_button).to_be_visible()
        new_pool_button.click()

        # Verify modal is displayed
        modal = page.locator("#newPoolModal")
        expect(modal).to_be_visible()

        # Verify modal contains form elements
        token_count_input = page.locator("#tokenCount")
        expect(token_count_input).to_be_visible()

        # Verify modal has cancel and submit buttons
        cancel_button = page.locator("#cancelButton")
        expect(cancel_button).to_be_visible()

        submit_button = page.locator('button[type="submit"]:has-text("Create Pool")')
        expect(submit_button).to_be_visible()

    def test_create_pool_with_valid_token_count(
        self, page: Page, flask_server: dict, db_connection
    ):
        """Test that creating a pool with valid token count succeeds.

        Property 2: Valid pool registration creates database entry
        Validates: Requirements 8.2, 8.3, 8.4
        """
        base_url = flask_server["base_url"]
        valid_key = flask_server["access_key"]
        test_token_count = 25
        created_pool_uuid = None

        try:
            # Login to access dashboard
            page.goto(f"{base_url}/login")
            access_key_input = page.locator('input[name="access_key"]')
            access_key_input.fill(valid_key)
            submit_button = page.locator('button[type="submit"]')
            submit_button.click()

            # Wait for navigation to dashboard
            page.wait_for_url(f"{base_url}/")

            # Get initial pool count
            initial_pool_cards = page.locator(".pool-card")
            initial_count = initial_pool_cards.count()

            # Click the New Pool button
            new_pool_button = page.locator("#newPoolButton")
            new_pool_button.click()

            # Wait for modal to appear
            modal = page.locator("#newPoolModal")
            expect(modal).to_be_visible()

            # Fill in token count
            token_count_input = page.locator("#tokenCount")
            token_count_input.fill(str(test_token_count))

            # Submit the form
            submit_button = page.locator(
                'button[type="submit"]:has-text("Create Pool")'
            )
            submit_button.click()

            # Wait for modal to close (indicates success)
            expect(modal).not_to_be_visible(timeout=5000)

            # Wait for pools to refresh
            page.wait_for_timeout(2000)  # Give time for refresh to complete

            # Verify pool count increased
            updated_pool_cards = page.locator(".pool-card")
            expect(updated_pool_cards).to_have_count(initial_count + 1)

            # Verify the new pool exists in the database
            with db_connection.connection:
                with db_connection.connection.cursor() as cursor:
                    cursor.execute(
                        """SELECT pooluuid, startcount, currentcount, poolStatus 
                           FROM lfautomator.accessTokenPools 
                           WHERE startcount = %s 
                           ORDER BY pooldate DESC 
                           LIMIT 1""",
                        (test_token_count,),
                    )
                    row = cursor.fetchone()
                    assert row is not None, "Pool not found in database"
                    created_pool_uuid = row[0]
                    assert row[1] == test_token_count, "Start count mismatch"
                    assert row[2] == test_token_count, "Current count mismatch"
                    assert row[3] == "active", "Pool status should be active"

        finally:
            # Cleanup: Delete test pool
            if created_pool_uuid:
                try:
                    with db_connection.connection:
                        with db_connection.connection.cursor() as cursor:
                            cursor.execute(
                                "DELETE FROM lfautomator.accessTokenPools WHERE pooluuid = %s",
                                (created_pool_uuid,),
                            )
                except Exception as e:
                    logger.error(f"Error cleaning up test pool: {e}")

    def test_create_pool_with_invalid_token_count_shows_error(
        self, page: Page, flask_server: dict
    ):
        """Test that creating a pool with invalid token count shows error.

        Property 3: Invalid pool registration shows error
        Validates: Requirements 8.5
        """
        base_url = flask_server["base_url"]
        valid_key = flask_server["access_key"]

        # Login to access dashboard
        page.goto(f"{base_url}/login")
        access_key_input = page.locator('input[name="access_key"]')
        access_key_input.fill(valid_key)
        submit_button = page.locator('button[type="submit"]')
        submit_button.click()

        # Wait for navigation to dashboard
        page.wait_for_url(f"{base_url}/")

        # Click the New Pool button
        new_pool_button = page.locator("#newPoolButton")
        new_pool_button.click()

        # Wait for modal to appear
        modal = page.locator("#newPoolModal")
        expect(modal).to_be_visible()

        # Try to submit with empty token count (remove required attribute first)
        page.evaluate(
            "document.querySelector('#tokenCount').removeAttribute('required')"
        )

        # Submit the form
        submit_button = page.locator('button[type="submit"]:has-text("Create Pool")')
        submit_button.click()

        # Verify error message is displayed
        error_message = page.locator("text=/Please enter a valid token count/i")
        expect(error_message).to_be_visible()

        # Modal should still be visible
        expect(modal).to_be_visible()

    def test_cancel_button_closes_modal(self, page: Page, flask_server: dict):
        """Test that clicking cancel button closes the modal without creating a pool.

        Validates: Requirements 8.1
        """
        base_url = flask_server["base_url"]
        valid_key = flask_server["access_key"]

        # Login to access dashboard
        page.goto(f"{base_url}/login")
        access_key_input = page.locator('input[name="access_key"]')
        access_key_input.fill(valid_key)
        submit_button = page.locator('button[type="submit"]')
        submit_button.click()

        # Wait for navigation to dashboard
        page.wait_for_url(f"{base_url}/")

        # Click the New Pool button
        new_pool_button = page.locator("#newPoolButton")
        new_pool_button.click()

        # Wait for modal to appear
        modal = page.locator("#newPoolModal")
        expect(modal).to_be_visible()

        # Click cancel button
        cancel_button = page.locator("#cancelButton")
        cancel_button.click()

        # Verify modal is closed
        expect(modal).not_to_be_visible()

    def test_modal_closes_on_background_click(self, page: Page, flask_server: dict):
        """Test that clicking outside the modal closes it.

        Validates: Requirements 8.1
        """
        base_url = flask_server["base_url"]
        valid_key = flask_server["access_key"]

        # Login to access dashboard
        page.goto(f"{base_url}/login")
        access_key_input = page.locator('input[name="access_key"]')
        access_key_input.fill(valid_key)
        submit_button = page.locator('button[type="submit"]')
        submit_button.click()

        # Wait for navigation to dashboard
        page.wait_for_url(f"{base_url}/")

        # Click the New Pool button
        new_pool_button = page.locator("#newPoolButton")
        new_pool_button.click()

        # Wait for modal to appear
        modal = page.locator("#newPoolModal")
        expect(modal).to_be_visible()

        # Click on the modal background using JavaScript (more reliable than position click)
        page.evaluate("""
            const modal = document.getElementById('newPoolModal');
            const event = new MouseEvent('click', { bubbles: true });
            Object.defineProperty(event, 'target', { value: modal, enumerable: true });
            modal.dispatchEvent(event);
        """)

        # Verify modal is closed
        expect(modal).not_to_be_visible()


class TestTokenPoolActivation:
    """Tests for token pool activation functionality using Playwright.

    Feature: web-dashboard, Property 5: Pool activation updates database
    Validates: Requirements 9.2, 9.3
    """

    def test_activate_button_visible_for_inactive_pool(
        self, page: Page, flask_server: dict, db_connection
    ):
        """Test that Activate Pool button is visible for inactive pools.

        Validates: Requirements 9.1, 9.4
        """
        base_url = flask_server["base_url"]
        valid_key = flask_server["access_key"]

        # Create an inactive pool
        pool = TokenPool()
        pool_uuid = pool.create_tokenpool(
            token_count=20, pool_status="inactive", pool_priority=1
        )

        try:
            # Login to access dashboard
            page.goto(f"{base_url}/login")
            access_key_input = page.locator('input[name="access_key"]')
            access_key_input.fill(valid_key)
            submit_button = page.locator('button[type="submit"]')
            submit_button.click()

            # Wait for navigation to dashboard
            page.wait_for_url(f"{base_url}/")

            # Verify INACTIVE badge is visible
            inactive_badge = page.locator("text=/INACTIVE/i").first
            expect(inactive_badge).to_be_visible()

            # Verify Activate Pool button is visible
            activate_button = page.locator(
                f'button.toggle-status-btn[data-pool-id="{pool_uuid}"]:has-text("Activate Pool")'
            )
            expect(activate_button).to_be_visible()

            # Verify button has correct styling (green background)
            expect(activate_button).to_have_class(re.compile(r"bg-green-600"))

        finally:
            # Cleanup: Delete test pool
            try:
                with db_connection.connection:
                    with db_connection.connection.cursor() as cursor:
                        cursor.execute(
                            "DELETE FROM lfautomator.accessTokenPools WHERE pooluuid = %s",
                            (pool_uuid,),
                        )
            except Exception as e:
                logger.error(f"Error cleaning up test pool: {e}")

    def test_activate_pool_button_updates_status(
        self, page: Page, flask_server: dict, db_connection
    ):
        """Test that clicking Activate Pool button updates pool status to active.

        Property 5: Pool activation updates database
        Validates: Requirements 9.2, 9.3
        """
        base_url = flask_server["base_url"]
        valid_key = flask_server["access_key"]

        # Create an inactive pool
        pool = TokenPool()
        pool_uuid = pool.create_tokenpool(
            token_count=20, pool_status="inactive", pool_priority=1
        )

        try:
            # Login to access dashboard
            page.goto(f"{base_url}/login")
            access_key_input = page.locator('input[name="access_key"]')
            access_key_input.fill(valid_key)
            submit_button = page.locator('button[type="submit"]')
            submit_button.click()

            # Wait for navigation to dashboard
            page.wait_for_url(f"{base_url}/")

            # Verify pool is initially inactive
            inactive_badge = page.locator("text=/INACTIVE/i").first
            expect(inactive_badge).to_be_visible()

            # Click the Activate Pool button
            activate_button = page.locator(
                f'button.toggle-status-btn[data-pool-id="{pool_uuid}"]:has-text("Activate Pool")'
            )
            activate_button.click()

            # Wait for API call to complete and pools to refresh
            page.wait_for_timeout(4000)

            # Verify pool status changed in database
            with db_connection.connection:
                with db_connection.connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT poolStatus FROM lfautomator.accessTokenPools WHERE pooluuid = %s",
                        (pool_uuid,),
                    )
                    row = cursor.fetchone()
                    assert row is not None, "Pool not found in database"
                    assert row[0] == "active", "Pool status should be active"

            # Verify UI updated - pool should now show ACTIVE badge
            active_badge = page.locator("text=/ACTIVE/i").first
            expect(active_badge).to_be_visible()

        finally:
            # Cleanup: Delete test pool
            try:
                with db_connection.connection:
                    with db_connection.connection.cursor() as cursor:
                        cursor.execute(
                            "DELETE FROM lfautomator.accessTokenPools WHERE pooluuid = %s",
                            (pool_uuid,),
                        )
            except Exception as e:
                logger.error(f"Error cleaning up test pool: {e}")

    def test_deactivate_pool_button_updates_status(
        self, page: Page, flask_server: dict, db_connection
    ):
        """Test that clicking Deactivate Pool button updates pool status to inactive.

        Validates: Requirements 9.2, 9.3
        """
        base_url = flask_server["base_url"]
        valid_key = flask_server["access_key"]

        # Create an active pool
        pool = TokenPool()
        pool_uuid = pool.create_tokenpool(
            token_count=20, pool_status="active", pool_priority=1
        )

        try:
            # Login to access dashboard
            page.goto(f"{base_url}/login")
            access_key_input = page.locator('input[name="access_key"]')
            access_key_input.fill(valid_key)
            submit_button = page.locator('button[type="submit"]')
            submit_button.click()

            # Wait for navigation to dashboard
            page.wait_for_url(f"{base_url}/")

            # Verify pool is initially active
            active_badge = page.locator("text=/ACTIVE/i").first
            expect(active_badge).to_be_visible()

            # Click the Deactivate Pool button
            deactivate_button = page.locator(
                f'button.toggle-status-btn[data-pool-id="{pool_uuid}"]:has-text("Deactivate Pool")'
            )
            deactivate_button.click()

            # Wait for API call to complete and pools to refresh
            page.wait_for_timeout(3000)

            # Verify pool status changed in database
            with db_connection.connection:
                with db_connection.connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT poolStatus FROM lfautomator.accessTokenPools WHERE pooluuid = %s",
                        (pool_uuid,),
                    )
                    row = cursor.fetchone()
                    assert row is not None, "Pool not found in database"
                    assert row[0] == "inactive", "Pool status should be inactive"

            # Verify UI updated - pool should now show INACTIVE badge
            inactive_badge = page.locator("text=/INACTIVE/i").first
            expect(inactive_badge).to_be_visible()

        finally:
            # Cleanup: Delete test pool
            try:
                with db_connection.connection:
                    with db_connection.connection.cursor() as cursor:
                        cursor.execute(
                            "DELETE FROM lfautomator.accessTokenPools WHERE pooluuid = %s",
                            (pool_uuid,),
                        )
            except Exception as e:
                logger.error(f"Error cleaning up test pool: {e}")

    def test_activate_button_shows_success_message(
        self, page: Page, flask_server: dict, db_connection
    ):
        """Test that activating a pool shows a success message.

        Validates: Requirements 9.5
        """
        base_url = flask_server["base_url"]
        valid_key = flask_server["access_key"]

        # Create an inactive pool
        pool = TokenPool()
        pool_uuid = pool.create_tokenpool(
            token_count=20, pool_status="inactive", pool_priority=1
        )

        try:
            # Login to access dashboard
            page.goto(f"{base_url}/login")
            access_key_input = page.locator('input[name="access_key"]')
            access_key_input.fill(valid_key)
            submit_button = page.locator('button[type="submit"]')
            submit_button.click()

            # Wait for navigation to dashboard
            page.wait_for_url(f"{base_url}/")

            # Click the Activate Pool button
            activate_button = page.locator(
                f'button.toggle-status-btn[data-pool-id="{pool_uuid}"]:has-text("Activate Pool")'
            )
            activate_button.click()

            # Wait for API call to complete
            page.wait_for_timeout(2000)

            # Verify success message appears (check for message container visibility)
            success_message = page.locator("#messageContainer")
            expect(success_message).to_be_visible(timeout=5000)

        finally:
            # Cleanup: Delete test pool
            try:
                with db_connection.connection:
                    with db_connection.connection.cursor() as cursor:
                        cursor.execute(
                            "DELETE FROM lfautomator.accessTokenPools WHERE pooluuid = %s",
                            (pool_uuid,),
                        )
            except Exception as e:
                logger.error(f"Error cleaning up test pool: {e}")
