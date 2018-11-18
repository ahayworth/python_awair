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
            "uuid": self._quote(uuid),
            "fahrenheit": self._quote(fahrenheit),
        }

        return (yield from self._query(const.LATEST_QUERY % self._query_variables(variables),
                                       variables))['AirDataLatest']['airDataSeq']


    @asyncio.coroutine
    def air_data_five_minute(self, uuid, **kwargs):
        """Returns the 5min summary air quality measurements."""
        # args from_date, to_date, limit, desc, fahrenheit)
        variables = {
            "uuid": self._quote(uuid),
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
            "uuid": self._quote(uuid),
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
            "uuid": self._quote(uuid),
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
            text = yield from resp.text()
            if resp.status != 200:
                raise Exception(text)

            return (yield from resp.json())['data']

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
