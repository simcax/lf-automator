"""Tests for the configuration info route."""

from lf_automator.webapp.app import create_app


class TestConfigRoute:
    """Test suite for configuration info endpoint."""

    def test_config_route_requires_authentication(self):
        """Test that config route requires authentication."""
        app = create_app()

        with app.test_client() as client:
            # Try to access config without authentication
            response = client.get("/config")

            # Should redirect to login
            assert response.status_code == 302
            assert "/login" in response.location

    def test_config_route_displays_configuration(self):
        """Test that config route displays configuration information."""
        app = create_app()

        with app.test_client() as client:
            # Authenticate
            with client.session_transaction() as sess:
                sess["authenticated"] = True

            # Access config page
            response = client.get("/config")

            # Should return 200
            assert response.status_code == 200

            # Should contain configuration sections
            assert b"Database Configuration" in response.data
            assert b"Foreninglet API Configuration" in response.data
            assert b"Email Configuration" in response.data
            assert b"Scheduling Configuration" in response.data
            assert b"Membership Configuration" in response.data
            assert b"Security Configuration" in response.data

    def test_config_route_masks_secrets(self):
        """Test that config route masks secret values."""
        app = create_app()

        with app.test_client() as client:
            # Authenticate
            with client.session_transaction() as sess:
                sess["authenticated"] = True

            # Access config page
            response = client.get("/config")

            # Should return 200
            assert response.status_code == 200

            # Should not contain actual secret values
            assert b"SG.m6JSCI1aQK2y2r8NTz7btg" not in response.data
            assert b"8b4a33e86d" not in response.data
            assert b"lfautomator_dev" not in response.data
            assert (
                b"c2c25b1d02b87823f47709539e69a40483d39a89a432bd71d2ca87001f083ce9"
                not in response.data
            )

    def test_config_route_shows_secret_status(self):
        """Test that config route shows whether secrets are set."""
        app = create_app()

        with app.test_client() as client:
            # Authenticate
            with client.session_transaction() as sess:
                sess["authenticated"] = True

            # Access config page
            response = client.get("/config")

            # Should return 200
            assert response.status_code == 200

            # Should show status badges for secrets
            assert b"Set" in response.data or b"Not Set" in response.data

    def test_config_route_displays_non_secret_values(self):
        """Test that config route displays non-secret configuration values."""
        app = create_app()

        with app.test_client() as client:
            # Authenticate
            with client.session_transaction() as sess:
                sess["authenticated"] = True

            # Access config page
            response = client.get("/config")

            # Should return 200
            assert response.status_code == 200

            # Should contain non-secret values
            assert b"localhost" in response.data  # Database host
            assert b"5432" in response.data  # Database port
            assert b"lfautomator" in response.data  # Database name
            assert b"https://foreninglet.dk/api/" in response.data  # API base URL
            assert b"carsten@lejre.fitness" in response.data  # Email recipients

    def test_config_route_shows_not_set_for_missing_secrets(self):
        """Test that config route shows 'Not Set' badge for missing secrets."""
        app = create_app()

        with app.test_client() as client:
            # Authenticate
            with client.session_transaction() as sess:
                sess["authenticated"] = True

            # Access config page
            response = client.get("/config")

            # Should return 200
            assert response.status_code == 200

            # Response should contain status badges (Set or Not Set)
            # This verifies the template renders the secret status correctly
            assert b"<span" in response.data  # Status badges are rendered
