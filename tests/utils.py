"""Test utilities."""

import re
from collections import namedtuple
from contextlib import contextmanager
from datetime import datetime
from typing import Optional
from unittest.mock import patch

import vcr

from python_awair.auth import AwairAuth
from python_awair.client import AwairClient
from python_awair.devices import AwairDevice
from python_awair.user import AwairUser
from tests.const import MOCK_GEN1_DEVICE_ATTRS, MOCK_USER_ATTRS


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


class SillyAuth(AwairAuth):
    """Testing auth class."""

    def __init__(self, access_token: str) -> None:
        """Store our access token."""
        self.access_token = access_token

    async def get_bearer_token(self) -> str:
        """Return the access_token."""
        return self.access_token


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
