"""MemberTokenSync component for synchronizing member token data from Foreninglet API."""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

from lf_automator.automator.tokenregistry.registry import TokenRegistry
from foreninglet_data.api import ForeningLet
from foreninglet_data.memberlist import Memberlist

logger = logging.getLogger(__name__)


class MemberTokenSync:
    """Synchronizes member token data from the Foreninglet API."""

    def __init__(
        self,
        api_client: Optional[ForeningLet] = None,
        registry: Optional[TokenRegistry] = None,
        max_retries: int = 5,
        initial_backoff: float = 1.0,
    ):
        """Initialize with API client and token registry.

        Args:
            api_client: ForeningLet API client instance. If None, creates a new one.
            registry: TokenRegistry instance. If None, creates a new one.
            max_retries: Maximum number of retry attempts for API failures
            initial_backoff: Initial backoff time in seconds for exponential backoff
        """
        self.api_client = api_client if api_client is not None else ForeningLet()
        self.registry = registry if registry is not None else TokenRegistry()
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff

    def fetch_members_with_tokens(self) -> List[Dict]:
        """Fetch all members from API who have token numbers assigned.

        Uses exponential backoff retry logic for API failures.

        Returns:
            List of dicts with member_uuid and token_number

        Raises:
            RuntimeError: If API request fails after all retries
        """
        retries = 0
        backoff = self.initial_backoff

        while retries < self.max_retries:
            try:
                # Fetch member list from API
                memberlist_data = self.api_client.get_memberlist()
                memberlist = Memberlist(memberlist_data)

                # Extract members with token numbers
                members_with_tokens = []
                for member in memberlist.memberlist:
                    token_number = self._extract_token_number(member)
                    if token_number:
                        member_uuid = member.get("MemberUuid")
                        if member_uuid:
                            members_with_tokens.append(
                                {
                                    "member_uuid": member_uuid,
                                    "token_number": token_number,
                                }
                            )

                logger.info(
                    f"Successfully fetched {len(members_with_tokens)} members with tokens"
                )
                return members_with_tokens

            except Exception as error:
                retries += 1
                if retries >= self.max_retries:
                    logger.error(
                        f"Failed to fetch members after {self.max_retries} retries: {error}"
                    )
                    raise RuntimeError(
                        f"API request failed after {self.max_retries} retries: {error}"
                    )

                logger.warning(
                    f"API request failed (attempt {retries}/{self.max_retries}), "
                    f"retrying in {backoff}s: {error}"
                )
                time.sleep(backoff)
                backoff *= 2  # Exponential backoff

        raise RuntimeError("Unexpected error in retry logic")

    def _extract_token_number(self, member: Dict) -> Optional[str]:
        """Extract and validate token number from member data.

        Args:
            member: Member dictionary from API

        Returns:
            Token number string if valid, None otherwise
        """
        token_field = member.get("MemberField3")

        # Filter out empty, null, or whitespace-only values
        if not token_field or not str(token_field).strip():
            return None

        # Validate token number format (basic validation)
        token_str = str(token_field).strip()
        if self._is_valid_token_number(token_str):
            return token_str

        logger.warning(f"Invalid token number format: {token_str}")
        return None

    def _is_valid_token_number(self, token_number: str) -> bool:
        """Validate token number format.

        Args:
            token_number: Token number string to validate

        Returns:
            True if valid, False otherwise
        """
        # Basic validation: non-empty string with reasonable length
        # Can be extended with more specific validation rules
        if not token_number or len(token_number) == 0:
            return False
        if len(token_number) > 50:  # Max length from database schema
            return False
        return True

    def sync_to_registry(self) -> int:
        """Sync current API state to registry.

        Fetches all members with tokens from API and registers them in the registry.

        Returns:
            Count of new registrations (not updates)

        Raises:
            RuntimeError: If API fetch fails
            ValueError: If registry operations fail
        """
        members_with_tokens = self.fetch_members_with_tokens()

        new_registrations = 0
        for member in members_with_tokens:
            try:
                is_new = self.registry.register_member_token(
                    member["member_uuid"], member["token_number"]
                )
                if is_new:
                    new_registrations += 1
            except ValueError as error:
                logger.error(
                    f"Failed to register member {member['member_uuid']}: {error}"
                )
                # Continue with other members even if one fails
                continue

        logger.info(
            f"Sync complete: {new_registrations} new registrations, "
            f"{len(members_with_tokens) - new_registrations} updates"
        )
        return new_registrations

    def get_new_assignments_since(self, timestamp: datetime) -> List[Dict]:
        """Get members with new token assignments since timestamp.

        Args:
            timestamp: Datetime to filter by

        Returns:
            List of dicts with member_uuid, token_number, registered_at, updated_at

        Raises:
            ValueError: If registry query fails
        """
        return self.registry.get_members_registered_since(timestamp)
