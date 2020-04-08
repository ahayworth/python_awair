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
        response = await self._query(const.USER_QUERY)
        return response["User"]

    async def devices(self):
        """List devices and locations."""
        response = await self._query(const.DEVICE_QUERY)
        return response["Devices"]["devices"]

    async def air_data_latest(self, uuid, fahrenheit=False):
        """Return the latest air quality measurements."""
        variables = {
            "deviceUUID": self._quote(uuid),
            "fahrenheit": self._quote(fahrenheit),
        }

        response = await self._query(
            const.LATEST_QUERY % self._query_variables(variables), variables
        )
        return response["AirDataLatest"]["airDataSeq"]

    async def air_data_five_minute(self, uuid, **kwargs):
        """Return the 5min summary air quality measurements."""
        # args from_date, to_date, limit, desc, fahrenheit)
        variables = {
            "deviceUUID": self._quote(uuid),
        }

        for key, value in kwargs.items():
            if key == 'from_date':
                key = 'from'

            variables[key] = self._quote(value)

        response = await self._query(
            const.FIVE_MIN_QUERY % self._query_variables(variables), variables
        )
        return response["AirData5Minute"]["airDataSeq"]

    async def air_data_fifteen_minute(self, uuid, **kwargs):
        """Return the 15min summary air quality measurements."""
        # args from_date, to_date, limit, desc, fahrenheit)
        variables = {
            "deviceUUID": self._quote(uuid),
        }

        for key, value in kwargs.items():
            if key == 'from_date':
                key = 'from'

            variables[key] = self._quote(value)

        response = await self._query(
            const.FIFTEEN_MIN_QUERY % self._query_variables(variables), variables
        )
        return response["AirData15Minute"]["airDataSeq"]

    async def air_data_raw(self, uuid, **kwargs):
        """Return raw air quality measurements."""
        # args from_date, to_date, limit, desc, fahrenheit)
        variables = {
            "deviceUUID": self._quote(uuid),
        }

        for key, value in kwargs.items():
            if key == 'from_date':
                key = 'from'

            variables[key] = self._quote(value)

        response = await self._query(
            const.RAW_QUERY % self._query_variables(variables), variables
        )
        return response["AirDataRaw"]["airDataSeq"]

    async def _query(self, query, variables=None):
        data = {"query": "query { %s }" % query, "variables": variables}

        if self._session is None:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    const.AWAIR_URL,
                    json=data,
                    headers=self._headers,
                    timeout=self._timeout,
                ) as resp:
                    if resp.status == 200:
                        json = await resp.json()
        else:
            async with self._session.post(
                const.AWAIR_URL, json=data, headers=self._headers, timeout=self._timeout
            ) as resp:
                if resp.status == 200:
                    json = await resp.json()

        if resp.status == 200:
            data = json["data"]

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

            return data

        if resp.status == 400:
            raise AwairClient.QueryError(
                "The query %s with variables %s is invalid." % (query, variables)
            )

        if resp.status == 401:
            raise AwairClient.AuthError(
                "The supplied access token is invalid or "
                + "does not have access to the requested data."
            )

        if resp.status == 404:
            raise AwairClient.NotFoundError(
                "The Awair API returned an unexpected HTTP 404."
            )

        raise AwairClient.GenericError("Unable to query the Awair API.")

    @staticmethod
    def _quote(arg):
        if isinstance(arg, bool):
            if arg:
                return "true"

            return "false"

        if isinstance(arg, str):
            return '"%s"' % arg

        return arg

    @staticmethod
    def _query_variables(variables):
        return ",".join(["%s: %s" % (k, v) for (k, v) in variables.items()])

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
