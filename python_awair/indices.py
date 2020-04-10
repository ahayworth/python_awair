"""Indices dict with attribute access."""
from python_awair.attrdict import AttrDict


class Indices(AttrDict):
    """Indices dict with attribute access."""

    def __repr__(self):
        """Pretty-print."""
        return f"Indices({super().__repr__()})"
