# python_awair

![Latest PyPI version](https://img.shields.io/pypi/v/python_awair.svg)
![CI](https://github.com/ahayworth/python_awair/workflows/CI/badge.svg?branch=master)
[![codecov](https://codecov.io/gh/ahayworth/python_awair/branch/master/graph/badge.svg)](https://codecov.io/gh/ahayworth/python_awair)
[![Documentation Status](https://readthedocs.org/projects/python-awair/badge/?version=latest)](https://python-awair.readthedocs.io/en/latest/?badge=latest)

This is an async library which accesses portions of the [Awair](https://getawair.com) REST API. It exists primarily
to support the Home Assistant integration, but is considered active and supported by its author. PRs welcome!

Features:
- Object-oriented approach to querying and handling data
- Supports the "user" portion of the API.
- Possible to list devices, user information, and to query for a variety of sensor data over various timeframes.

Not yet supported:
- Device API usage
- Organization API
- Device management (such as changing the display of a device)

Dive into our [documentation](https://python-awair.readthedocs.io/en/latest) to get started!

# Development

- We manage dependencies and builds via [poetry](https://python-poetry.org)
- We use [pytest](https://github.com/pytest-dev/pytest) and [tox](https://github.com/tox-dev/tox) to test
- A variety of linters are available and CI enforces them

After installing and configuring poetry:
- Run `poetry install` to install all dependencies
  - Run `poetry install -E linters` to install recommended linters
  - Run `poetry install -E docs` if you wish to rebuild docs
- Run `poetry shell` to drop into a virtualenv
- Run `poetry run tox` (or just `tox` if you're in a virtualenv) to test
  - Run `poetry run tox -e lint` (or just `tox -e lint` if you're in a virtualenv) to run linters.
