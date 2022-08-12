"""Local Sensors Example."""

import os
import asyncio
import aiohttp
from python_awair import AwairLocal


async def fetch_data():
    """Get data from local Awair device."""
    async with aiohttp.ClientSession() as session:
        device_address = os.environ.get("AWAIR_DEVICE", "AWAIR-ELEM-1419E1.local")
        client = AwairLocal(session=session, device_addrs=[device_address])

        # List the local devices:
        devices = await client.devices()

        # Get some air quality data for a user's device:
        data = await devices[0].air_data_latest()

        # Print things out!
        print(f"Device: {devices[0]}")
        print(f"Device firmware: {devices[0].fw_version}")

        # You can access sensors as dict items:
        for sensor, value in data.sensors.items():
            print(f"  {sensor}: {round(value, 2)}")

        # Or, as attributes:
        print(f"  temperature again: {round(data.sensors.temperature, 2)}")


asyncio.run(fetch_data())
