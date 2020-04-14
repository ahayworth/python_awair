"""Wrapper class for awair airdata responses."""

from datetime import datetime
from typing import Any, Dict

from python_awair import const
from python_awair.indices import Indices
from python_awair.sensors import Sensors


class AirData:
    """Wrapper class for awair airdata responses."""

    timestamp: datetime
    score: float
    sensors: Sensors
    indices: Indices

    def __init__(self, attributes: Dict[str, Any]) -> None:
        """Initialize from API data."""
        self.timestamp = datetime.strptime(attributes["timestamp"], const.DATE_FORMAT)
        self.score = attributes["score"]

        self.sensors = Sensors(
            {
                sensor["comp"]: sensor["value"]
                for sensor in attributes.get("sensors", [])
            }
        )

        self.indices = Indices(
            {index["comp"]: index["value"] for index in attributes.get("indices", [])}
        )

    def __repr__(self) -> str:
        """Return a friendly representation."""
        return (
            f"<AirData@{self.timestamp}: "
            + f"score={round(self.score, 2)} sensors={self.sensors}>"
        )
