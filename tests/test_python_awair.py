"""Test basic python_awair functionality."""
import asyncio

import aiohttp
import pytest
from aioresponses import aioresponses

from python_awair import AwairClient, const

@pytest.fixture
def mock_user_response():
    """Returns a mocked user query."""
    with aioresponses() as mocked:
        with open("tests/fixtures/user_response.json") as data:
            mocked.post(const.AWAIR_URL, status=200, body=data.read())
            yield mocked


@pytest.fixture
def mock_devices_response():
    """Returns a mocked user query."""
    with aioresponses() as mocked:
        with open("tests/fixtures/devices_response.json") as data:
            mocked.post(const.AWAIR_URL, status=200, body=data.read())
            yield mocked


@pytest.fixture
def mock_latest_response():
    """Returns a mocked user query."""
    with aioresponses() as mocked:
        with open("tests/fixtures/latest_response.json") as data:
            mocked.post(const.AWAIR_URL, status=200, body=data.read())
            yield mocked


@pytest.fixture
def mock_five_minute_response():
    """Returns a mocked user query."""
    with aioresponses() as mocked:
        with open("tests/fixtures/five_minute_response.json") as data:
            mocked.post(const.AWAIR_URL, status=200, body=data.read())
            yield mocked


@pytest.fixture
def mock_fifteen_minute_response():
    """Returns a mocked user query."""
    with aioresponses() as mocked:
        with open("tests/fixtures/fifteen_minute_response.json") as data:
            mocked.post(const.AWAIR_URL, status=200, body=data.read())
            yield mocked


@pytest.fixture
def mock_raw_response():
    """Returns a mocked user query."""
    with aioresponses() as mocked:
        with open("tests/fixtures/raw_response.json") as data:
            mocked.post(const.AWAIR_URL, status=200, body=data.read())
            yield mocked


@pytest.fixture
def mock_ratelimit_response():
    """Returns a mocked user query."""
    with aioresponses() as mocked:
        with open("tests/fixtures/ratelimit_response.json") as data:
            mocked.post(const.AWAIR_URL, status=200, body=data.read())
            yield mocked


async def test_get_user(
    mock_user_response,
):  # pylint: disable=unused-argument,redefined-outer-name
    """Test that we can get a user response."""
    awair = AwairClient("example_token")
    resp = await awair.user()

    assert resp["id"] == "12345"
    assert resp["email"] == "test@test.com"
    assert resp["name"]["lastName"] == "Test"
    assert resp["dob"]["day"] == 11
    assert resp["tier"] == "Hobbyist"
    assert resp["permissions"][0] == dict(scope="FIFTEEN_MIN", quota=100)
    assert resp["usage"][0] == dict(scope="LATEST", counts=9)


async def test_get_user_with_session(
    mock_user_response
):  # pylint: disable=unused-argument,redefined-outer-name
    """Test that we can get a user response with an explicit session."""
    session = aiohttp.ClientSession()
    awair = AwairClient("example_token", session=session)
    resp = await awair.user()

    # It's a big response, just assert some things
    assert resp["id"] == "12345"
    assert resp["email"] == "test@test.com"
    assert resp["name"]["lastName"] == "Test"
    assert resp["dob"]["day"] == 11
    assert resp["tier"] == "Hobbyist"
    assert resp["permissions"][0] == dict(scope="FIFTEEN_MIN", quota=100)
    assert resp["usage"][0] == dict(scope="LATEST", counts=9)


async def test_get_devices(
    mock_devices_response
):  # pylint: disable=unused-argument,redefined-outer-name
    """Test that we can get a list of devices."""
    awair = AwairClient("example_token")
    resp = await awair.devices()

    assert resp[0]["uuid"] == "awair_12345"
    assert resp[0]["deviceType"] == "awair"


async def test_get_latest(
    mock_latest_response
):  # pylint: disable=unused-argument,redefined-outer-name
    """Test that we can get the latest air data."""
    awair = AwairClient("example_token")
    resp = await awair.air_data_latest("test_device")
    assert resp[0]["timestamp"] == "2018-11-18T01:09:48.187Z"
    assert resp[0]["score"] == 69.0
    assert resp[0]["sensors"][0]["component"] == "TEMP"
    assert resp[0]["sensors"][0]["value"] == 26.66
    assert resp[0]["indices"][0]["component"] == "TEMP"
    assert resp[0]["indices"][0]["value"] == 1.0


async def test_get_five_minute(
    mock_five_minute_response
):  # pylint: disable=unused-argument,redefined-outer-name
    """Test that we can get the five-minute avg air data."""
    awair = AwairClient("example_token")
    resp = await awair.air_data_five_minute("test_device")
    assert resp[0]["timestamp"] == "2018-11-18T01:09:48.187Z"
    assert resp[0]["score"] == 69.0
    assert resp[0]["sensors"][0]["component"] == "TEMP"
    assert resp[0]["sensors"][0]["value"] == 26.66
    assert resp[0]["indices"][0]["component"] == "TEMP"
    assert resp[0]["indices"][0]["value"] == 1.0


async def test_get_fifteen_minute(
    mock_fifteen_minute_response
):  # pylint: disable=unused-argument,redefined-outer-name
    """Test that we can get the fifteen-minute avg air data."""
    awair = AwairClient("example_token")
    resp = await awair.air_data_fifteen_minute("test_device")
    assert resp[0]["timestamp"] == "2018-11-18T01:09:48.187Z"
    assert resp[0]["score"] == 69.0
    assert resp[0]["sensors"][0]["component"] == "TEMP"
    assert resp[0]["sensors"][0]["value"] == 26.66
    assert resp[0]["indices"][0]["component"] == "TEMP"
    assert resp[0]["indices"][0]["value"] == 1.0


async def test_get_raw(
    mock_raw_response
):  # pylint: disable=unused-argument,redefined-outer-name
    """Test that we can get the raw air data."""
    awair = AwairClient("example_token")
    resp = await awair.air_data_raw("test_device")
    assert resp[0]["timestamp"] == "2018-11-18T01:09:48.187Z"
    assert resp[0]["score"] == 69.0
    assert resp[0]["sensors"][0]["component"] == "TEMP"
    assert resp[0]["sensors"][0]["value"] == 26.66
    assert resp[0]["indices"][0]["component"] == "TEMP"
    assert resp[0]["indices"][0]["value"] == 1.0


async def test_auth_failure():
    """Test that we can raise on bad auth."""
    awair = AwairClient("bad_token")
    with aioresponses() as mocked:
        mocked.post(
            const.AWAIR_URL, status=401, body="The supplied authentication is invalid"
        )

        with pytest.raises(AwairClient.AuthError):
            resp = await awair.air_data_raw("test_device")
            assert resp.code == 401
            assert resp.body == "The supplied authentication is invalid"


async def test_bad_query():
    """Test that we can raise on bad query."""
    awair = AwairClient("bad_token")
    with aioresponses() as mocked:
        mocked.post(const.AWAIR_URL, status=400)

        with pytest.raises(AwairClient.QueryError):
            resp = await awair.air_data_raw("test_device")
            assert resp.code == 400


async def test_not_found():
    """Test that we can raise on 404."""
    awair = AwairClient("bad_token")
    with aioresponses() as mocked:
        mocked.post(const.AWAIR_URL, status=404)

        with pytest.raises(AwairClient.NotFoundError):
            resp = await awair.air_data_raw("test_device")
            assert resp.code == 404


async def test_ratelimit(
    mock_ratelimit_response
):  # pylint: disable=unused-argument,redefined-outer-name
    """Test that we can raise ratelimit."""
    awair = AwairClient("bad_token")

    with pytest.raises(AwairClient.RatelimitError):
        resp = await awair.air_data_raw("test_device")
        assert resp.code == 200
