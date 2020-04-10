"""Wrapper class to query the Awair API."""

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

        if resp.status == 200:
            if "errors" in json:
                errors = json["errors"]

                ratelimit = False
                for error in errors:
                    if "Too many requests" in error["message"]:
                        ratelimit = True
                        break

                if ratelimit:
                    raise AwairClient.RatelimitError(
                        "The ratelimit for the Awair API has been exceeded. "
                        + "Please try again later."
                    )

            return json

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
