"""Python asyncio client for the Awair GraphQL API."""

import asyncio
import aiohttp
import async_timeout
from python_awair import const

class AwairClient():
    """Python asyncio client for the Awair GraphQL API."""
    def __init__(self, access_token, session=None,
                 timeout=aiohttp.client.DEFAULT_TIMEOUT):
        self._headers = {"Authorization": "Bearer %s" % access_token,
                         "Content-Type": "application/json"}

        self._timeout = timeout
        if session is None:
            self._session = aiohttp.ClientSession()
        else:
            self._session = session

    @asyncio.coroutine
    def user(self):
        """Yields user data."""
        return (yield from self._query(const.USER_QUERY))['User']

    @asyncio.coroutine
    def devices(self):
        """Lists devices and locations."""
        return (yield from self._query(const.DEVICE_QUERY))['Devices']['devices']

    @asyncio.coroutine
    def air_data_latest(self, uuid, fahrenheit=False):
        """Returns the latest air quality measurements."""
        variables = {
            "deviceUUID": self._quote(uuid),
            "fahrenheit": self._quote(fahrenheit),
        }

        return (yield from self._query(const.LATEST_QUERY % self._query_variables(variables),
                                       variables))['AirDataLatest']['airDataSeq']


    @asyncio.coroutine
    def air_data_five_minute(self, uuid, **kwargs):
        """Returns the 5min summary air quality measurements."""
        # args from_date, to_date, limit, desc, fahrenheit)
        variables = {
            "deviceUUID": self._quote(uuid),
        }

        for key, value in kwargs.items():
            variables[key] = self._quote(value)

        return (yield from self._query(const.FIVE_MIN_QUERY % self._query_variables(variables),
                                       variables))['AirData5Minute']['airDataSeq']


    @asyncio.coroutine
    def air_data_fifteen_minute(self, uuid, **kwargs):
        """Returns the 15min summary air quality measurements."""
        # args from_date, to_date, limit, desc, fahrenheit)
        variables = {
            "deviceUUID": self._quote(uuid),
        }

        for key, value in kwargs.items():
            variables[key] = self._quote(value)

        return (yield from self._query(const.FIFTEEN_MIN_QUERY % self._query_variables(variables),
                                       variables))['AirData15Minute']['airDataSeq']


    @asyncio.coroutine
    def air_data_raw(self, uuid, **kwargs):
        """Returns raw air quality measurements."""
        # args from_date, to_date, limit, desc, fahrenheit)
        variables = {
            "deviceUUID": self._quote(uuid),
        }

        for key, value in kwargs.items():
            variables[key] = self._quote(value)

        return (yield from self._query(const.RAW_QUERY % self._query_variables(variables),
                                       variables))['AirDataRaw']['airDataSeq']


    @asyncio.coroutine
    def _query(self, query, variables=None):
        data = {"query": "query { %s }" % query, "variables": variables}
        with async_timeout.timeout(self._timeout.total):
            resp = yield from self._session.post(const.AWAIR_URL, json=data, headers=self._headers)
            if resp.status == 400:
                raise AwairClient.QueryError(
                    "The query %s with variables %s is invalid." % (
                        query, variables
                    )
                )
            elif resp.status == 401:
                raise AwairClient.AuthError(
                    "The supplied access token is invalid or " +
                    "does not have access to the requested data."
                )
            elif resp.status == 404:
                raise AwairClient.NotFoundError(
                    "The Awair API returned an unexpected HTTP 404."
                )

            if resp.status == 200:
                json = yield from resp.json()
                data = json['data']

                if 'errors' in json:
                    errors = json['errors']

                    ratelimit = False
                    for error in errors:
                        if "Too many requests" in error['message']:
                            ratelimit = True
                            break

                    if ratelimit:
                        raise AwairClient.RatelimitError(
                            "The ratelimit for the Awair API has been exceeded. " +
                            "Please try again later."
                        )

                return data

            return AwairClient.GenericError("Unable to query the Awair API.")

    @staticmethod
    def _quote(arg):
        if isinstance(arg, bool):
            if arg:
                return "true"

            return "false"

        if isinstance(arg, str):
            return "\"%s\"" % arg

        return arg

    @staticmethod
    def _query_variables(variables):
        return ",".join(["%s: %s" % (k, v) for (k, v) in variables.items()])


    class GenericError(Exception):
        """Generic error."""
        pass


    class AuthError(Exception):
        """Some kind of authorization or authentication failure."""
        pass


    class QueryError(Exception):
        """The query was somehow malformed."""
        pass


    class NotFoundError(Exception):
        """The requested endpoint is gone."""
        pass


    class RatelimitError(Exception):
        """The API quota was exceeded."""
        pass
