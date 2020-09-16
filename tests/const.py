"""Test constants."""

import os

ACCESS_TOKEN = os.environ.get("AWAIR_ACCESS_TOKEN", "abcdefg")
AWAIR_GEN1_ID = 24947
MOCK_GEN1_DEVICE_ATTRS = {
    "deviceId": AWAIR_GEN1_ID,
    "deviceType": "awair",
    "deviceUUID": f"awair_{AWAIR_GEN1_ID}",
}
MOCK_OMNI_DEVICE_ATTRS = {
    "deviceId": 755,
    "deviceType": "awair-omni",
    "deviceUUID": "awair-omni_755",
}
MOCK_MINT_DEVICE_ATTRS = {
    "deviceId": 3665,
    "deviceType": "awair-mint",
    "deviceUUID": "awair-mint_3665",
}
MOCK_GEN2_DEVICE_ATTRS = {
    "deviceId": 5709,
    "deviceType": "awair-r2",
    "deviceUUID": "awair-r2_5709",
}
MOCK_GLOW_DEVICE_ATTRS = {
    "deviceId": 1405,
    "deviceType": "awair-glow",
    "deviceUUID": "awair-glow_1405",
}
MOCK_USER_ATTRS = {"id": "32406"}
MOCK_ELEMENT_DEVICE_A_ATTRS = {
    "deviceId": 6049,
    "deviceType": "awair-element",
    "deviceUUID": "awair-element_6049",
}
MOCK_ELEMENT_DEVICE_B_ATTRS = {
    "deviceId": 5366,
    "deviceType": "awair-element",
    "deviceUUID": "awair-element_5366",
}
