"""Indices dict with attribute access."""

from python_awair.attrdict import AttrDict


class Indices(AttrDict):
    """Indices of an AwairDevice.

    An Indices object represents a set of "index" values for a
    set of sensors of a given AwairDevice. Essentially, the "index"
    is a bit like a quality score - and Awair has devised a set of
    quality levels for a variety of their sensors. The "index" is given
    as a *float* between -4 and 4, but the absolute value is what
    really matters - just ignore the sign. As a value approaches 4.0,
    it is considered "worse". As it approaches 0, it is considered
    "better".

    A mapping of index ranges and values per-sensor can be found
    at Awair's `API documentation`_ - that list is authoritative.

    .. _`API documentation`:
      https://docs.developer.getawair.com/?version=latest#data-guide


    The Indices object is a subclass of AttrDict, and thus its values
    are accessible via string keys - like *foo["bar"]* - or via dot-notation:
    *foo.bar*.

    The index names from the Awair API are not entirely user-friendly,
    so we've aliased known indices to more descriptive values:

    .. table::

        ======== ==========================
        API name python_awair name
        ======== ==========================
        temp     temperature
        humid    humidity
        co2      carbon_dioxide
        voc      volatile_organic_compounds
        pm25     particulate_matter_2_5
        ======== ==========================

    Any new indices added by an Awair device before this library
    is updated will be accessible via their API name, rather than
    a friendly name.

    .. note::
        The 1st generation Awair device will have a "dust" index,
        since it has an aggregate pm2.5/pm10 dust sensor (and cannot
        distinguish between those two sizes).

    .. note::
        Do not assume that every sensor present on a device will
        also have a corresponding "index"; this is not the case.
    """

    def __repr__(self) -> str:
        """Pretty-print."""
        return f"Indices({super().__repr__()})"
