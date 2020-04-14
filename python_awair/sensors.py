"""Sensors dict with attribute-like access."""

from python_awair.attrdict import AttrDict


class Sensors(AttrDict):
    """Sensors of an AwairDevice.

    A Sensors object represents a set of sensors and corresponding
    values for a given Awair device, at a given point in time. The
    object itself essentially inherits from *dict*, and thus one
    can access sensor values by their string keys, and it is iterable -
    just like a dict.

    However, the class also supports getting, setting, and deleting
    sensor values via dot-notation; like an attribute or property.

    For example, given a *foo* Sensors object with a "bar" sensor, you could
    access that value either by calling *foo["bar"]* or *foo.bar*.

    The sensor names from the Awair API are not entirely user-friendly,
    so we've aliased known sensors to more descriptive values:

    .. table::

        ======== ==========================
        API name python_awair name
        ======== ==========================
        temp     temperature
        humid    humidity
        co2      carbon_dioxide
        voc      volatile_organic_compounds
        pm25     particulate_matter_2_5
        lux      illuminance
        spl_a    sound_pressure_level
        ======== ==========================

    A more thorough description of available sensors and their
    units is available on `Awair's API documentation`_.

    Any new sensors added by an Awair device before this library
    is updated will be accessible via their API name, rather than
    a friendly name.

    .. note::
        The 1st generation Awair device contains an "aggregate dust"
        sensor, which measures a range of particle sizes. It cannot
        distinguish between pm2.5 and pm10 particles.

    .. _`Awair's API documentation`:
      https://docs.developer.getawair.com/?version=latest#data-guide
    """

    def __repr__(self) -> str:
        """Pretty-print."""
        return f"Sensors({super().__repr__()})"
