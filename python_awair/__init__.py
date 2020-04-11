"""Python asyncio client for the Awair GraphQL API."""


from typing import Optional

from aiohttp import ClientSession

from python_awair import const
from python_awair.auth import AccessTokenAuth, AwairAuth
from python_awair.client import AwairClient
from python_awair.exceptions import AwairError
from python_awair.user import AwairUser


class Awair:
    """Base class for the Awair API."""

    client: AwairClient

    def __init__(
        self,
        session: ClientSession,
        access_token: Optional[str] = None,
        authenticator: Optional[AwairAuth] = None,
    ) -> None:
        """Initialize the Awair API wrapper."""
        if authenticator:
            self.client = AwairClient(authenticator, session)
        elif access_token:
            self.client = AwairClient(AccessTokenAuth(access_token), session)
        else:
            raise AwairError("No authentication supplied!")

    async def user(self) -> AwairUser:
        """Yield user data."""
        response = await self.client.query(const.USER_URL)
        return AwairUser(client=self.client, attributes=response)
