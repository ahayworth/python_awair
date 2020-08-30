"""Python asyncio client for the Awair REST API.

This module is an object-oriented wrapper around the Awair_
REST API_. It requires an access token (which can be obtained
from the `developer console`_) and implements read-only access
to the "user" portions of the API.

.. _Awair: https://getawair.com
.. _API: https://docs.developer.getawair.com/?version=latest
.. _`developer console`: https://developer.getawair.com
"""

from asyncio import gather
from typing import List, Optional

from aiohttp import ClientSession

from python_awair import const
from python_awair.auth import AccessTokenAuth, AwairAuth
from python_awair.client import AwairClient
from python_awair.devices import AwairLocalDevice
from python_awair.exceptions import AwairError
from python_awair.user import AwairUser


class Awair:
    """Entry class for the Awair API.

    Args:
        session: An aiohttp session that will be used to query
            the Awair API.
        access_token: An optional access token, obtained from
            the Awair developer console, used to authenticate
            to the Awair API.
        authenticator: An optional instance of an AwairAuth class,
            which can provide an HTTP Bearer token for
            authentication. Most users will simply provide an
            access_token, instead.
    """

    client: AwairClient
    """AwairClient: The instantiated AwairClient
        that will be used to fetch API responses and
        check for HTTP errors.
    """

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
        """Return the current AwairUser.

        The Awair "user" API does not provide a way to query for
        a specific user, so this method always returns the user
        that is associated with the authentication that is in-use.
        This is *typically* the user that owns the access_token
        that was provided at class instantiaton, unless you have
        provided an authenticator class implementing some other
        stategy (perhaps OAuth).
        """
        response = await self.client.query(const.USER_URL)
        return AwairUser(client=self.client, attributes=response)


class AwairLocal:
    """Entry class for the local sensors Awair API."""

    client: AwairClient
    """AwairClient: The instantiated AwairClient
        that will be used to fetch API responses and
        check for HTTP errors.
    """

    _device_addrs: List[str]
    """IP or DNS addresses of Awair devices with the local sensors API enabled."""

    def __init__(self, session: ClientSession, device_addrs: List[str]) -> None:
        """Initialize the Awair local sensors API wrapper."""
        self._device_addrs = device_addrs
        if len(device_addrs) > 0:
            self.client = AwairClient(AccessTokenAuth(""), session)
        else:
            raise AwairError("No local Awair device addresses supplied!")

    async def devices(self) -> List[AwairLocalDevice]:
        """Return a list of local awair devices."""
        responses = await gather(
            *(
                self.client.query(f"http://{addr}/settings/config/data")
                for addr in self._device_addrs
            )
        )
        return [
            AwairLocalDevice(
                client=self.client, device_addr=self._device_addrs[i], attributes=device
            )
            for i, device in enumerate(responses)
        ]
