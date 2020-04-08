# python_awair

![Latest PyPI version](https://img.shields.io/pypi/v/python_awair.svg)
![CI](https://github.com/ahayworth/python_awair/workflows/CI/badge.svg?branch=master)
![Coveralls](https://coveralls.io/repos/github/ahayworth/python_awair/badge.svg?branch=master)

This is a WIP library to access the Awair API.
Features:
- uses graphql to access data (not sure if that's really a feature, but it's cool).
- async friendly!

Not yet supported:
- graphql mutations. There aren't docs on the developer site yet. We may implement them
  via REST.
- anything other than hobbyist-level endpoints (eg, no organizations)

Getting started:
- You'll need an access token from the [Awair Developer Console](https://developer.getawair.com/console). It's free.

Usage:

```python
from python_awair import AwairClient
import aiohttp
import asyncio

async def test_it():
  session = aiohttp.ClientSession()
  client = AwairClient('your_access_token', session=session)
  result = await client.air_data_latest("device_uuid")
  print(result)
  await session.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.ensure_future(test_it()))
loop.close()
```

# Development

- We manage dependencies and builds via [poetry](https://python-poetry.org)
- We use [pytest](https://github.com/pytest-dev/pytest) and [tox](https://github.com/tox-dev/tox) to test
- Code style is enforced via flake8

After installing and configuring poetry:
- Run `poetry install` to install all dependencies
- Run `poetry shell` to drop into a virtualenv
- Run `poetry run tox` (or just `tox` if you're in the virtualenv) to test
