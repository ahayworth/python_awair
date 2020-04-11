"""Wrapper class to query the Awair API."""

from typing import NoReturn

from aiohttp import ClientSession, ClientResponse

from python_awair.auth import AwairAuth
from python_awair.exceptions import (
    AuthError,
    AwairError,
    NotFoundError,
    QueryError,
    RatelimitError,
)


class AwairClient:
    """Python asyncio client for the Awair GraphQL API."""

    def __init__(
        self, authenticator: AwairAuth, session: ClientSession,
    ) -> None:
        """Initialize an AwairClient with sensible defaults."""
        self.__authenticator = authenticator
        self.__session = session

    async def query(self, url: str) -> dict:
        """Query the Awair api, and handle errors."""
        headers = await self.__headers()
        async with self.__session.get(url, headers=headers) as resp:
            if resp.status != 200:
                self.__handle_non_200_error(resp)

            json = await resp.json()
            self.__check_errors_array(json)

            return json

    async def __headers(self) -> dict:
        """Return headers to set on the API request."""
        token = await self.__authenticator.get_bearer_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def __check_errors_array(json: dict) -> None:
        """Check for an "errors" array and process it.

        Holdover from the GraphQL API, unclear if we could still get messages like this.
        """
        if "errors" in json:
            messages = []
            for error in json["errors"]:
                if "Too many requests" in error["message"]:
                    raise RatelimitError()

                messages.append(error.get("message", "Unknown error"))

            if messages:
                raise AwairError(", ".join(messages))

    @staticmethod
    def __handle_non_200_error(resp: ClientResponse) -> NoReturn:
        if resp.status == 400:
            raise QueryError()

        if resp.status == 401 or resp.status == 403:
            raise AuthError()

        if resp.status == 404:
            raise NotFoundError()

        if resp.status == 429:
            raise RatelimitError()

        raise AwairError()
