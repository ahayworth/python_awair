"""Sensors dict with attribute access."""

from python_awair.attrdict import AttrDict


class Sensors(AttrDict):
    """Sensors dict with attribute access."""

    def __repr__(self) -> str:
        """Pretty-print."""
        return f"Sensors({super().__repr__()})"
