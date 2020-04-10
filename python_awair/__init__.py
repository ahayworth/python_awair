"""Python asyncio client for the Awair GraphQL API."""


import aiohttp

from python_awair import const
from python_awair.client import AwairClient
from python_awair.user import AwairUser


class Awair:
    """Base class for the Awair API."""

    client: AwairClient

    def __init__(
        self, access_token, session=None, timeout=aiohttp.client.DEFAULT_TIMEOUT
    ) -> None:
        """Initialize the Awair API wrapper."""
        self.client = AwairClient(access_token, session, timeout)

    async def user(self) -> AwairUser:
        """Yield user data."""
        response = await self.client.query(const.USER_URL)
        return AwairUser(client=self.client, attributes=response)
