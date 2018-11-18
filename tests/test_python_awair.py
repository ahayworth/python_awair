import aiohttp
import asyncio
import pytest
from aioresponses import aioresponses
from python_awair import AwairClient
from python_awair import const

loop = asyncio.get_event_loop()

user_response = '''{"data":{"User":{"id":"12345","email":"test@test.com","name":{"firstName":"Test","lastName":"Test"},"dob":{"year":2018,"month":11,"day":11},"sex":"MALE","tier":"Hobbyist","permissions":[{"scope":"FIFTEEN_MIN","quota":100}],"usage":[{"scope":"LATEST","counts":9}]}}}'''
latest_response = '''{"data":{"AirDataLatest":{"airDataSeq":[{"timestamp":"2018-11-18T01:09:48.187Z","score":69.0,"sensors":[{"component":"TEMP","value":26.66}],"indices":[{"component":"TEMP","value":1.0}]}]}}}'''

def test_get_user():
    awair = AwairClient('example_token')
    with aioresponses() as mocked:
        mocked.post(const.AWAIR_URL, status=200, body=user_response)

        resp = loop.run_until_complete(awair.get_user())
        name = dict(firstName="Test", lastName="Test")
        dob = dict(year=2018, month=11, day=11)

        # It's a big response, just assert some things
        assert resp["id"] == '12345'
        assert resp["email"] == "test@test.com"
        assert resp["name"]["lastName"] == "Test"
        assert resp["dob"]["day"] == 11
        assert resp["tier"] == "Hobbyist"
        assert resp["permissions"][0] == dict(scope="FIFTEEN_MIN", quota=100)
        assert resp["usage"][0] == dict(scope="LATEST", counts=9)

def test_get_user_with_session():
    session = aiohttp.ClientSession()
    awair = AwairClient('example_token', session=session)
    with aioresponses() as mocked:
        mocked.post(const.AWAIR_URL, status=200, body=user_response)

        resp = loop.run_until_complete(awair.get_user())

        # It's a big response, just assert some things
        assert resp["id"] == '12345'
        assert resp["email"] == "test@test.com"
        assert resp["name"]["lastName"] == "Test"
        assert resp["dob"]["day"] == 11
        assert resp["tier"] == "Hobbyist"
        assert resp["permissions"][0] == dict(scope="FIFTEEN_MIN", quota=100)
        assert resp["usage"][0] == dict(scope="LATEST", counts=9)

def test_get_latest():
    awair = AwairClient('example_token')
    with aioresponses() as mocked:
        mocked.post(const.AWAIR_URL, status=200, body=latest_response)

        resp = loop.run_until_complete(awair.get_latest("test_device"))
        assert resp[0]['timestamp'] == '2018-11-18T01:09:48.187Z'
        assert resp[0]['score'] == 69.0
        assert resp[0]['sensors'][0]['component'] == 'TEMP'
        assert resp[0]['sensors'][0]['value'] == 26.66
        assert resp[0]['indices'][0]['component'] == 'TEMP'
        assert resp[0]['indices'][0]['value'] == 1.0
