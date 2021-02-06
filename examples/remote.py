"""Remote sensors example."""

import os
import asyncio
import aiohttp
from python_awair import Awair


async def fetch_data():
    """Fetch remote data."""
    async with aiohttp.ClientSession() as session:
        # Instantiate a client with your access token, and an asyncio session:
        token = os.environ.get("AWAIR_TOKEN")
        client = Awair(access_token=token, session=session)

        # Retrieve a user object:
        user = await client.user()

        # List that user's devices:
        devices = await user.devices()

        # Get some air quality data for a user's device:
        data = await devices[0].air_data_latest()

        # Print things out!
        print(f"Device: {devices[0]}")

        # You can access sensors as dict items:
        for sensor, value in data.sensors.items():
            print(f"  {sensor}: {round(value, 2)}")

        # Or, as attributes:
        print(f"  temperature again: {round(data.sensors.temperature, 2)}")


asyncio.run(fetch_data())
