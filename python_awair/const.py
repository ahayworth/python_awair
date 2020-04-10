"""Mostly query constants."""
BASE_URL = "https://developer-apis.awair.is/v1"
USER_URL = f"{BASE_URL}/users/self"
DEVICE_URL = f"{USER_URL}/devices"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

SENSOR_TO_ALIAS = {
    "temp": "temperature",
    "humid": "humidity",
    "co2": "carbon_dioxide",
    "voc": "volatile_organic_compounds",
    "pm25": "particulate_matter_2_5",
    "lux": "illuminance",
    "spl_a": "sound_pressure_level",
}

AWAIR_MODELS = {
    "awair": "Awair",
    "awair-glow": "Awair Glow",
    "awair-mint": "Awair Mint",
    "awair-omni": "Awair Omni",
    "awair-r2": "Awair 2nd Edition",
    "awair-glow-c": "Awair Glow C",
    "awair-element": "Awair Element",
}
