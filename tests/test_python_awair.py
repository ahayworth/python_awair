"""Test basic python_awair functionality."""

import os
import re
from collections import namedtuple
from unittest.mock import patch

import aiohttp
import pytest
import vcr
from aioresponses import aioresponses

from python_awair import AwairClient, const

ACCESS_TOKEN = os.environ.get("AWAIR_ACCESS_TOKEN", "abcdefg")
AWAIR_GEN1_TYPE = "awair"
AWAIR_GEN1_ID = 24947

Scrubber = namedtuple("Scrubber", ["pattern", "replacement"])
SCRUBBERS = [
    Scrubber(pattern=r'"email":"[^"]+"', replacement='"email":"foo@bar.com"'),
    Scrubber(pattern=r'"dobYear":\d+', replacement='"dobYear":2020'),
    Scrubber(pattern=r'"dobMonth":\d+', replacement='"dobMonth":4'),
    Scrubber(pattern=r'"dobDay":\d+', replacement='"dobDay":8'),
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


async def test_get_user():
    """Test that we can get a user response."""
    with VCR.use_cassette("user.yaml"):
        awair = AwairClient(ACCESS_TOKEN)
        resp = await awair.user()

    assert resp["id"] == "32406"
    assert resp["email"] == "foo@bar.com"
    assert resp["firstName"] == "Andrew"
    assert resp["dobDay"] == 8
    assert resp["tier"] == "Large_developer"
    assert dict(scope="FIFTEEN_MIN", quota=30000) in resp["permissions"]
    assert dict(scope="USER_INFO", usage=27) in resp["usages"]


async def test_get_user_with_session():
    """Test that we can get a user response with an explicit session."""
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("user.yaml"):
            awair = AwairClient(ACCESS_TOKEN, session=session)
            resp = await awair.user()

    assert resp["id"] == "32406"
    assert resp["email"] == "foo@bar.com"
    assert resp["firstName"] == "Andrew"
    assert resp["dobDay"] == 8
    assert resp["tier"] == "Large_developer"
    assert dict(scope="FIFTEEN_MIN", quota=30000) in resp["permissions"]
    assert dict(scope="USER_INFO", usage=27) in resp["usages"]


async def test_get_devices():
    """Test that we can get a list of devices."""
    with VCR.use_cassette("devices.yaml"):
        awair = AwairClient(ACCESS_TOKEN)
        resp = await awair.devices()

    assert resp[0]["deviceId"] == AWAIR_GEN1_ID
    assert resp[0]["deviceType"] == "awair"


async def test_get_latest():
    """Test that we can get the latest air data."""
    with VCR.use_cassette("latest.yaml"):
        awair = AwairClient(ACCESS_TOKEN)
        resp = await awair.air_data_latest(AWAIR_GEN1_TYPE, AWAIR_GEN1_ID)

    assert resp["timestamp"] == "2020-04-09T04:13:15.356Z"
    assert resp["score"] == 88.0
    assert dict(comp="temp", value=24.420000076293945) in resp["sensors"]
    assert dict(comp="temp", value=0.0) in resp["indices"]


async def test_get_five_minute():
    """Test that we can get the five-minute avg air data."""
    with VCR.use_cassette("five_minute.yaml"):
        awair = AwairClient(ACCESS_TOKEN)
        resp = await awair.air_data_five_minute(
            AWAIR_GEN1_TYPE, AWAIR_GEN1_ID, from_date="2020-04-08T22:59:29.884Z",
        )

    assert resp[0]["timestamp"] == "2020-04-09T04:10:00.000Z"
    assert resp[0]["score"] == 88.0
    assert dict(comp="temp", value=24.443000411987306) in resp[0]["sensors"]
    assert dict(comp="temp", value=0.0) in resp[0]["indices"]


async def test_get_fifteen_minute():
    """Test that we can get the fifteen-minute avg air data."""
    with VCR.use_cassette("fifteen_minute.yaml"):
        awair = AwairClient(ACCESS_TOKEN)
        resp = await awair.air_data_fifteen_minute(
            AWAIR_GEN1_TYPE, AWAIR_GEN1_ID, from_date="2020-04-08T22:59:29.884Z"
        )

    assert resp[0]["timestamp"] == "2020-04-09T04:00:00.000Z"
    assert resp[0]["score"] == 88.0
    assert resp[0]["sensors"][0]["comp"] == "temp"
    assert resp[0]["sensors"][0]["value"] == 24.499499988555907
    assert resp[0]["indices"][0]["comp"] == "temp"
    assert resp[0]["indices"][0]["value"] == 0.0


async def test_get_raw():
    """Test that we can get the raw air data."""
    with VCR.use_cassette("raw.yaml"):
        awair = AwairClient(ACCESS_TOKEN)
        resp = await awair.air_data_raw(
            AWAIR_GEN1_TYPE, AWAIR_GEN1_ID, from_date="2020-04-08T22:59:29.884Z"
        )

    assert resp[0]["timestamp"] == "2020-04-09T04:13:15.356Z"
    assert resp[0]["score"] == 88.0
    assert resp[0]["sensors"][0]["comp"] == "temp"
    assert resp[0]["sensors"][0]["value"] == 24.420000076293945
    assert resp[0]["indices"][0]["comp"] == "temp"
    assert resp[0]["indices"][0]["value"] == 0.0


async def test_auth_failure():
    """Test that we can raise on bad auth."""
    with VCR.use_cassette("bad_auth.yaml"):
        awair = AwairClient("bad")
        with pytest.raises(AwairClient.AuthError):
            await awair.air_data_raw(AWAIR_GEN1_TYPE, AWAIR_GEN1_ID)

        awair = AwairClient(ACCESS_TOKEN)
        with pytest.raises(AwairClient.AuthError):
            await awair.air_data_raw(AWAIR_GEN1_TYPE, AWAIR_GEN1_ID + 1)


async def test_bad_query():
    """Test that we can raise on bad query."""
    with VCR.use_cassette("bad_params.yaml"):
        awair = AwairClient(ACCESS_TOKEN)
        with pytest.raises(AwairClient.QueryError):
            await awair.air_data_raw(AWAIR_GEN1_TYPE, AWAIR_GEN1_ID, fahrenheit=451)


async def test_not_found():
    """Test that we can raise on 404."""
    with VCR.use_cassette("not_found.yaml"):
        awair = AwairClient(ACCESS_TOKEN)
        with patch("python_awair.const.DEVICE_URL", f"{const.USER_URL}/devicesxyz"):
            with pytest.raises(AwairClient.NotFoundError):
                await awair.air_data_raw(AWAIR_GEN1_TYPE, AWAIR_GEN1_ID)
