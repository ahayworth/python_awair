"""Test basic python_awair functionality."""

import os
import re
from collections import namedtuple
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from typing import Optional
from unittest.mock import patch

import aiohttp
import pytest
import vcr
import voluptuous as vol

from python_awair import Awair, const
from python_awair.client import AwairClient
from python_awair.devices import AwairDevice
from python_awair.exceptions import AuthError, AwairError, NotFoundError, QueryError
from python_awair.user import AwairUser
from tests.utils import SillyAuth

ACCESS_TOKEN = os.environ.get("AWAIR_ACCESS_TOKEN", "abcdefg")

AWAIR_GEN1_TYPE = "awair"
AWAIR_GEN1_ID = 24947
MOCK_GEN1_DEVICE_ATTRS = {
    "deviceId": AWAIR_GEN1_ID,
    "deviceType": AWAIR_GEN1_TYPE,
    "deviceUUID": f"{AWAIR_GEN1_TYPE}_{AWAIR_GEN1_ID}",
}
MOCK_OMNI_DEVICE_ATTRS = {
    "deviceId": 755,
    "deviceType": "awair-omni",
    "deviceUUID": "awair-omni_755",
}
MOCK_MINT_DEVICE_ATTRS = {
    "deviceId": 3665,
    "deviceType": "awair-mint",
    "deviceUUID": "awair-mint_3665",
}
MOCK_GEN2_DEVICE_ATTRS = {
    "deviceId": 5709,
    "deviceType": "awair-r2",
    "deviceUUID": "awair-r2_5709",
}
MOCK_GLOW_DEVICE_ATTRS = {
    "deviceId": 1405,
    "deviceType": "awair-glow",
    "deviceUUID": "awair-glow_1405",
}
MOCK_USER_ATTRS = {"id": "32406"}


def mock_awair_user(client: AwairClient) -> AwairUser:
    """Return a mock awair user."""
    return AwairUser(client=client, attributes=MOCK_USER_ATTRS)


def mock_awair_device(
    client: AwairClient, device: Optional[dict] = None,
) -> AwairDevice:
    """Return a mock awair device."""
    if not device:
        device = MOCK_GEN1_DEVICE_ATTRS

    return AwairDevice(client=client, attributes=device)


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


@contextmanager
def time_travel(target: datetime):
    """Manage time in our tests."""
    with patch("python_awair.devices.datetime") as mock_date:
        mock_date.now.return_value = target
        mock_date.side_effect = datetime

        yield


async def test_get_user():
    """Test that we can get a user response."""
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("user.yaml"):
            awair = Awair(session=session, access_token=ACCESS_TOKEN)
            user = await awair.user()

    assert user.user_id == "32406"
    assert user.email == "foo@bar.com"
    assert user.first_name == "Andrew"
    assert user.dob == date(year=2020, month=4, day=8)
    assert user.tier == "Large_developer"
    assert user.permissions["FIFTEEN_MIN"] == 30000
    assert user.usages["USER_INFO"] == 80


async def test_custom_auth():
    """Test that we can use the API with a custom auth class."""
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("custom_auth.yaml"):
            auth = SillyAuth(access_token=ACCESS_TOKEN)
            awair = Awair(session=session, authenticator=auth)
            user = await awair.user()

    assert user.user_id == "32406"


async def test_get_devices():
    """Test that we can get a list of devices."""
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("devices.yaml"):
            awair = Awair(session=session, access_token=ACCESS_TOKEN)
            user = mock_awair_user(client=awair.client)
            devices = await user.devices()

    assert devices[0].device_id == AWAIR_GEN1_ID
    assert devices[0].device_type == "awair"
    assert devices[0].uuid == f"awair_{AWAIR_GEN1_ID}"


async def test_get_latest():
    """Test that we can get the latest air data."""
    target = datetime(2020, 4, 10, 10, 38, 30)
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("latest.yaml"), time_travel(target):
            awair = Awair(session=session, access_token=ACCESS_TOKEN)
            device = mock_awair_device(client=awair.client)
            resp = await device.air_data_latest()

    assert resp.timestamp == datetime(2020, 4, 10, 15, 38, 24, 111000)
    assert resp.score == 88.0
    assert resp.sensors["temperature"] == 21.770000457763672
    assert resp.indices["temperature"] == -1.0


async def test_get_five_minute():
    """Test that we can get the five-minute avg air data."""
    target = datetime(2020, 4, 10, 10, 38, 31, 2883)
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("five_minute.yaml"), time_travel(target):
            awair = Awair(session=session, access_token=ACCESS_TOKEN)
            device = mock_awair_device(client=awair.client)
            resp = await device.air_data_five_minute(
                from_date=(target - timedelta(minutes=30))
            )

    assert resp[0].timestamp == datetime(2020, 4, 10, 15, 35)
    assert resp[0].score == 88.0
    assert resp[0].sensors["temperature"] == 21.777143478393555
    assert resp[0].indices["temperature"] == -1.0


async def test_get_fifteen_minute():
    """Test that we can get the fifteen-minute avg air data."""
    target = datetime(2020, 4, 10, 10, 38, 31, 252873)
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("fifteen_minute.yaml"):
            awair = Awair(session=session, access_token=ACCESS_TOKEN)
            device = mock_awair_device(client=awair.client)
            resp = await device.air_data_fifteen_minute(
                from_date=(target - timedelta(minutes=30))
            )

    assert resp[0].timestamp == datetime(2020, 4, 10, 15, 30)
    assert resp[0].score == 88.0
    assert resp[0].sensors["temperature"] == 21.791961108936984
    assert resp[0].indices["temperature"] == -1.0


async def test_get_raw():
    """Test that we can get the raw air data."""
    target = datetime(2020, 4, 10, 10, 38, 31, 720296)
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("raw.yaml"), time_travel(target):
            awair = Awair(session=session, access_token=ACCESS_TOKEN)
            device = mock_awair_device(client=awair.client)
            resp = await device.air_data_raw(from_date=(target - timedelta(minutes=30)))

    assert resp[0].timestamp == datetime(2020, 4, 10, 15, 38, 24, 111000)
    assert resp[0].score == 88.0
    assert resp[0].sensors["temperature"] == 21.770000457763672
    assert resp[0].indices["temperature"] == -1.0


async def test_sensor_creation_gen1():
    """Test that an Awair gen 1 creates expected sensors."""
    target = datetime(2020, 4, 10, 10, 38, 30)
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("latest.yaml"), time_travel(target):
            awair = Awair(session=session, access_token=ACCESS_TOKEN)
            device = mock_awair_device(client=awair.client)
            resp = await device.air_data_latest()

    assert hasattr(resp, "timestamp")
    assert hasattr(resp, "score")
    assert hasattr(resp, "sensors")
    assert hasattr(resp, "indices")
    expected_sensors = [
        "humidity",
        "temperature",
        "carbon_dioxide",
        "volatile_organic_compounds",
        "dust",
    ]
    assert len(resp.sensors) == len(expected_sensors)
    assert len(resp.indices) == len(expected_sensors)
    for sensor in expected_sensors:
        assert hasattr(resp.sensors, sensor)
        assert hasattr(resp.indices, sensor)


async def test_sensor_creation_omni():
    """Test that an Awair omni creates expected sensors."""
    target = datetime(2020, 4, 10, 10, 38, 30)
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("omni.yaml"), time_travel(target):
            awair = Awair(session=session, access_token=ACCESS_TOKEN)
            device = mock_awair_device(
                client=awair.client, device=MOCK_OMNI_DEVICE_ATTRS
            )
            resp = await device.air_data_latest()

    assert hasattr(resp, "timestamp")
    assert hasattr(resp, "score")
    assert hasattr(resp, "sensors")
    assert hasattr(resp, "indices")

    expected_sensors = [
        "humidity",
        "temperature",
        "carbon_dioxide",
        "volatile_organic_compounds",
        "particulate_matter_2_5",
        "illuminance",
        "sound_pressure_level",
    ]
    assert len(resp.sensors) == len(expected_sensors)
    for sensor in expected_sensors:
        assert hasattr(resp.sensors, sensor)

    expected_indices = [
        "humidity",
        "temperature",
        "carbon_dioxide",
        "volatile_organic_compounds",
        "particulate_matter_2_5",
    ]
    assert len(resp.indices) == len(expected_indices)
    for sensor in expected_indices:
        assert hasattr(resp.indices, sensor)


async def test_sensor_creation_mint():
    """Test that an Awair mint creates expected sensors."""
    target = datetime(2020, 4, 10, 10, 38, 30)
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("mint.yaml"), time_travel(target):
            awair = Awair(session=session, access_token=ACCESS_TOKEN)
            device = mock_awair_device(
                client=awair.client, device=MOCK_MINT_DEVICE_ATTRS
            )
            resp = await device.air_data_latest()

    assert hasattr(resp, "timestamp")
    assert hasattr(resp, "score")
    assert hasattr(resp, "sensors")
    assert hasattr(resp, "indices")

    expected_sensors = [
        "humidity",
        "temperature",
        "volatile_organic_compounds",
        "particulate_matter_2_5",
        "illuminance",
    ]
    assert len(resp.sensors) == len(expected_sensors)
    for sensor in expected_sensors:
        assert hasattr(resp.sensors, sensor)

    expected_indices = [
        "humidity",
        "temperature",
        "volatile_organic_compounds",
        "particulate_matter_2_5",
    ]
    assert len(resp.indices) == len(expected_indices)
    for sensor in expected_indices:
        assert hasattr(resp.indices, sensor)


async def test_sensor_creation_gen2():
    """Test that an Awair gen2 creates expected sensors."""
    target = datetime(2020, 4, 10, 10, 38, 30)
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("awair-r2.yaml"), time_travel(target):
            awair = Awair(session=session, access_token=ACCESS_TOKEN)
            device = mock_awair_device(
                client=awair.client, device=MOCK_GEN2_DEVICE_ATTRS
            )
            resp = await device.air_data_latest()

    assert hasattr(resp, "timestamp")
    assert hasattr(resp, "score")
    assert hasattr(resp, "sensors")
    assert hasattr(resp, "indices")

    expected_sensors = [
        "humidity",
        "temperature",
        "volatile_organic_compounds",
        "particulate_matter_2_5",
        "carbon_dioxide",
    ]
    assert len(resp.sensors) == len(expected_sensors)
    for sensor in expected_sensors:
        assert hasattr(resp.sensors, sensor)

    expected_indices = [
        "humidity",
        "temperature",
        "volatile_organic_compounds",
        "particulate_matter_2_5",
        "carbon_dioxide",
    ]
    assert len(resp.indices) == len(expected_indices)
    for sensor in expected_indices:
        assert hasattr(resp.indices, sensor)


async def test_sensor_creation_glow():
    """Test that an Awair glow creates expected sensors."""
    target = datetime(2020, 4, 10, 10, 38, 30)
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("glow.yaml"), time_travel(target):
            awair = Awair(session=session, access_token=ACCESS_TOKEN)
            device = mock_awair_device(
                client=awair.client, device=MOCK_GLOW_DEVICE_ATTRS
            )
            resp = await device.air_data_latest()

    assert hasattr(resp, "timestamp")
    assert hasattr(resp, "score")
    assert hasattr(resp, "sensors")
    assert hasattr(resp, "indices")

    expected_sensors = [
        "humidity",
        "temperature",
        "volatile_organic_compounds",
        "carbon_dioxide",
    ]
    assert len(resp.sensors) == len(expected_sensors)
    for sensor in expected_sensors:
        assert hasattr(resp.sensors, sensor)

    expected_indices = [
        "humidity",
        "temperature",
        "volatile_organic_compounds",
        "carbon_dioxide",
    ]
    assert len(resp.indices) == len(expected_indices)
    for sensor in expected_indices:
        assert hasattr(resp.indices, sensor)


async def test_auth_failure():
    """Test that we can raise on bad auth."""
    async with aiohttp.ClientSession() as session:
        with pytest.raises(AwairError):
            Awair(session=session)

        with VCR.use_cassette("bad_auth.yaml"):
            awair = Awair(session=session, access_token="bad")
            with pytest.raises(AuthError):
                await awair.user()


async def test_bad_query():
    """Test that we can raise on bad query."""
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("bad_params.yaml"):
            with patch(
                "python_awair.devices.AwairDevice._format_args",
                return_value="?fahrenheit=451",
            ):
                with pytest.raises(QueryError):
                    awair = Awair(session=session, access_token=ACCESS_TOKEN)
                    device = mock_awair_device(client=awair.client)
                    await device.air_data_latest()


async def test_not_found():
    """Test that we can raise on 404."""
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("not_found.yaml"):
            with patch("python_awair.const.DEVICE_URL", f"{const.USER_URL}/devicesxyz"):
                with pytest.raises(NotFoundError):
                    awair = Awair(session=session, access_token=ACCESS_TOKEN)
                    user = mock_awair_user(client=awair.client)
                    await user.devices()


async def test_air_data_handles_boolean_attributes():
    """Test that we handle boolean query attributes."""
    async with aiohttp.ClientSession() as session:
        awair = Awair(session=session, access_token=ACCESS_TOKEN)
        device = mock_awair_device(client=awair.client)

        with pytest.raises(vol.Invalid):
            await device.air_data_raw(desc=None)

        with pytest.raises(vol.Invalid):
            await device.air_data_raw(fahrenheit=1)


async def test_air_data_handles_numeric_limits():
    """Test that we handle numeric query attributes."""
    async with aiohttp.ClientSession() as session:
        awair = Awair(session=session, access_token=ACCESS_TOKEN)
        device = mock_awair_device(client=awair.client)

        with pytest.raises(vol.Invalid):
            await device.air_data_raw(limit=-1)

        with pytest.raises(vol.Invalid):
            await device.air_data_raw(limit=361)

        with pytest.raises(vol.Invalid):
            await device.air_data_five_minute(limit=289)

        with pytest.raises(vol.Invalid):
            await device.air_data_fifteen_minute(limit=673)


async def test_air_data_handles_datetime_limits():
    """Test that we handle date limits."""
    async with aiohttp.ClientSession() as session:
        awair = Awair(session=session, access_token=ACCESS_TOKEN)
        device = mock_awair_device(client=awair.client)

        now = datetime.now()

        with pytest.raises(vol.Invalid):
            await device.air_data_raw(from_date=(now + timedelta(hours=1)))

        with pytest.raises(vol.Invalid):
            await device.air_data_raw(from_date=False)

        with pytest.raises(vol.Invalid):
            await device.air_data_raw(from_date=(now - timedelta(hours=2)))

        with pytest.raises(vol.Invalid):
            await device.air_data_five_minute(from_date=(now - timedelta(hours=25)))

        with pytest.raises(vol.Invalid):
            await device.air_data_fifteen_minute(from_date=(now - timedelta(days=8)))

        with pytest.raises(vol.Invalid):
            await device.air_data_fifteen_minute(
                from_date=(now - timedelta(hours=1)), to_date=(now - timedelta(hours=3))
            )
