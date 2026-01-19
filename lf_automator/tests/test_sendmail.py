"""Tests for sending emails"""

from unittest.mock import patch

import pytest
from automator.mailer.send import Mailer
from dotenv import load_dotenv

load_dotenv()


@pytest.mark.integration
def test_sending_email():
    """Test sending an email."""
    mailer = Mailer(
        sender="carsten@lejre.fitness", subject="Test email from LF Automator"
    )

    assert (
        mailer.send_email(
            "Tester lige mailafsendelse fra LF Automator", to_email="carsten@simcax.dk"
        )
        == 0
    )


def test_sending_email_with_mock():
    """Test sending an email."""
    mailer = Mailer(
        sender="someone@example.com", subject="Test email from LF Automator"
    )
    with patch("automator.mailer.send.SendGridAPIClient") as mock:
        assert (
            mailer.send_email(
                "Tester lige mailafsendelse fra LF Automator",
                to_email="someoneelse@example.com",
            )
            == 0
        )
        mock.assert_called_once()
