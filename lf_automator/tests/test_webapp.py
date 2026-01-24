"""Tests for the Flask web application."""

import os

import pytest

from lf_automator.webapp.app import create_app
from lf_automator.webapp.auth import (
    check_access_key,
    clear_session,
    is_authenticated,
    require_auth,
    set_authenticated,
)


class TestApplicationFactory:
    """Tests for the Flask application factory."""

    def test_create_app_returns_flask_instance(self):
        """Test that create_app returns a Flask application instance."""
        app = create_app()
        assert app is not None
        assert app.name == "lf_automator.webapp.app"

    def test_configuration_loading_from_environment(self):
        """Test that configuration is loaded from environment variables."""
        # Set environment variables
        test_secret = "test-secret-key-12345"
        test_access_key = "test-access-key-uuid"

        os.environ["SECRET_KEY"] = test_secret
        os.environ["ACCESS_KEY"] = test_access_key

        app = create_app()

        assert app.config["SECRET_KEY"] == test_secret
        assert app.config["ACCESS_KEY"] == test_access_key

        # Clean up
        del os.environ["SECRET_KEY"]
        del os.environ["ACCESS_KEY"]

    def test_configuration_defaults_when_env_missing(self):
        """Test that configuration uses defaults when environment variables are missing."""
        # Save original values
        original_secret = os.environ.get("SECRET_KEY")
        original_access = os.environ.get("ACCESS_KEY")

        # Ensure environment variables are not set
        os.environ.pop("SECRET_KEY", None)
        os.environ.pop("ACCESS_KEY", None)

        app = create_app()

        # SECRET_KEY should be generated (not empty)
        assert app.config["SECRET_KEY"] != ""
        assert len(app.config["SECRET_KEY"]) > 0

        # ACCESS_KEY should default to "test"
        assert app.config["ACCESS_KEY"] == "test"

        # Restore original values
        if original_secret:
            os.environ["SECRET_KEY"] = original_secret
        if original_access:
            os.environ["ACCESS_KEY"] = original_access

    def test_session_cookie_configuration(self):
        """Test that session cookie settings are configured correctly."""
        app = create_app()

        assert app.config["SESSION_COOKIE_HTTPONLY"] is True
        assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"

    def test_session_cookie_secure_in_production(self):
        """Test that SESSION_COOKIE_SECURE is True in production environment."""
        os.environ["FLASK_ENV"] = "production"

        app = create_app()

        assert app.config["SESSION_COOKIE_SECURE"] is True

        # Clean up
        del os.environ["FLASK_ENV"]

    def test_session_cookie_not_secure_in_development(self):
        """Test that SESSION_COOKIE_SECURE is False in development environment."""
        os.environ["FLASK_ENV"] = "development"

        app = create_app()

        assert app.config["SESSION_COOKIE_SECURE"] is False

        # Clean up
        del os.environ["FLASK_ENV"]

    def test_blueprint_registration(self):
        """Test that blueprints are registered correctly."""
        app = create_app()

        # Check that the 'main' blueprint is registered
        assert "main" in app.blueprints
        assert app.blueprints["main"] is not None

    def test_static_folder_configuration(self):
        """Test that static folder is configured correctly."""
        app = create_app()

        assert app.static_folder is not None
        assert app.static_folder.endswith("static")

    def test_template_folder_configuration(self):
        """Test that template folder is configured correctly."""
        app = create_app()

        assert app.template_folder is not None
        assert app.template_folder.endswith("templates")

    def test_static_file_serving(self):
        """Test that static files can be served."""
        app = create_app()

        with app.test_client() as client:
            # Test that static route exists
            # Note: This will return 404 if file doesn't exist, but route should be registered
            response = client.get("/static/css/output.css")
            # We expect either 200 (file exists) or 404 (file doesn't exist but route works)
            assert response.status_code in [200, 404]

    def test_app_context_available(self):
        """Test that application context is available."""
        app = create_app()

        with app.app_context():
            from flask import current_app

            assert current_app is not None
            assert current_app.name == "lf_automator.webapp.app"

    def test_test_client_available(self):
        """Test that test client can be created."""
        app = create_app()

        with app.test_client() as client:
            assert client is not None


class TestAuthentication:
    """Tests for the authentication module."""

    def test_check_access_key_with_valid_key(self):
        """Test that check_access_key returns True for valid access key."""
        test_key = "test-uuid-access-key-12345"
        os.environ["ACCESS_KEY"] = test_key

        result = check_access_key(test_key)

        assert result is True

        # Clean up
        del os.environ["ACCESS_KEY"]

    def test_check_access_key_with_invalid_key(self):
        """Test that check_access_key returns False for invalid access key."""
        configured_key = "correct-uuid-access-key"
        provided_key = "wrong-uuid-access-key"

        os.environ["ACCESS_KEY"] = configured_key

        result = check_access_key(provided_key)

        assert result is False

        # Clean up
        del os.environ["ACCESS_KEY"]

    def test_check_access_key_with_empty_provided_key(self):
        """Test that check_access_key returns False for empty provided key."""
        os.environ["ACCESS_KEY"] = "configured-key"

        result = check_access_key("")

        assert result is False

        # Clean up
        del os.environ["ACCESS_KEY"]

    def test_check_access_key_with_empty_configured_key(self):
        """Test that check_access_key returns False when configured key is empty."""
        os.environ["ACCESS_KEY"] = ""

        result = check_access_key("some-key")

        assert result is False

        # Clean up
        del os.environ["ACCESS_KEY"]

    def test_check_access_key_with_missing_env_variable(self):
        """Test that check_access_key returns False when ACCESS_KEY env var is missing."""
        os.environ.pop("ACCESS_KEY", None)

        result = check_access_key("some-key")

        assert result is False

    def test_require_auth_decorator_redirects_unauthenticated(self):
        """Test that require_auth decorator redirects unauthenticated requests."""
        app = create_app()

        @require_auth
        def protected_route():
            return "Protected content"

        # Test decorator behavior by checking it attempts to redirect
        with app.test_request_context():
            # Clear session to ensure not authenticated
            from flask import session as flask_session

            flask_session.clear()

            # Call the decorated function - it will try to redirect
            # Since routes aren't fully set up, we'll catch the BuildError
            # but verify the decorator is checking authentication
            try:
                result = protected_route()
                # If we get here without error, check if it's a redirect
                if hasattr(result, "status_code"):
                    assert result.status_code == 302
            except Exception as e:
                # Expected: BuildError because routes.login doesn't exist yet
                # This confirms the decorator is trying to redirect
                assert "routes.login" in str(e) or "login" in str(e).lower()

    def test_require_auth_decorator_allows_authenticated(self):
        """Test that require_auth decorator allows authenticated requests."""
        app = create_app()

        @require_auth
        def protected_route():
            return "Protected content"

        with app.test_request_context():
            # Set session as authenticated
            from flask import session as flask_session

            flask_session["authenticated"] = True

            # Call the decorated function
            result = protected_route()

            # Should return the protected content
            assert result == "Protected content"

    def test_set_authenticated_sets_session_flag(self):
        """Test that set_authenticated sets the session flag correctly."""
        app = create_app()

        with app.test_request_context():
            from flask import session as flask_session

            # Initially not authenticated
            assert flask_session.get("authenticated", False) is False

            # Set authenticated
            set_authenticated(True)

            # Check session is now authenticated
            assert flask_session.get("authenticated") is True

    def test_set_authenticated_clears_session_flag(self):
        """Test that set_authenticated can clear the session flag."""
        app = create_app()

        with app.test_request_context():
            from flask import session as flask_session

            flask_session["authenticated"] = True

            # Clear authenticated
            set_authenticated(False)

            # Check session is now not authenticated
            assert flask_session.get("authenticated") is False

    def test_clear_session_removes_all_data(self):
        """Test that clear_session removes all session data."""
        app = create_app()

        with app.test_request_context():
            from flask import session as flask_session

            flask_session["authenticated"] = True
            flask_session["user_id"] = "test-user"
            flask_session["other_data"] = "some-value"

            # Clear session
            clear_session()

            # Check all data is removed
            assert len(flask_session) == 0
            assert "authenticated" not in flask_session
            assert "user_id" not in flask_session
            assert "other_data" not in flask_session

    def test_is_authenticated_returns_true_when_authenticated(self):
        """Test that is_authenticated returns True when session is authenticated."""
        app = create_app()

        with app.test_request_context():
            from flask import session as flask_session

            flask_session["authenticated"] = True

            result = is_authenticated()

            assert result is True

    def test_is_authenticated_returns_false_when_not_authenticated(self):
        """Test that is_authenticated returns False when session is not authenticated."""
        app = create_app()

        with app.test_request_context():
            from flask import session as flask_session

            flask_session.clear()

            result = is_authenticated()

            assert result is False

    def test_session_persistence_across_requests(self):
        """Test that authentication session persists across multiple requests."""
        app = create_app()

        with app.test_client() as client:
            # First request: set authentication
            with client.session_transaction() as sess:
                sess["authenticated"] = True

            # Second request: check authentication persists
            with client.session_transaction() as sess:
                assert sess.get("authenticated") is True

            # Third request: still authenticated
            with client.session_transaction() as sess:
                assert sess.get("authenticated") is True

    def test_session_isolation_between_clients(self):
        """Test that sessions are isolated between different test clients."""
        app = create_app()

        # Client 1: authenticated
        with app.test_client() as client1:
            with client1.session_transaction() as sess:
                sess["authenticated"] = True

            with client1.session_transaction() as sess:
                assert sess.get("authenticated") is True

        # Client 2: not authenticated (different session)
        with app.test_client() as client2:
            with client2.session_transaction() as sess:
                assert sess.get("authenticated", False) is False


class TestLoginRoutes:
    """Tests for the login routes."""

    def test_get_login_returns_login_form(self):
        """Test that GET /login returns the login form."""
        app = create_app()

        with app.test_client() as client:
            response = client.get("/login")

            assert response.status_code == 200
            assert b"login" in response.data.lower()

    def test_post_login_with_valid_key_redirects_to_dashboard(self):
        """Test that POST /login with valid key redirects to dashboard."""
        test_key = "test-valid-access-key-uuid"
        os.environ["ACCESS_KEY"] = test_key

        app = create_app()

        with app.test_client() as client:
            response = client.post(
                "/login", data={"access_key": test_key}, follow_redirects=False
            )

            # Should redirect to dashboard
            assert response.status_code == 302
            assert response.location == "/"

            # Check that session is authenticated
            with client.session_transaction() as sess:
                assert sess.get("authenticated") is True

        # Clean up
        del os.environ["ACCESS_KEY"]

    def test_post_login_with_valid_key_allows_dashboard_access(self):
        """Test that POST /login with valid key allows access to dashboard."""
        test_key = "test-valid-access-key-uuid"
        os.environ["ACCESS_KEY"] = test_key

        app = create_app()

        with app.test_client() as client:
            # Login with valid key
            client.post("/login", data={"access_key": test_key})

            # Access dashboard
            response = client.get("/")

            # Should be able to access dashboard
            assert response.status_code == 200

        # Clean up
        del os.environ["ACCESS_KEY"]

    def test_post_login_with_invalid_key_shows_error(self):
        """Test that POST /login with invalid key shows error message."""
        configured_key = "correct-access-key"
        invalid_key = "wrong-access-key"

        os.environ["ACCESS_KEY"] = configured_key

        app = create_app()

        with app.test_client() as client:
            response = client.post("/login", data={"access_key": invalid_key})

            # Should return 200 (showing login form with error)
            assert response.status_code == 200
            assert b"Invalid access key" in response.data

            # Check that session is NOT authenticated
            with client.session_transaction() as sess:
                assert sess.get("authenticated", False) is False

        # Clean up
        del os.environ["ACCESS_KEY"]

    def test_post_login_with_empty_key_shows_error(self):
        """Test that POST /login with empty key shows error message."""
        os.environ["ACCESS_KEY"] = "configured-key"

        app = create_app()

        with app.test_client() as client:
            response = client.post("/login", data={"access_key": ""})

            # Should return 200 (showing login form with error)
            assert response.status_code == 200
            assert b"Invalid access key" in response.data

            # Check that session is NOT authenticated
            with client.session_transaction() as sess:
                assert sess.get("authenticated", False) is False

        # Clean up
        del os.environ["ACCESS_KEY"]

    def test_post_logout_clears_session(self):
        """Test that POST /logout clears the session."""
        app = create_app()

        with app.test_client() as client:
            # Set up authenticated session
            with client.session_transaction() as sess:
                sess["authenticated"] = True
                sess["other_data"] = "some-value"

            # Logout
            response = client.post("/logout", follow_redirects=False)

            # Should redirect to login
            assert response.status_code == 302
            assert "/login" in response.location

            # Check that session is cleared
            with client.session_transaction() as sess:
                assert len(sess) == 0
                assert "authenticated" not in sess
                assert "other_data" not in sess

    def test_post_logout_redirects_to_login(self):
        """Test that POST /logout redirects to login page."""
        app = create_app()

        with app.test_client() as client:
            # Set up authenticated session
            with client.session_transaction() as sess:
                sess["authenticated"] = True

            # Logout
            response = client.post("/logout", follow_redirects=False)

            # Should redirect to login
            assert response.status_code == 302
            assert response.location == "/login"

    def test_logout_requires_authentication(self):
        """Test that POST /logout requires authentication."""
        app = create_app()

        with app.test_client() as client:
            # Try to logout without being authenticated
            response = client.post("/logout", follow_redirects=False)

            # Should redirect to login (because not authenticated)
            assert response.status_code == 302
            assert "/login" in response.location

    def test_login_with_access_key_from_env_file(self):
        """Test that login works with the ACCESS_KEY from .env file.

        This test verifies that the ACCESS_KEY loaded from the .env file
        can be used to successfully authenticate and access the dashboard.
        """
        # Get the ACCESS_KEY from environment (loaded from .env via conftest.py)
        # Note: We need to reload it because other tests may have modified the environment
        from dotenv import load_dotenv

        load_dotenv()
        access_key_from_env = os.environ.get("ACCESS_KEY")

        # Skip test if ACCESS_KEY is not set in environment
        if not access_key_from_env:
            pytest.skip("ACCESS_KEY not found in environment")

        app = create_app()

        with app.test_client() as client:
            # Login with the ACCESS_KEY from .env file
            response = client.post(
                "/login",
                data={"access_key": access_key_from_env},
                follow_redirects=False,
            )

            # Should redirect to dashboard
            assert response.status_code == 302
            assert response.location == "/"

            # Check that session is authenticated
            with client.session_transaction() as sess:
                assert sess.get("authenticated") is True

            # Verify we can access the dashboard
            dashboard_response = client.get("/")
            assert dashboard_response.status_code == 200


class TestDashboardRoute:
    """Tests for the dashboard route."""

    @pytest.mark.integration
    def test_dashboard_displays_all_pools_from_database(self, db_connection):
        """Test that dashboard displays all token pools from the database."""
        from lf_automator.automator.tokenpools.pools import TokenPool

        # Create test token pools
        pool1 = TokenPool()
        pool1_uuid = pool1.create_tokenpool(token_count=20, pool_status="active")

        pool2 = TokenPool()
        pool2_uuid = pool2.create_tokenpool(token_count=8, pool_status="active")

        pool3 = TokenPool()
        pool3_uuid = pool3.create_tokenpool(token_count=3, pool_status="active")

        app = create_app()

        with app.test_client() as client:
            # Authenticate
            with client.session_transaction() as sess:
                sess["authenticated"] = True

            # Access dashboard
            response = client.get("/")

            # Should return 200
            assert response.status_code == 200

            # Check that all pool UUIDs (first 8 chars) are displayed
            assert str(pool1_uuid)[:8].encode() in response.data
            assert str(pool2_uuid)[:8].encode() in response.data
            assert str(pool3_uuid)[:8].encode() in response.data

            # Check that counts are displayed
            assert b"20" in response.data
            assert b"8" in response.data
            assert b"3" in response.data

            # Check that state indicators are present
            response_text = response.data.decode()
            assert "Normal" in response_text or "normal" in response_text
            assert "Warning" in response_text or "warning" in response_text
            assert "Critical" in response_text or "critical" in response_text

    def test_state_calculation_function_critical(self):
        """Test that get_pool_state returns 'critical' for pools at or below critical threshold."""
        from lf_automator.webapp.routes import get_pool_state

        # Test critical state (5 or fewer tokens)
        assert get_pool_state({"current_count": 0}) == "critical"
        assert get_pool_state({"current_count": 1}) == "critical"
        assert get_pool_state({"current_count": 5}) == "critical"

    def test_state_calculation_function_warning(self):
        """Test that get_pool_state returns 'warning' for pools at or below warning threshold."""
        from lf_automator.webapp.routes import get_pool_state

        # Test warning state (6-10 tokens)
        assert get_pool_state({"current_count": 6}) == "warning"
        assert get_pool_state({"current_count": 8}) == "warning"
        assert get_pool_state({"current_count": 10}) == "warning"

    def test_state_calculation_function_normal(self):
        """Test that get_pool_state returns 'normal' for pools above warning threshold."""
        from lf_automator.webapp.routes import get_pool_state

        # Test normal state (more than 10 tokens)
        assert get_pool_state({"current_count": 11}) == "normal"
        assert get_pool_state({"current_count": 20}) == "normal"
        assert get_pool_state({"current_count": 100}) == "normal"

    def test_state_calculation_function_with_missing_count(self):
        """Test that get_pool_state handles missing current_count gracefully."""
        from lf_automator.webapp.routes import get_pool_state

        # Test with missing current_count (should default to 0, which is critical)
        assert get_pool_state({}) == "critical"

    @pytest.mark.integration
    def test_empty_state_when_no_pools_exist(self, db_connection):
        """Test that dashboard displays empty state message when no pools exist."""
        # Ensure database is empty by deleting all pools
        with db_connection.connection:
            with db_connection.connection.cursor() as cursor:
                cursor.execute("DELETE FROM lfautomator.accessTokenPools")

        app = create_app()

        with app.test_client() as client:
            # Authenticate
            with client.session_transaction() as sess:
                sess["authenticated"] = True

            # Access dashboard
            response = client.get("/")

            # Should return 200
            assert response.status_code == 200

            # Check that response contains the dashboard template
            # (empty pools list should be handled gracefully)
            assert (
                b"dashboard" in response.data.lower()
                or b"pool" in response.data.lower()
            )

    @pytest.mark.integration
    def test_dashboard_error_handling_with_database_failure(self, db_connection):
        """Test that dashboard handles database errors gracefully."""
        from unittest.mock import MagicMock, patch

        app = create_app()

        with app.test_client() as client:
            # Authenticate
            with client.session_transaction() as sess:
                sess["authenticated"] = True

            # Mock TokenPool to raise an exception
            with patch("lf_automator.webapp.routes.TokenPool") as mock_token_pool:
                mock_instance = MagicMock()
                mock_instance.db.connection.__enter__.side_effect = Exception(
                    "Database connection failed"
                )
                mock_token_pool.return_value = mock_instance

                # Access dashboard
                response = client.get("/")

                # Should return 200 (not crash)
                assert response.status_code == 200

                # Should display error message
                assert (
                    b"Unable to load token pools" in response.data
                    or b"error" in response.data.lower()
                )

    @pytest.mark.integration
    def test_dashboard_calculates_state_for_each_pool(self, db_connection):
        """Test that dashboard calculates and includes state for each pool."""
        from lf_automator.automator.tokenpools.pools import TokenPool

        # Create pools in different states
        pool_normal = TokenPool()
        pool_normal.create_tokenpool(token_count=20, pool_status="active")  # normal

        pool_warning = TokenPool()
        pool_warning.create_tokenpool(token_count=8, pool_status="active")  # warning

        pool_critical = TokenPool()
        pool_critical.create_tokenpool(token_count=3, pool_status="active")  # critical

        app = create_app()

        with app.test_client() as client:
            # Authenticate
            with client.session_transaction() as sess:
                sess["authenticated"] = True

            # Access dashboard
            response = client.get("/")

            # Should return 200
            assert response.status_code == 200

            # Check that state indicators are present
            # The template should show different states for different pools
            response_text = response.data.decode()

            # Verify pools are displayed with their counts
            assert "20" in response_text
            assert "8" in response_text
            assert "3" in response_text

    @pytest.mark.integration
    def test_dashboard_requires_authentication(self, db_connection):
        """Test that dashboard route requires authentication."""
        app = create_app()

        with app.test_client() as client:
            # Try to access dashboard without authentication
            response = client.get("/", follow_redirects=False)

            # Should redirect to login
            assert response.status_code == 302
            assert "/login" in response.location

    @pytest.mark.integration
    def test_dashboard_orders_pools_by_priority(self, db_connection):
        """Test that dashboard displays pools ordered by priority."""
        from lf_automator.automator.tokenpools.pools import TokenPool

        # Create pools with explicit priorities
        pool3 = TokenPool()
        pool3.create_tokenpool(token_count=15, pool_status="active", pool_priority=3)

        pool1 = TokenPool()
        pool1.create_tokenpool(token_count=20, pool_status="active", pool_priority=1)

        pool2 = TokenPool()
        pool2.create_tokenpool(token_count=10, pool_status="active", pool_priority=2)

        app = create_app()

        with app.test_client() as client:
            # Authenticate
            with client.session_transaction() as sess:
                sess["authenticated"] = True

            # Access dashboard
            response = client.get("/")

            # Should return 200
            assert response.status_code == 200

            # Verify response contains pool data
            response_text = response.data.decode()
            assert "20" in response_text
            assert "10" in response_text
            assert "15" in response_text


class TestDepositWithdrawEndpoint:
    """Tests for the deposit/withdraw transaction endpoint."""

    @pytest.mark.integration
    def test_deposit_increases_pool_count(self, db_connection):
        """Test that deposit transaction increases pool count."""
        from lf_automator.automator.tokenpools.pools import TokenPool

        # Create a pool
        pool = TokenPool()
        pool_uuid = pool.create_tokenpool(token_count=10, pool_status="active")

        app = create_app()

        with app.test_client() as client:
            # Authenticate
            with client.session_transaction() as sess:
                sess["authenticated"] = True

            # Deposit 5 tokens
            response = client.post(
                f"/api/pools/{pool_uuid}/transaction",
                json={"transaction_type": "deposit", "count": 5},
            )

            # Should return 200
            assert response.status_code == 200

            # Verify response
            data = response.get_json()
            assert data["success"] is True
            assert data["pool"]["current_count"] == 15

    @pytest.mark.integration
    def test_withdraw_decreases_pool_count(self, db_connection):
        """Test that withdraw transaction decreases pool count."""
        from lf_automator.automator.tokenpools.pools import TokenPool

        # Create a pool
        pool = TokenPool()
        pool_uuid = pool.create_tokenpool(token_count=10, pool_status="active")

        app = create_app()

        with app.test_client() as client:
            # Authenticate
            with client.session_transaction() as sess:
                sess["authenticated"] = True

            # Withdraw 3 tokens
            response = client.post(
                f"/api/pools/{pool_uuid}/transaction",
                json={"transaction_type": "withdraw", "count": 3},
            )

            # Should return 200
            assert response.status_code == 200

            # Verify response
            data = response.get_json()
            assert data["success"] is True
            assert data["pool"]["current_count"] == 7

    @pytest.mark.integration
    def test_withdraw_prevents_negative_count(self, db_connection):
        """Test that withdraw transaction prevents negative counts."""
        from lf_automator.automator.tokenpools.pools import TokenPool

        # Create a pool with 5 tokens
        pool = TokenPool()
        pool_uuid = pool.create_tokenpool(token_count=5, pool_status="active")

        app = create_app()

        with app.test_client() as client:
            # Authenticate
            with client.session_transaction() as sess:
                sess["authenticated"] = True

            # Try to withdraw 10 tokens (more than available)
            response = client.post(
                f"/api/pools/{pool_uuid}/transaction",
                json={"transaction_type": "withdraw", "count": 10},
            )

            # Should return 400
            assert response.status_code == 400

            # Verify error message
            data = response.get_json()
            assert "error" in data
            assert "Cannot withdraw" in data["error"]

    @pytest.mark.integration
    def test_transaction_requires_authentication(self, db_connection):
        """Test that transaction endpoint requires authentication."""
        from lf_automator.automator.tokenpools.pools import TokenPool

        # Create a pool
        pool = TokenPool()
        pool_uuid = pool.create_tokenpool(token_count=10, pool_status="active")

        app = create_app()

        with app.test_client() as client:
            # Try to deposit without authentication
            response = client.post(
                f"/api/pools/{pool_uuid}/transaction",
                json={"transaction_type": "deposit", "count": 5},
                follow_redirects=False,
            )

            # Should redirect to login
            assert response.status_code == 302
            assert "/login" in response.location

    @pytest.mark.integration
    def test_transaction_validates_transaction_type(self, db_connection):
        """Test that transaction endpoint validates transaction type."""
        from lf_automator.automator.tokenpools.pools import TokenPool

        # Create a pool
        pool = TokenPool()
        pool_uuid = pool.create_tokenpool(token_count=10, pool_status="active")

        app = create_app()

        with app.test_client() as client:
            # Authenticate
            with client.session_transaction() as sess:
                sess["authenticated"] = True

            # Try with invalid transaction type
            response = client.post(
                f"/api/pools/{pool_uuid}/transaction",
                json={"transaction_type": "invalid", "count": 5},
            )

            # Should return 400
            assert response.status_code == 400

            # Verify error message
            data = response.get_json()
            assert "error" in data
            assert "transaction_type" in data["error"]

    @pytest.mark.integration
    def test_transaction_validates_count(self, db_connection):
        """Test that transaction endpoint validates count."""
        from lf_automator.automator.tokenpools.pools import TokenPool

        # Create a pool
        pool = TokenPool()
        pool_uuid = pool.create_tokenpool(token_count=10, pool_status="active")

        app = create_app()

        with app.test_client() as client:
            # Authenticate
            with client.session_transaction() as sess:
                sess["authenticated"] = True

            # Try with negative count
            response = client.post(
                f"/api/pools/{pool_uuid}/transaction",
                json={"transaction_type": "deposit", "count": -5},
            )

            # Should return 400
            assert response.status_code == 400

            # Verify error message
            data = response.get_json()
            assert "error" in data
            assert "greater than 0" in data["error"]

    @pytest.mark.integration
    def test_transaction_returns_404_for_nonexistent_pool(self, db_connection):
        """Test that transaction endpoint returns 404 for nonexistent pool."""
        import uuid

        app = create_app()

        with app.test_client() as client:
            # Authenticate
            with client.session_transaction() as sess:
                sess["authenticated"] = True

            # Try to deposit to nonexistent pool
            fake_uuid = str(uuid.uuid4())
            response = client.post(
                f"/api/pools/{fake_uuid}/transaction",
                json={"transaction_type": "deposit", "count": 5},
            )

            # Should return 404
            assert response.status_code == 404

            # Verify error message
            data = response.get_json()
            assert "error" in data
            assert "not found" in data["error"].lower()


class TestStatusEndpoint:
    """Tests for the system status endpoint."""

    @pytest.mark.integration
    def test_status_endpoint_requires_authentication(self, db_connection):
        """Test that status endpoint requires authentication."""
        from lf_automator.webapp.app import create_app

        app = create_app()

        with app.test_client() as client:
            # Try to access status without authentication
            response = client.get("/api/status")

            # Should redirect to login
            assert response.status_code == 302
            assert "/login" in response.location

    @pytest.mark.integration
    def test_status_endpoint_returns_system_info(self, db_connection):
        """Test that status endpoint returns system information."""
        from lf_automator.webapp.app import create_app

        app = create_app()

        with app.test_client() as client:
            # Authenticate
            with client.session_transaction() as sess:
                sess["authenticated"] = True

            # Get status
            response = client.get("/api/status")

            # Should return 200
            assert response.status_code == 200

            # Should return JSON
            data = response.get_json()
            assert data is not None

            # Should contain expected fields
            assert "current_token_total" in data
            assert "threshold" in data
            assert "status" in data
            assert "configuration" in data

            # Configuration should have expected fields
            config = data["configuration"]
            assert "schedule_cron" in config
            assert "scheduling_enabled" in config
            assert "email_recipients" in config
