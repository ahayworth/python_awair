"""Dict with attribute-like access."""

from python_awair import const


class AttrDict(dict):
    """Dict with attribute-like access."""

    def __init__(self, attrs: dict) -> None:
        """Initialize, hiding known sensor aliases."""
        new_attrs = dict(attrs)
        for key, value in attrs.items():
            if key in const.SENSOR_TO_ALIAS:
                new_attrs[const.SENSOR_TO_ALIAS[key]] = value
                del new_attrs[key]

        super().__init__(new_attrs)

    def __getattr__(self, name):
        """Return things in the dict via dot-notation."""
        if name in self:
            return self[name]

        raise AttributeError()

    def __setattr__(self, name, value):
        """Set values in the dict via dot-notation."""
        self[name] = value

    def __delattr__(self, name):
        """Remove values from the dict via dot-notation."""
        del self[name]

    def __dir__(self):
        """Return dict keys as dir attributes."""
        return self.keys()
