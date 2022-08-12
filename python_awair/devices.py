"""Class to describe an Awair device."""

import urllib
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, cast

import voluptuous as vol

from python_awair import const
from python_awair.air_data import AirData
from python_awair.client import AwairClient

AirDataParam = Union[datetime, bool, int, None]


class AwairBaseDevice(ABC):
    """An Awair device.

    This class serves two purposes - it provides metadata about
    a given Awair device, but it also provides methods that
    retrieve sensor measurements from that device. Available
    information includes things like the model, name, and location
    of a device; and the query interface allows the user to query
    for sensor data in several different samplings, over various
    timeframes.

    .. note::
        While you can instantiate this class by hand (perhaps in
        a test case), you should typically load user devices by
        calling *AwairUser.devices()*.

    Args:
        client: An AwairClient that is used if this AwairDevice
            object needs to query the API.

        attributes: A mapping which describes the device. This
            class expects that the *attributes* provided are
            essentially the result of calling the
            */v1/users/self/devices* API endpoint.
    """

    device_id: int
    """int: The ID that identifies the Awair device."""

    uuid: str
    """str: Another ID that identifies the Awair device.

    This ID typically takes the form of *model_id*. For example,
    given a first-gen Awair device with ID 123, The uuid would be
    "awair_123".
    """

    device_type: str
    """str: The API name for the model of this Awair device.

    This differs from the human-friendly name, which is given
    by the *model* attribute.

    .. table::
        :widths: auto

        =============    ======================
        Device type      Model
        =============    ======================
        awair            `Awair (1st Edition)`_
        awair-element    `Awair Element`_
        awair-glow       `Awair Glow`_
        awair-glow-c     `Awair Glow C`_
        awair-mint       `Awair Baby`_
        awair-omni       `Awair Omni`_
        awair-r2         `Awair (2nd Edition)`_
        =============    ======================

    .. _`Awair (2nd Edition)`: https://getawair.com/pages/awair-2nd-edition
    .. _`Awair Baby`: https://getawair.com/pages/awair-baby
    .. _`Awair Element`: https://getawair.com/pages/awair-element
    .. _`Awair Glow C`: https://getawair.com/pages/awair-glow
    .. _`Awair Glow`:
      https://web.archive.org/web/20161210171139/https://getawair.com/pages/awair-glow
    .. _`Awair Omni`: https://getawair.com/pages/awair-for-business
    .. _`Awair (1st Edition)`:
      https://web.archive.org/web/20150528004143/https://getawair.com/
    """

    mac_address: Optional[str]
    """Optional[str]: The network MAC address."""

    latitude: Optional[float]
    """float: The latitude of the device's location, if known."""

    location_name: Optional[str]
    """float: Description of the device's location."""

    longitude: Optional[float]
    """float: The longitude of the device's location, if known."""

    name: Optional[str]
    """Optional[str]: The user-assigned name for this device."""

    preference: Optional[str]
    """Optional[str]: The device "preference".

    This represents an instruction to the Awair application,
    which represents the area of concern for this device. Put
    differently, it represents *why* the user is using this
    device to monitor air quality - for example, concern about
    allergies.

    Example: "GENERAL"
    """

    room_type: Optional[str]
    """Optional[str]: The type of room this device is in.

    For example, a "LIVING_ROOM" or an "OFFICE".
    """

    space_type: Optional[str]
    """Optional[str]: The type of space this device is in.

    For example, this might be an "OFFICE" or a "HOME".
    """

    timezone: Optional[str]
    """Optional[str]: The timezone of the device."""

    client: AwairClient
    """AwairClient: A reference to the configured AwairClient.

    This is the class that actually queries the API. It's here
    if you need it, but you probably don't need to use it.
    """

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
        """Return the human-friendly model, if known.

        .. table::
            :widths: auto

            =============    ======================
            Device type      Model
            =============    ======================
            awair            `Awair (1st Edition)`_
            awair-element    `Awair Element`_
            awair-glow       `Awair Glow`_
            awair-glow-c     `Awair Glow C`_
            awair-mint       `Awair Baby`_
            awair-omni       `Awair Omni`_
            awair-r2         `Awair (2nd Edition)`_
            =============    ======================

        .. _`Awair (2nd Edition)`: https://getawair.com/pages/awair-2nd-edition
        .. _`Awair Baby`: https://getawair.com/pages/awair-baby
        .. _`Awair Element`: https://getawair.com/pages/awair-element
        .. _`Awair Glow C`: https://getawair.com/pages/awair-glow
        .. _`Awair Glow`:
          https://web.archive.org/web/20161210171139/https://getawair.com/pages/awair-glow
        .. _`Awair Omni`: https://getawair.com/pages/awair-for-business
        .. _`Awair (1st Edition)`:
          https://web.archive.org/web/20150528004143/https://getawair.com/
        """
        return const.AWAIR_MODELS.get(self.device_type, self.device_type)

    async def air_data_latest(self, fahrenheit: bool = False) -> Optional[AirData]:
        """Get the latest air data for this device.

        Returns one AirData class describing the most up-to-date measurements
        for this device's sensors. If the device has been offline for more
        than 10 minutes, None will be returned.

        Args:
            fahrenheit: Return temperatures in fahrenheit (the default is to
              return temperatures in celsius). The conversion is done in the
              Awair API itself, not in this library.
        """
        response = await self.__get_airdata("latest", fahrenheit=fahrenheit)
        if response:
            return response[0]

        return None

    async def air_data_five_minute(self, **kwargs: AirDataParam) -> List[AirData]:
        r"""Return five-minute summary air data readings for this device.

        Each data point returned represents a five-minute average of sensor readings.
        Up to a maximum of 288 data points will be returned - which represents 24
        hours of data.

        Args:
            kwargs: A mapping of query parameters, which influence the data returned.
                None are required:

                ==========  =====================================================
                Parameter   Value
                ==========  =====================================================
                fahrenheit  *False* (default): temperature data is returned in
                            celsius.

                            *True*: temperature data is returned in fahrenheit.

                desc        *True* (default): datapoints are ordered descending
                            from the *to* parameter.

                            *False*: datapoints are ordered ascending from the
                            *to* parameter.

                limit       *int*: represents the maximum number of datapoints to
                            return. The default and maximum for this parameter is
                            288.

                from        *datetime*: lower bound for the earliest datapoint to
                            return. May not be chronologically after the *to*
                            parameter, and the difference between the *to* and
                            *from* parameters may not exceed 24 hours.
                            Defaults to 24 hours before the current date/time.

                to          *datetime*: upper bound for the most recent datapoint
                            to return. May not be chronologically before the
                            *from* parameter, and the difference between the *to*
                            and *from* parameters may not exceed 24 hours.
                            Defaults to the current date/time.
                ==========  =====================================================

        """
        return await self.__get_airdata("5-min-avg", **kwargs)

    async def air_data_fifteen_minute(self, **kwargs: AirDataParam) -> List[AirData]:
        r"""Return fifteen-minute summary air data readings for this device.

        Each data point returned represents a fifteen-minute average of sensor readings.
        Up to a maximum of 672 data points will be returned - which represents 7 days
        of data.

        Args:
            kwargs: A mapping of query parameters, which influence the data returned.
                None are required:

                ==========  =====================================================
                Parameter   Value
                ==========  =====================================================
                fahrenheit  *False* (default): temperature data is returned in
                            celsius.

                            *True*: temperature data is returned in fahrenheit.

                desc        *True* (default): datapoints are ordered descending
                            from the *to* parameter.

                            *False*: datapoints are ordered ascending from the
                            *to* parameter.

                limit       *int*: represents the maximum number of datapoints to
                            return. The default and maximum for this parameter is
                            672.

                from        *datetime*: lower bound for the earliest datapoint to
                            return. May not be chronologically after the *to*
                            parameter, and the difference between the *to* and
                            *from* parameters may not exceed 7 days.
                            Defaults to 7 days before the current date/time.

                to          *datetime*: upper bound for the most recent datapoint
                            to return. May not be chronologically before the
                            *from* parameter, and the difference between the *to*
                            and *from* parameters may not exceed 7 days.
                            Defaults to the current date/time.
                ==========  =====================================================

        """
        return await self.__get_airdata("15-min-avg", **kwargs)

    async def air_data_raw(self, **kwargs: AirDataParam) -> List[AirData]:
        r"""Return the raw, per-second air data readings for this device.

        Each data point returned represents the sensor readings at a given second.
        Up to a maximum of 360 data points will be returned - which represents 1 hour
        of data.

        Args:
            kwargs: A mapping of query parameters, which influence the data returned.
                None are required:

                ==========  =====================================================
                Parameter   Value
                ==========  =====================================================
                fahrenheit  *False* (default): temperature data is returned in
                            celsius.

                            *True*: temperature data is returned in fahrenheit.

                desc        *True* (default): datapoints are ordered descending
                            from the *to* parameter.

                            *False*: datapoints are ordered ascending from the
                            *to* parameter.

                limit       *int*: represents the maximum number of datapoints to
                            return. The default and maximum for this parameter is
                            360.

                from        *datetime*: lower bound for the earliest datapoint to
                            return. May not be chronologically after the *to*
                            parameter, and the difference between the *to* and
                            *from* parameters may not exceed 1 hour.
                            Defaults to 1 hour before the current date/time.

                to          *datetime*: upper bound for the most recent datapoint
                            to return. May not be chronologically before the
                            *from* parameter, and the difference between the *to*
                            and *from* parameters may not exceed 1 hour.
                            Defaults to the current date/time.
                ==========  =====================================================

        """
        return await self.__get_airdata("raw", **kwargs)

    @abstractmethod
    def _get_airdata_base_url(self) -> str:
        """Get the base URL to use for airdata."""
        raise TypeError("expected subclass to define override")

    @abstractmethod
    def _extract_airdata(self, response: Any) -> List[Any]:
        """Get the data object out of a response."""
        raise TypeError("expected subclass to define override")

    async def __get_airdata(self, kind: str, **kwargs: AirDataParam) -> List[AirData]:
        """Call one of several varying air-data API endpoints."""
        url = "/".join([self._get_airdata_base_url(), "air-data", kind])

        if kwargs is not None:
            url += self._format_args(kind, **kwargs)

        response = await self.client.query(url)
        return [AirData(data) for data in self._extract_airdata(response)]

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


class AwairDevice(AwairBaseDevice):
    """A cloud-based Awair device."""

    def _get_airdata_base_url(self) -> str:
        """Get the base URL to use for airdata."""
        return "/".join([const.DEVICE_URL, self.device_type, str(self.device_id)])

    def _extract_airdata(self, response: Any) -> List[Any]:
        """Get the data object out of a response."""
        return cast(List[Any], response.get("data", []))


class AwairLocalDevice(AwairBaseDevice):
    """A local Awair device."""

    device_addr: str
    """The DNS or IP address of the device."""

    fw_version: str
    """The firmware version currently running on the device."""

    def __init__(
        self, client: AwairClient, device_addr: str, attributes: Dict[str, Any]
    ):
        """Initialize an awair local device from API attributes."""
        # the format of the config endpoint for local sensors is different than
        # the cloud API.
        device_uuid: str = attributes["device_uuid"]
        [device_type, device_id_str] = device_uuid.split("_", 1)
        device_id = int(device_id_str)
        attributes["deviceId"] = device_id
        attributes["deviceUUID"] = device_uuid
        attributes["deviceType"] = device_type
        attributes["macAddress"] = attributes.get("wifi_mac", None)
        super().__init__(client, attributes)
        self.device_addr = device_addr
        self.fw_version = attributes.get("fw_version", None)

    def _get_airdata_base_url(self) -> str:
        """Get the base URL to use for airdata."""
        return f"http://{self.device_addr}"

    def _extract_airdata(self, response: Any) -> List[Any]:
        """Get the data object out of a response."""
        # reformat local sensors response to match the cloud API
        top_level = {"timestamp", "score"}
        sensors = [
            {"comp": k, "value": response[k]}
            for k in response.keys()
            if k not in top_level
        ]
        data = {
            "timestamp": response["timestamp"],
            "score": response["score"],
            "sensors": sensors,
        }

        return [data]

    @staticmethod
    def _format_args(kind: str, **kwargs: AirDataParam) -> str:
        if "fahrenheit" in kwargs:
            if kwargs["fahrenheit"]:
                raise ValueError("fahrenheit is not supported for local sensors yet")
            # if we pass any URL parameters with local sensors, it causes the
            # timestamp to be the empty string.
            del kwargs["fahrenheit"]

        return AwairBaseDevice._format_args(kind, **kwargs)
