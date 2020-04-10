"""Class to describe an Awair device."""

import urllib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from python_awair import const
from python_awair.air_data import AirData
from python_awair.client import AwairClient


class AwairDevice:
    """An awair device."""

    device_id: int
    uuid: str
    device_type: str
    mac_address: Optional[str]

    latitude: Optional[float]
    location_name: Optional[str]
    longitude: Optional[float]
    name: Optional[str]
    preference: Optional[str]
    room_type: Optional[str]
    space_type: Optional[str]
    timezone: Optional[str]

    client: AwairClient

    def __init__(self, client: AwairClient, attributes: dict) -> None:
        """Initialize an awair device from API attributes."""
        self.device_id = attributes["deviceId"]
        self.uuid = attributes["deviceUUID"]
        self.device_type = attributes["deviceType"]
        self.mac_address = attributes.get("macAddress", None)

        self.latitude = attributes.get("latitude", None)
        self.longitude = attributes.get("longitude", None)
        self.name = attributes.get("name", None)
        self.preference = attributes.get("preference", None)
        self.room_type = attributes.get("roomType", None)
        self.space_type = attributes.get("spaceType", None)
        self.timezone = attributes.get("timezone", None)

        self.client = client

    async def air_data_latest(self, fahrenheit: bool = False) -> Optional[AirData]:
        """Get the latest air data for this device."""
        response = await self.__get_airdata("latest", fahrenheit=fahrenheit)
        if response:
            return response[0]

        return None

    async def air_data_five_minute(
        self, **kwargs: Union[datetime, bool, int, None],
    ) -> List[AirData]:
        """Return the 5min summary air data for this device."""
        return await self.__get_airdata("5-min-avg", **kwargs)

    async def air_data_fifteen_minute(
        self, **kwargs: Union[datetime, bool, int, None],
    ) -> List[AirData]:
        """Return the 15min summary air data for this device."""
        return await self.__get_airdata("15-min-avg", **kwargs)

    async def air_data_raw(
        self, **kwargs: Union[datetime, bool, int, None],
    ) -> List[AirData]:
        """Return the raw air data for this device."""
        return await self.__get_airdata("raw", **kwargs)

    async def __get_airdata(self, kind: str, **kwargs) -> List[AirData]:
        """Call one of several varying air-data API endpoints."""
        url = "/".join(
            [const.DEVICE_URL, self.device_type, str(self.device_id), "air-data", kind]
        )

        if kwargs is not None:
            url += self._format_args(kind, **kwargs)

        response = await self.client.query(url)
        return [AirData(data) for data in response.get("data", [])]

    @staticmethod
    def _format_args(kind: str, **kwargs: Union[datetime, bool, int, None]) -> str:
        args: Dict[str, str] = {}

        boolean_args = ("fahrenheit", "desc")
        numeric_args = {"limit": {"raw": 360, "5-min-avg": 288, "15-min-avg": 672}}
        time_args = ("from_date", "to_date")
        default_hours = {"raw": 1, "15-min-avg": 168, "5-min-avg": 24}

        right_now = datetime.now()
        max_hours = default_hours.get(kind, 24)
        from_date = right_now - timedelta(hours=max_hours)
        to_date = right_now

        for arg, val in kwargs.items():
            if arg in boolean_args:
                sval = str(val).lower()
                if sval not in ("true", "false"):
                    raise ValueError(f"'{arg}' must be True or False")
                args[arg] = sval

            if arg in numeric_args.keys():
                max_val = numeric_args[arg][kind]
                if not isinstance(val, int):
                    raise ValueError(f"'{arg} must be an integer.")

                if val < 1 or val > max_val:
                    raise ValueError(
                        f"'{arg}' must be between 1 and {max_val}, or unspecified."
                    )

                args[arg] = str(val)

            if arg in time_args:
                if not isinstance(val, datetime):
                    raise ValueError(f"'{arg}' must be an instance of datetime.")

                if val > right_now:
                    raise ValueError(f"'{arg}' cannot be in the future.")

                if arg == "from_date":
                    from_date = val
                if arg == "to_date":
                    to_date = val

                args[arg] = str(val)

        if from_date > to_date:
            raise ValueError("'from_date' cannot be greater than 'to_date'.")

        if (to_date - from_date) > timedelta(hours=max_hours):
            raise ValueError(
                "Difference between 'from_date' and 'to_date' must be less than "
                + f"or equal to {max_hours} hours."
            )

        if args:
            return "?" + urllib.parse.urlencode(args)

        return ""
