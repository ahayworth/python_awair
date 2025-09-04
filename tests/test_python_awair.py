"""Test basic python_awair functionality."""

from datetime import date, datetime, timedelta
from typing import Any
from unittest.mock import patch

import aiohttp
import pytest
import voluptuous as vol

from python_awair import Awair, AwairLocal, const
from python_awair.attrdict import AttrDict
from python_awair.exceptions import AuthError, AwairError, NotFoundError, QueryError
from tests.const import (
    ACCESS_TOKEN,
    AWAIR_GEN1_ID,
    MOCK_ELEMENT_DEVICE_A_ATTRS,
    MOCK_ELEMENT_DEVICE_B_ATTRS,
    MOCK_GEN2_DEVICE_ATTRS,
    MOCK_GLOW_DEVICE_ATTRS,
    MOCK_MINT_DEVICE_ATTRS,
    MOCK_OMNI_DEVICE_ATTRS,
)
from tests.utils import VCR, SillyAuth, mock_awair_device, mock_awair_user, time_travel


async def test_get_user() -> Any:
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

    assert "<AwairUser" in str(user)


async def test_custom_auth() -> Any:
    """Test that we can use the API with a custom auth class."""
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("custom_auth.yaml"):
            auth = SillyAuth(access_token=ACCESS_TOKEN)
            awair = Awair(session=session, authenticator=auth)
            user = await awair.user()

    assert user.user_id == "32406"


async def test_get_devices() -> Any:
    """Test that we can get a list of devices."""
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("devices.yaml"):
            awair = Awair(session=session, access_token=ACCESS_TOKEN)
            user = mock_awair_user(client=awair.client)
            devices = await user.devices()

    assert devices[0].device_id == AWAIR_GEN1_ID
    assert devices[0].device_type == "awair"
    assert devices[0].uuid == f"awair_{AWAIR_GEN1_ID}"
    assert "<AwairDevice" in str(devices[0])


async def test_get_local_devices() -> Any:
    """Test that we can get a list of devices."""
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("local_devices.yaml"):
            awair = AwairLocal(
                session=session,
                device_addrs=["AWAIR-ELEM-1416DC.local", "AWAIR-ELEM-1419E1.local"],
            )
            devices = await awair.devices()

    assert len(devices) == 2

    assert devices[0].device_id == MOCK_ELEMENT_DEVICE_A_ATTRS["deviceId"]
    assert devices[0].device_type == MOCK_ELEMENT_DEVICE_A_ATTRS["deviceType"]
    assert devices[0].uuid == MOCK_ELEMENT_DEVICE_A_ATTRS["deviceUUID"]
    assert devices[0].fw_version == MOCK_ELEMENT_DEVICE_A_ATTRS["fw_version"]
    assert "<AwairDevice" in str(devices[0])

    assert devices[1].device_id == MOCK_ELEMENT_DEVICE_B_ATTRS["deviceId"]
    assert devices[1].device_type == MOCK_ELEMENT_DEVICE_B_ATTRS["deviceType"]
    assert devices[1].uuid == MOCK_ELEMENT_DEVICE_B_ATTRS["deviceUUID"]
    assert devices[1].fw_version == MOCK_ELEMENT_DEVICE_B_ATTRS["fw_version"]
    assert "<AwairDevice" in str(devices[1])


async def test_get_latest() -> Any:
    """Test that we can get the latest air data."""
    target = datetime(2020, 4, 10, 10, 38, 30)
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("latest.yaml"), time_travel(target):
            awair = Awair(session=session, access_token=ACCESS_TOKEN)
            device = mock_awair_device(client=awair.client)
            resp = await device.air_data_latest()

    assert resp is not None
    assert resp.timestamp == datetime(2020, 4, 10, 15, 38, 24, 111000)
    assert resp.score == 88.0
    assert resp.sensors["temperature"] == 21.770000457763672
    assert resp.indices["temperature"] == -1.0
    assert "<AirData@2020-04-10" in str(resp)


async def test_get_latest_local() -> Any:
    """Test that we can get the latest air data."""
    target = datetime(2020, 8, 31, 22, 7, 3)
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("latest_local.yaml"), time_travel(target):
            awair = AwairLocal(
                session=session, device_addrs=["AWAIR-ELEM-1419E1.local"]
            )
            devices = await awair.devices()
            assert len(devices) == 1
            device = devices[0]
            resp = await device.air_data_latest()

    assert resp is not None
    assert resp.timestamp == datetime(2020, 8, 31, 22, 7, 3, 831000)
    assert resp.score == 93
    assert resp.sensors["temperature"] == 19.59
    assert len(resp.indices) == 0
    assert "<AirData@2020-08-31" in str(resp)


async def test_get_five_minute() -> Any:
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


async def test_get_fifteen_minute() -> Any:
    """Test that we can get the fifteen-minute avg air data."""
    target = datetime(2020, 4, 10, 10, 38, 31, 252873)
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("fifteen_minute.yaml"), time_travel(target):
            awair = Awair(session=session, access_token=ACCESS_TOKEN)
            device = mock_awair_device(client=awair.client)
            resp = await device.air_data_fifteen_minute(
                from_date=(target - timedelta(minutes=30))
            )

    assert resp[0].timestamp == datetime(2020, 4, 10, 15, 30)
    assert resp[0].score == 88.0
    assert resp[0].sensors["temperature"] == 21.791961108936984
    assert resp[0].indices["temperature"] == -1.0


async def test_get_raw() -> Any:
    """Test that we can get the raw air data."""
    target = datetime(2020, 4, 10, 10, 38, 31, 720296)
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("raw.yaml"), time_travel(target):
            awair = Awair(session=session, access_token=ACCESS_TOKEN)
            device = mock_awair_device(client=awair.client)
            resp = await device.air_data_raw(from_date=target - timedelta(minutes=30))

    assert resp[0].timestamp == datetime(2020, 4, 10, 15, 38, 24, 111000)
    assert resp[0].score == 88.0
    assert resp[0].sensors["temperature"] == 21.770000457763672
    assert resp[0].indices["temperature"] == -1.0


async def test_sensor_creation_gen1() -> Any:
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
    assert resp is not None
    assert len(resp.sensors) == len(expected_sensors)
    assert len(resp.indices) == len(expected_sensors)
    for sensor in expected_sensors:
        assert hasattr(resp.sensors, sensor)
        assert hasattr(resp.indices, sensor)

    assert device.model == "Awair"


async def test_sensor_creation_omni() -> Any:
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
    assert resp is not None
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


async def test_sensor_creation_mint() -> Any:
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
    assert resp is not None
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


async def test_sensor_creation_gen2() -> Any:
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
    assert resp is not None
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


async def test_sensor_creation_glow() -> Any:
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
    assert resp is not None
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

    assert "Indices(" in str(resp.indices)
    assert "Sensors(" in str(resp.sensors)


async def test_auth_failure() -> Any:
    """Test that we can raise on bad auth."""
    async with aiohttp.ClientSession() as session:
        with pytest.raises(AwairError):
            Awair(session=session)

        with VCR.use_cassette("bad_auth.yaml"):
            awair = Awair(session=session, access_token="bad")
            with pytest.raises(AuthError):
                await awair.user()


async def test_bad_query() -> Any:
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


async def test_not_found() -> Any:
    """Test that we can raise on 404."""
    async with aiohttp.ClientSession() as session:
        with VCR.use_cassette("not_found.yaml"):
            with patch("python_awair.const.DEVICE_URL", f"{const.USER_URL}/devicesxyz"):
                with pytest.raises(NotFoundError):
                    awair = Awair(session=session, access_token=ACCESS_TOKEN)
                    user = mock_awair_user(client=awair.client)
                    await user.devices()


async def test_air_data_handles_boolean_attributes() -> Any:
    """Test that we handle boolean query attributes."""
    async with aiohttp.ClientSession() as session:
        awair = Awair(session=session, access_token=ACCESS_TOKEN)
        device = mock_awair_device(client=awair.client)

        with pytest.raises(vol.Invalid):
            await device.air_data_raw(desc=None)

        with pytest.raises(vol.Invalid):
            await device.air_data_raw(fahrenheit=1)


async def test_air_data_handles_numeric_limits() -> Any:
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


async def test_air_data_handles_datetime_limits() -> Any:
    """Test that we handle date limits."""
    async with aiohttp.ClientSession() as session:
        awair = Awair(session=session, access_token=ACCESS_TOKEN)
        device = mock_awair_device(client=awair.client)

        now = datetime.now()

        with pytest.raises(vol.Invalid):
            await device.air_data_raw(from_date=now + timedelta(hours=1))

        with pytest.raises(vol.Invalid):
            await device.air_data_raw(from_date=False)

        with pytest.raises(vol.Invalid):
            await device.air_data_raw(from_date=now - timedelta(hours=2))

        with pytest.raises(vol.Invalid):
            await device.air_data_five_minute(from_date=now - timedelta(hours=25))

        with pytest.raises(vol.Invalid):
            await device.air_data_fifteen_minute(from_date=now - timedelta(days=8))

        with pytest.raises(vol.Invalid):
            await device.air_data_fifteen_minute(
                from_date=(now - timedelta(hours=1)), to_date=(now - timedelta(hours=3))
            )


def test_attrdict() -> Any:
    """Test a few AttrDict properties."""
    comp = AttrDict({"foo": "bar", "humid": 123})

    with pytest.raises(AttributeError):
        print(comp.nope)

    with pytest.raises(AttributeError):
        print(comp.humid)

    assert comp.humidity == 123

    comp["nope"] = "hi"
    assert comp.nope == "hi"

    comp.nope = "hello"
    assert comp.nope == "hello"

    del comp["nope"]
    del comp.humidity

    assert "foo" in dir(comp)
    assert "nope" not in dir(comp)
    assert "humid" not in dir(comp)
    assert "humidity" not in dir(comp)
