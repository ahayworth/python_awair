"""Wrapper class for awair airdata responses."""

from datetime import datetime

from python_awair import const
from python_awair.sensors import Sensors
from python_awair.indices import Indices


class AirData:
    """Wrapper class for awair airdata responses."""

    timestamp: datetime
    score: float
    sensors: Sensors
    indices: Indices

    def __init__(self, attributes: dict) -> None:
        """Initialize from API data."""
        self.timestamp = datetime.strptime(attributes["timestamp"], const.DATE_FORMAT)
        self.score = attributes["score"]

        self.sensors = Sensors({
            sensor["comp"]: sensor["value"] for sensor in attributes.get("sensors", [])
        })

        self.indices = Indices({
            index["comp"]: index["value"] for index in attributes.get("indices", [])
        })
