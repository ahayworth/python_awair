"""Wrapper class to query the Awair API."""

from typing import NoReturn

import aiohttp


class AwairClient:
    """Python asyncio client for the Awair GraphQL API."""

    def __init__(
        self, access_token, session=None, timeout=aiohttp.client.DEFAULT_TIMEOUT
    ) -> None:
        """Initialize an AwairClient with sensible defaults."""
        self._headers = {
            "Authorization": "Bearer %s" % access_token,
            "Content-Type": "application/json",
        }

        self._timeout = timeout
        self._session = session

    # TODO: refactor, too many branches.
    async def query(self, url: str) -> dict:
        """Query the Awair api, and handle errors."""
        if self._session is None:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=self._headers, timeout=self._timeout,
                ) as resp:
                    if resp.status == 200:
                        json = await resp.json()
        else:
            async with self._session.get(
                url, headers=self._headers, timeout=self._timeout
            ) as resp:
                if resp.status == 200:
                    json = await resp.json()

        if resp.status != 200:
            self.__handle_error(resp)

        return self.__check_200_errors(json)

    @staticmethod
    def __check_200_errors(json: dict) -> dict:
        """Check for an "errors" array and process it.

        Holdover from the GraphQL API, unclear if we could still get messages like this.
        """
        if "errors" in json:
            messages = []
            for error in json["errors"]:
                if "Too many requests" in error["message"]:
                    raise AwairClient.RatelimitError(
                        "The ratelimit for the Awair API has been exceeded. "
                        + "Please try again later."
                    )

                messages.append(error.get("message", "Unknown error"))

            if messages:
                raise AwairClient.GenericError(
                    f"Error querying the Awair API: {messages}"
                )

        return json

    @staticmethod
    def __handle_error(resp: aiohttp.ClientResponse) -> NoReturn:
        if resp.status == 400:
            raise AwairClient.QueryError("The supplied parameters were invalid.")

        if resp.status == 401 or resp.status == 403:
            raise AwairClient.AuthError(
                "The supplied access token is invalid or "
                + "does not have access to the requested data."
            )

        if resp.status == 404:
            raise AwairClient.NotFoundError(
                "The Awair API returned an unexpected HTTP 404."
            )

        if resp.status == 429:
            raise AwairClient.RatelimitError(
                "The ratelimit for the Awair API has been exceeded. "
                + "Please try again later."
            )

        raise AwairClient.GenericError("Unable to query the Awair API.")

    # TODO: break out into top-level exceptions
    class GenericError(Exception):
        """Generic error."""

    class AuthError(Exception):
        """Some kind of authorization or authentication failure."""

    class QueryError(Exception):
        """The query was somehow malformed."""

    class NotFoundError(Exception):
        """The requested endpoint is gone."""

    class RatelimitError(Exception):
        """The API quota was exceeded."""
