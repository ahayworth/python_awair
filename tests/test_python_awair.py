"""Test basic python_awair functionality."""

import os
import re
from collections import namedtuple

import aiohttp
import pytest
import vcr
from aioresponses import aioresponses

from python_awair import AwairClient, const

ACCESS_TOKEN = os.environ.get("AWAIR_ACCESS_TOKEN", "abcdefg")
AWAIR_GEN1_UUID = "awair_24947"

Scrubber = namedtuple("Scrubber", ["pattern", "replacement"])
SCRUBBERS = [
    Scrubber(pattern=r'"email":"[^"]+"', replacement='"email":"foo@bar.com"'),
    Scrubber(pattern=r'"year":\d+', replacement='"year":2020'),
    Scrubber(pattern=r'"month":\d+', replacement='"month":4'),
    Scrubber(pattern=r'"day":\d+', replacement='"day":8'),
    Scrubber(pattern=r'"latitude":-?\d+\.\d+', replacement='"latitude":0.0'),
    Scrubber(pattern=r'"longitude":-?\d+\.\d+', replacement='"longitude":0.0'),
]


def scrub(response):
    """Scrub sensitive data."""
    body = response["body"]["string"].decode("utf-8")
    for scrubber in SCRUBBERS:
        body = re.sub(scrubber.pattern, scrubber.replacement, body)

    response["body"]["string"] = body.encode("utf-8")
    return response


VCR = vcr.VCR(
    cassette_library_dir="tests/fixtures/cassettes",
    record_mode="none",
    filter_headers=[("authorization", "fake_token")],
    decode_compressed_response=True,
    before_record_response=scrub,
)


@pytest.fixture
def mock_ratelimit_response():
    """Returns a mocked user query."""
    with aioresponses() as mocked:
        with open("tests/fixtures/ratelimit_response.json") as data:
            mocked.post(const.AWAIR_URL, status=200, body=data.read())
            yield mocked


async def test_get_user():
    """Test that we can get a user response."""
    with VCR.use_cassette("user.yaml"):
        awair = AwairClient(ACCESS_TOKEN)
        resp = await awair.user()

    assert resp["id"] == "32406"
    assert resp["email"] == "foo@bar.com"
    assert resp["name"]["firstName"] == "Andrew"
    assert resp["dob"]["day"] == 8
    assert resp["tier"] == "Large_developer"
    assert dict(scope="FIFTEEN_MIN", quota=30000) in resp["permissions"]
    assert dict(scope="USER_INFO", counts=10) in resp["usage"]


async def test_get_user_with_session():
    """Test that we can get a user response with an explicit session."""
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("user.yaml"):
            awair = AwairClient(ACCESS_TOKEN, session=session)
            resp = await awair.user()

    assert resp["id"] == "32406"
    assert resp["email"] == "foo@bar.com"
    assert resp["name"]["firstName"] == "Andrew"
    assert resp["dob"]["day"] == 8
    assert resp["tier"] == "Large_developer"
    assert dict(scope="FIFTEEN_MIN", quota=30000) in resp["permissions"]
    assert dict(scope="USER_INFO", counts=10) in resp["usage"]


async def test_get_devices():
    """Test that we can get a list of devices."""
    with VCR.use_cassette("devices.yaml"):
        awair = AwairClient(ACCESS_TOKEN)
        resp = await awair.devices()

    assert resp[0]["uuid"] == AWAIR_GEN1_UUID
    assert resp[0]["deviceType"] == "awair"


async def test_get_latest():
    """Test that we can get the latest air data."""
    with VCR.use_cassette("latest.yaml"):
        awair = AwairClient(ACCESS_TOKEN)
        resp = await awair.air_data_latest(AWAIR_GEN1_UUID)

    assert resp[0]["timestamp"] == "2020-04-08T22:59:29.884Z"
    assert resp[0]["score"] == 84.0
    assert dict(component="TEMP", value=24.75) in resp[0]["sensors"]
    assert dict(component="TEMP", value=0.0) in resp[0]["indices"]


async def test_get_five_minute():
    """Test that we can get the five-minute avg air data."""
    with VCR.use_cassette("five_minute.yaml"):
        awair = AwairClient(ACCESS_TOKEN)
        resp = await awair.air_data_five_minute(
            AWAIR_GEN1_UUID, from_date="2020-04-08T22:59:29.884Z",
        )

    assert resp[0]["timestamp"] == "2020-04-08T23:00:00.000Z"
    assert resp[0]["score"] == 84.76666666666667
    assert dict(component="TEMP", value=24.666666666666668) in resp[0]["sensors"]
    assert dict(component="TEMP", value=0.0) in resp[0]["indices"]


async def test_get_fifteen_minute():
    """Test that we can get the fifteen-minute avg air data."""
    with VCR.use_cassette("fifteen_minute.yaml"):
        awair = AwairClient(ACCESS_TOKEN)
        resp = await awair.air_data_fifteen_minute(
            AWAIR_GEN1_UUID, from_date="2020-04-08T22:59:29.884Z"
        )

    assert resp[0]["timestamp"] == "2020-04-08T23:00:00.000Z"
    assert resp[0]["score"] == 84.70786516853933
    assert resp[0]["sensors"][0]["component"] == "TEMP"
    assert resp[0]["sensors"][0]["value"] == 24.64910108587715
    assert resp[0]["indices"][0]["component"] == "TEMP"
    assert resp[0]["indices"][0]["value"] == 0.0


async def test_get_raw():
    """Test that we can get the raw air data."""
    with VCR.use_cassette("raw.yaml"):
        awair = AwairClient(ACCESS_TOKEN)
        resp = await awair.air_data_raw(
            AWAIR_GEN1_UUID, from_date="2020-04-08T22:59:29.884Z"
        )

    assert resp[0]["timestamp"] == "2020-04-08T22:59:29.884Z"
    assert resp[0]["score"] == 84.0
    assert resp[0]["sensors"][0]["component"] == "TEMP"
    assert resp[0]["sensors"][0]["value"] == 24.75
    assert resp[0]["indices"][0]["component"] == "TEMP"
    assert resp[0]["indices"][0]["value"] == 0.0


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
    mock_ratelimit_response,
):  # pylint: disable=unused-argument,redefined-outer-name
    """Test that we can raise ratelimit."""
    awair = AwairClient("bad_token")

    with pytest.raises(AwairClient.RatelimitError):
        resp = await awair.air_data_raw("test_device")
        assert resp.code == 200
