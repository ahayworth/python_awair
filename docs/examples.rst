--------
Examples
--------

.. contents::
  :local:

Sample program
==============

.. code:: python

  import asyncio
  import aiohttp
  from python_awair import Awair

  async def data():
      async with aiohttp.ClientSession() as session:
          # Instantiate a client with your access token, and an asyncio session:
          client = Awair(access_token="token", session=session)

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

  asyncio.run(data())


Here's what running that sample would print::

  $ python awair_demo.py
  Device: <AwairDevice: uuid=awair_24947 model=Awair>
    dust: 13.7
    temperature: 22.12
    humidity: 45.18
    carbon_dioxide: 1114.0
    volatile_organic_compounds: 545.0
    temperature again: 22.12


Instantiating a client
======================

To instantiate a client, you'll need your access token and
must also pass in an aiohttp session:

.. code:: python

    async with aiohttp.ClientSession() as session:
        client = Awair(access_token="token", session=session)

Getting the current user
========================

This example retrieves the user, and prints out some information.

.. code:: python

  async with aiohttp.ClientSession() as session:
      client = Awair(session=session, token="token")
      user = await client.user()

      if user.dob is not None:
          print(f"This user was born on: {user.dob}")

      for method, limit in user.permissions.items():
          print(f"Method: {method} - {limit}")


Listing a user's devices
========================

To retrieve every device a user can see:

.. code:: python

  async with aiohttp.ClientSession() as session:
      client = Awair(session=session, token="token")
      user = await client.user()
      devices = await user.devices()
      for device in devices:
          print(f"I can see this device: {device}")

Fetching recent data for a device
=================================

.. code:: python

  async with aiohttp.ClientSession() as session:
      client = Awair(session=session, token="token")
      user = await client.user()
      devices = await user.devices()
      device = devices[0]

      data = await device.air_data_latest()
      print(f"Awair score: {data.score}")
      for sensor, value in data.sensors:
        print(f"{sensor}: {round(value, 2)}")
        if sensor in data.indices:
          print(f"  awair index: {data.indices[sensor]}")

Fetching data from a different time
===================================

.. code:: python

  async with aiohttp.ClientSession() as session:
      client = Awair(session=session, token="token")
      user = await client.user()
      devices = await user.devices()
      device = devices[0]

      data = await device.air_data_five_minute(
        fahrenheit=True,
        limit=4,
        from=(datetime.now() - timedelta(hours=2)),
        to=(datetime.now() - timedelta(hours=1, minutes=30))
      )

      for datum in data:
        print("----------------------------")
        print(f"Data at: {datum.timestamp}")
        print(f"Awair score: {datum.score}")
        for sensor, value in datum.sensors:
          print(f"{sensor}: {round(value, 2)}")
          if sensor in datum.indices:
            print(f"  awair index: {datum.indices[sensor]}")

Sample local sensors program
=================================

Awair recently added the `local sensors API`_, where you can retrieve current (and only current)
air data from devices on your local network over HTTP.

.. _`local sensors API`: https://docs.google.com/document/d/1001C-ro_ig7aEyz0GiWUiiJn0M6DLj47BYWj31acesg/edit

.. literalinclude:: ../examples/local.py
   :language: python

Running this sample prints::

  $ AWAIR_DEVICE=192.168.0.5 python examples/local.py
  Device: <AwairDevice: uuid=awair-element_5366 model=Awair Element>
    dew_point: 10.81
    abs_humid: 9.59
    co2_est: 461
    voc_baseline: 2536742680
    voc_h2_raw: 27
    voc_ethanol_raw: 39
    pm10_est: 3
    temperature: 19.16
    humidity: 58.46
    carbon_dioxide: 438
    volatile_organic_compounds: 384
    particulate_matter_2_5: 2
    temperature again: 19.16

