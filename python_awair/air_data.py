"""Wrapper class for awair airdata responses."""

from datetime import datetime
from typing import Dict

from python_awair import const


class AirData:
    """Wrapper class for awair airdata responses."""

    timestamp: datetime
    score: float

    # TODO: use attributes directly?
    sensors: Dict[str, float]

    # TODO: use attributes directly?
    indices: Dict[str, float]

    def __init__(self, attributes: dict) -> None:
        """Initialize from API data."""
        self.timestamp = datetime.strptime(attributes["timestamp"], const.DATE_FORMAT)
        self.score = attributes["score"]

        self.sensors = {
            sensor["comp"]: sensor["value"] for sensor in attributes.get("sensors", [])
        }

        self.indices = {
            index["comp"]: index["value"] for index in attributes.get("indices", [])
        }
