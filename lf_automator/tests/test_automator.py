"""Tests for the Automator class."""

import random

import pytest
from lf_automator.automator.automation import Automator
from dotenv import load_dotenv
from foreninglet_data.api import ForeningLet
from foreninglet_data.memberlist import Memberlist

load_dotenv()


def test_automator():
    """Test the Automator class."""
    automator = Automator()
    assert automator is not None
    assert automator.run() == 0


def test_get_current_token_count():
    """Test the get_current_token_count method."""
    automator = Automator()
    rand_count = random.randint(0, 100)
    automator.current_token_count = rand_count
    assert automator.get_current_token_count() == rand_count


def test_alert_below_threshold():
    """Test the alert_below_threshold method."""
    automator = Automator()
    automator.current_token_count = 5
    assert automator.alert_below_threshold()
    automator.current_token_count = 25
    assert automator.alert_below_threshold() is False
    automator.current_token_count = 30
    assert automator.alert_below_threshold() is False


def test_adding_tokens():
    """Test adding tokens to the current token count."""
    automator = Automator()
    automator.current_token_count = 5
    automator.add_tokens(10)
    assert automator.current_token_count == 15
    automator.add_tokens(10)
    assert automator.current_token_count == 25
    automator.add_tokens(10)
    assert automator.current_token_count == 35


@pytest.mark.integration
def test_find_token_field_on_member():
    """Test finding the token field on a member."""
    fl_obj = ForeningLet()
    memberlist = fl_obj.get_memberlist()
    memberlist_obj = Memberlist(memberlist)
    for member in memberlist_obj.memberlist:
        token_field = member.get("MemberField3")
        assert token_field is not None
        # Just assert one member having the field
        break
