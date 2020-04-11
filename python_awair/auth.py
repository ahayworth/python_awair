"""Authentication constructs for the Awair API."""

from abc import ABC, abstractmethod


class AwairAuth(ABC):
    """Abstract authentication that provides a Bearer token."""

    @abstractmethod
    async def get_bearer_token(self) -> str:
        """Return a valid bearer token for authentication."""


class AccessTokenAuth(AwairAuth):
    """Authentication that uses an Awair access token."""

    def __init__(self, access_token: str) -> None:
        """Initialize and save off our acces token."""
        self.access_token = access_token
        super().__init__()

    async def get_bearer_token(self) -> str:
        """Return the access token for authentication."""
        return self.access_token
