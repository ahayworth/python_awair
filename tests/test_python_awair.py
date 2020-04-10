"""Test basic python_awair functionality."""

import os
import re
from collections import namedtuple
from datetime import date, datetime, timedelta
from unittest.mock import patch

import aiohttp
import pytest
import vcr
from aioresponses import aioresponses

from python_awair import Awair, const
from python_awair.client import AwairClient
from python_awair.devices import AwairDevice
from python_awair.user import AwairUser

ACCESS_TOKEN = os.environ.get("AWAIR_ACCESS_TOKEN", "abcdefg")

AWAIR_GEN1_TYPE = "awair"
AWAIR_GEN1_ID = 24947
MOCK_GEN1_DEVICE_ATTRS = {
    "deviceId": AWAIR_GEN1_ID,
    "deviceType": AWAIR_GEN1_TYPE,
    "deviceUUID": f"{AWAIR_GEN1_TYPE}_{AWAIR_GEN1_ID}",
}
MOCK_USER_ATTRS = {"id": "32406"}


def mock_awair_user(client: AwairClient) -> AwairUser:
    """Return a mock awair user."""
    return AwairUser(client=client, attributes=MOCK_USER_ATTRS)


def mock_awair_device(client: AwairClient) -> AwairDevice:
    """Return a mock awair device."""
    return AwairDevice(client=client, attributes=MOCK_GEN1_DEVICE_ATTRS)


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
        awair = Awair(ACCESS_TOKEN)
        user = await awair.user()

    assert user.user_id == "32406"
    assert user.email == "foo@bar.com"
    assert user.first_name == "Andrew"
    assert user.dob == date(year=2020, month=4, day=8)
    assert user.tier == "Large_developer"
    assert user.permissions["FIFTEEN_MIN"] == 30000
    assert user.usages["USER_INFO"] == 80


async def test_get_user_with_session():
    """Test that we can get a user response with an explicit session."""
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("user.yaml"):
            awair = Awair(ACCESS_TOKEN, session=session)
            user = await awair.user()

    assert user.user_id == "32406"
    assert user.email == "foo@bar.com"
    assert user.first_name == "Andrew"
    assert user.dob == date(year=2020, month=4, day=8)
    assert user.tier == "Large_developer"
    assert user.permissions["FIFTEEN_MIN"] == 30000
    assert user.usages["USER_INFO"] == 80


async def test_get_devices():
    """Test that we can get a list of devices."""
    with VCR.use_cassette("devices.yaml"):
        awair = Awair(ACCESS_TOKEN)
        user = mock_awair_user(client=awair.client)
        devices = await user.devices()

    assert devices[0].device_id == AWAIR_GEN1_ID
    assert devices[0].device_type == "awair"
    assert devices[0].uuid == f"awair_{AWAIR_GEN1_ID}"


async def test_get_latest():
    """Test that we can get the latest air data."""
    with VCR.use_cassette("latest.yaml"):
        awair = Awair(ACCESS_TOKEN)
        device = mock_awair_device(client=awair.client)
        resp = await device.air_data_latest()

    assert resp.timestamp == datetime(2020, 4, 9, 23, 18, 40, 317000)
    assert resp.score == 90.0
    assert resp.sensors["temp"] == 23.59000015258789
    assert resp.indices["temp"] == 0.0


# TODO I think we're outside of bounds?
async def test_get_five_minute():
    """Test that we can get the five-minute avg air data."""
    with VCR.use_cassette("five_minute.yaml"):
        awair = Awair(ACCESS_TOKEN)
        device = mock_awair_device(client=awair.client)
        resp = await device.air_data_five_minute(
            from_date=datetime(2020, 4, 8, 22, 59, 29)
        )

    assert resp[0].timestamp == datetime(2020, 4, 9, 23, 15)
    assert resp[0].score == 89.8695652173913
    assert resp[0].sensors["temp"] == 23.660434805828594
    assert resp[0].indices["temp"] == 0.0


async def test_get_fifteen_minute():
    """Test that we can get the fifteen-minute avg air data."""
    with VCR.use_cassette("fifteen_minute.yaml"):
        awair = Awair(ACCESS_TOKEN)
        device = mock_awair_device(client=awair.client)
        resp = await device.air_data_fifteen_minute(
            from_date=datetime(2020, 4, 8, 22, 59, 29)
        )

    assert resp[0].timestamp == datetime(2020, 4, 9, 23, 15)
    assert resp[0].score == 89.8695652173913
    assert resp[0].sensors["temp"] == 23.660434805828594
    assert resp[0].indices["temp"] == 0.0


async def test_get_raw():
    """Test that we can get the raw air data."""
    with VCR.use_cassette("raw.yaml"):
        awair = Awair(ACCESS_TOKEN)
        device = mock_awair_device(client=awair.client)
        resp = await device.air_data_raw(from_date=datetime(2020, 4, 8, 22, 59, 29))

    assert resp[0].timestamp == datetime(2020, 4, 9, 23, 18, 40, 317000)
    assert resp[0].score == 90.0
    assert resp[0].sensors["temp"] == 23.59000015258789
    assert resp[0].indices["temp"] == 0.0


async def test_auth_failure():
    """Test that we can raise on bad auth."""
    with VCR.use_cassette("bad_auth.yaml"):
        awair = Awair("bad")
        with pytest.raises(AwairClient.AuthError):
            await awair.user()


async def test_bad_query():
    """Test that we can raise on bad query."""
    with VCR.use_cassette("bad_params.yaml"):
        with patch(
            "python_awair.devices.AwairDevice._format_args",
            return_value="?fahrenheit=451",
        ):
            with pytest.raises(AwairClient.QueryError):
                awair = Awair(ACCESS_TOKEN)
                device = mock_awair_device(client=awair.client)
                await device.air_data_latest()


async def test_not_found():
    """Test that we can raise on 404."""
    with VCR.use_cassette("not_found.yaml"):
        with patch("python_awair.const.DEVICE_URL", f"{const.USER_URL}/devicesxyz"):
            with pytest.raises(AwairClient.NotFoundError):
                awair = Awair(ACCESS_TOKEN)
                user = mock_awair_user(client=awair.client)
                await user.devices()


async def test_air_data_handles_boolean_attributes():
    """Test that we handle boolean query attributes."""
    awair = Awair(ACCESS_TOKEN)
    device = mock_awair_device(client=awair.client)

    with pytest.raises(ValueError):
        await device.air_data_raw(desc=None)

    with pytest.raises(ValueError):
        await device.air_data_raw(fahrenheit=1)


async def test_air_data_handles_numeric_limits():
    """Test that we handle numeric query attributes."""
    awair = Awair(ACCESS_TOKEN)
    device = mock_awair_device(client=awair.client)

    with pytest.raises(ValueError):
        await device.air_data_raw(limit=-1)

    with pytest.raises(ValueError):
        await device.air_data_raw(limit=361)

    with pytest.raises(ValueError):
        await device.air_data_five_minute(limit=289)

    with pytest.raises(ValueError):
        await device.air_data_fifteen_minute(limit=673)


async def test_air_data_handles_datetime_limits():
    """Test that we handle date limits."""
    awair = Awair(ACCESS_TOKEN)
    device = mock_awair_device(client=awair.client)

    now = datetime.now()

    with pytest.raises(ValueError):
        await device.air_data_raw(from_date=(now + timedelta(hours=1)))

    with pytest.raises(ValueError):
        await device.air_data_raw(from_date=False)

    with pytest.raises(ValueError):
        await device.air_data_raw(from_date=(now - timedelta(hours=2)))

    with pytest.raises(ValueError):
        await device.air_data_five_minute(from_date=(now - timedelta(hours=25)))

    with pytest.raises(ValueError):
        await device.air_data_fifteen_minute(from_date=(now - timedelta(days=8)))

    with pytest.raises(ValueError):
        await device.air_data_fifteen_minute(
            from_date=(now - timedelta(hours=1)), to_date=(now - timedelta(hours=3))
        )
