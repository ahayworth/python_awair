"""Class to describe an Awair device."""

import urllib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import voluptuous as vol

from python_awair import const
from python_awair.air_data import AirData
from python_awair.client import AwairClient

AirDataParam = Union[datetime, bool, int, None]


class AwairDevice:
    """An awair device."""

    device_id: int
    uuid: str
    device_type: str
    device_model: str
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

    def __init__(self, client: AwairClient, attributes: Dict[str, Any]) -> None:
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

    def __repr__(self) -> str:
        """Return a friendly representation."""
        return f"<AwairDevice: uuid={self.uuid} model={self.model}>"

    @property
    def model(self) -> str:
        """Return the human-friendly model, if known."""
        return const.AWAIR_MODELS.get(self.device_type, self.device_type)

    async def air_data_latest(self, fahrenheit: bool = False) -> Optional[AirData]:
        """Get the latest air data for this device."""
        response = await self.__get_airdata("latest", fahrenheit=fahrenheit)
        if response:
            return response[0]

        return None

    async def air_data_five_minute(self, **kwargs: AirDataParam) -> List[AirData]:
        """Return the 5min summary air data for this device."""
        return await self.__get_airdata("5-min-avg", **kwargs)

    async def air_data_fifteen_minute(self, **kwargs: AirDataParam) -> List[AirData]:
        """Return the 15min summary air data for this device."""
        return await self.__get_airdata("15-min-avg", **kwargs)

    async def air_data_raw(self, **kwargs: AirDataParam) -> List[AirData]:
        """Return the raw air data for this device."""
        return await self.__get_airdata("raw", **kwargs)

    async def __get_airdata(self, kind: str, **kwargs: AirDataParam) -> List[AirData]:
        """Call one of several varying air-data API endpoints."""
        url = "/".join(
            [const.DEVICE_URL, self.device_type, str(self.device_id), "air-data", kind]
        )

        if kwargs is not None:
            url += self._format_args(kind, **kwargs)

        response = await self.client.query(url)
        return [AirData(data) for data in response.get("data", [])]

    @staticmethod
    def _format_args(kind: str, **kwargs: AirDataParam) -> str:
        max_limit = {"raw": 360, "5-min-avg": 288, "15-min-avg": 672}
        max_hours = {"raw": 1, "15-min-avg": 168, "5-min-avg": 24}

        def validate_hours(params: Dict[str, Any]) -> Dict[str, Any]:
            hour_limit = max_hours.get(kind, 24)
            right_now = datetime.now()
            from_date = params.get("from_date", right_now - timedelta(hours=hour_limit))
            to_date = params.get("to_date", right_now)

            if not hasattr(from_date, "now") or not hasattr(to_date, "now"):
                raise vol.Invalid(
                    "Expected 'from_date' and/or 'to_date' to be instances of datetime"
                )

            if from_date > right_now or to_date > right_now:
                raise vol.Invalid("Dates cannot be in the future!")
            if from_date > to_date:
                raise vol.Invalid("'from_date' cannot be greater than 'to_date'.")
            if (to_date - from_date) > timedelta(hours=hour_limit):
                raise vol.Invalid(
                    "Difference between 'from_date' and 'to_date' must be less than "
                    + f"or equal to {hour_limit} hours."
                )

            if "from_date" in params:
                params["from_date"] = str(params["from_date"])

            if "to_date" in params:
                params["to_date"] = str(params["to_date"])

            return params

        schema = vol.Schema(
            vol.All(
                {
                    vol.Optional("fahrenheit"): vol.All(
                        bool, vol.Coerce(str), vol.Lower
                    ),
                    vol.Optional("desc"): vol.All(bool, vol.Coerce(str), vol.Lower),
                    vol.Optional("limit"): vol.All(
                        int,
                        vol.Range(min=1, max=max_limit.get(kind, 1)),
                        vol.Coerce(str),
                    ),
                    # We validate dates by hand because it's annoying af with mocking.
                    vol.Optional("from_date"): object,
                    vol.Optional("to_date"): object,
                },
                validate_hours,
            )
        )

        args = schema(kwargs)
        if args:
            return "?" + urllib.parse.urlencode(args)

        return ""
