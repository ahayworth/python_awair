"""Class to describe an Awair user."""


from datetime import date
from typing import Dict, List, Optional

from python_awair import const
from python_awair.client import AwairClient
from python_awair.devices import AwairDevice


class AwairUser:
    """An awair user."""

    user_id: str
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    sex: Optional[str]
    dob: Optional[date]
    tier: Optional[str]
    usages: Dict[str, int]
    permissions: Dict[str, int]

    client: AwairClient

    def __init__(self, client: AwairClient, attributes: dict) -> None:
        """Initialize an awair user from API attributes."""
        self.user_id = attributes["id"]
        self.email = attributes.get("email", None)
        self.first_name = attributes.get("firstName", None)
        self.last_name = attributes.get("lastName", None)

        self.sex = attributes.get("sex", None)
        self.dob: Optional[date]
        dob_day = attributes.get("dobDay", None)
        dob_month = attributes.get("dobMonth", None)
        dob_year = attributes.get("dobYear", None)

        if all([dob_day, dob_month, dob_year]):
            self.dob = date(day=dob_day, month=dob_month, year=dob_year)
        else:
            self.dob = None

        self.tier = attributes.get("tier", None)
        self.usages = {
            item["scope"]: item["usage"] for item in attributes.get("usages", [])
        }
        self.permissions = {
            item["scope"]: item["quota"] for item in attributes.get("permissions", [])
        }

        self.client = client

    async def devices(self) -> List[AwairDevice]:
        """Return a list of awair devices from the API."""
        response = await self.client.query(const.DEVICE_URL)
        return [
            AwairDevice(client=self.client, attributes=device)
            for device in response.get("devices", [])
        ]
