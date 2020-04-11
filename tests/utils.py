"""Test utilities."""

from python_awair.auth import AwairAuth


class SillyAuth(AwairAuth):
    """Testing auth class."""

    def __init__(self, access_token: str) -> None:
        """Store our access token."""
        self.access_token = access_token

    async def get_bearer_token(self) -> str:
        """Return the access_token."""
        return self.access_token
