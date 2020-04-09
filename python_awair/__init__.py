"""Python asyncio client for the Awair GraphQL API."""


import aiohttp

from python_awair import const


class AwairClient:
    """Python asyncio client for the Awair GraphQL API."""

    def __init__(
        self, access_token, session=None, timeout=aiohttp.client.DEFAULT_TIMEOUT
    ):
        """Initialize an AwairClient with sensible defaults."""
        self._headers = {
            "Authorization": "Bearer %s" % access_token,
            "Content-Type": "application/json",
        }

        self._timeout = timeout
        self._session = session

    async def user(self):
        """Yield user data."""
        response = await self._query(const.USER_URL)
        return response

    async def devices(self):
        """List devices and locations."""
        response = await self._query(const.DEVICE_URL)
        return response.get('devices', [])

    async def air_data_latest(self, type, id, fahrenheit=False):
        """Return the latest air quality measurements."""
        url = f"{const.DEVICE_URL}/{type}/{id}/air-data/latest?fahrenheit={str(fahrenheit).lower()}"
        response = await self._query(url)
        return response.get('data', [{}])[0]

    async def air_data_five_minute(self, type, id, **kwargs):
        """Return the 5min summary air quality measurements."""
        # args from_date, to_date, limit, desc, fahrenheit)
        url = f"{const.DEVICE_URL}/{type}/{id}/air-data/5-min-avg"
        if kwargs is not None:
            url += "?"

            for key, value in kwargs.items():
                if key == "from_date":
                    key = "from"
                    value = str(value).lower()

                elif key == "to_date":
                    key = "to"
                    value = str(value).lower()

                url += f"&{key}={value}"

        response = await self._query(url)
        return response.get('data', [])

    async def air_data_fifteen_minute(self, type, id, **kwargs):
        """Return the 15min summary air quality measurements."""
        # args from_date, to_date, limit, desc, fahrenheit)
        url = f"{const.DEVICE_URL}/{type}/{id}/air-data/15-min-avg"
        if kwargs is not None:
            url += "?"

            for key, value in kwargs.items():
                if key == "from_date":
                    key = "from"
                    value = str(value).lower()

                elif key == "to_date":
                    key = "to"
                    value = str(value).lower()

                url += f"&{key}={value}"

        response = await self._query(url)
        return response.get('data', [])

    async def air_data_raw(self, type, id, **kwargs):
        """Return the 5min summary air quality measurements."""
        # args from_date, to_date, limit, desc, fahrenheit)
        url = f"{const.DEVICE_URL}/{type}/{id}/air-data/raw"
        if kwargs is not None:
            url += "?"

            for key, value in kwargs.items():
                if key == "from_date":
                    key = "from"
                    value = str(value).lower()

                elif key == "to_date":
                    key = "to"
                    value = str(value).lower()

                url += f"&{key}={value}"

        response = await self._query(url)
        return response.get('data', [])

    async def _query(self, url, variables=None):
        if self._session is None:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    headers=self._headers,
                    timeout=self._timeout,
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
            raise AwairClient.QueryError(
                "The supplied parameters were invalid."
            )

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
