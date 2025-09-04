"""An Awair user."""

from datetime import date
from typing import Any, Dict, List, Optional

from python_awair import const
from python_awair.client import AwairClient
from python_awair.devices import AwairDevice


class AwairUser:
    """An Awair user.

    This class is primarily informational - it describes the
    user to which the provided authentication belongs (be that an
    access_token, or perhaps an OAuth token). Available fields
    include user information, API quotas, and usage. Additionally,
    the class provides a method to access the list of devices
    that are "owned" by this user.

    .. note::
        While you can instantiate this class by hand (perhaps in
        a test case), you should typically load a user by calling
        *Awair.user()* instead.

    Args:
        client: An AwairClient that is used if this AwairUser
            object needs to query the API.

        attributes: A mapping which describes the user. This class
            expects that the *attributes* provided are essentially
            the result of calling the */v1/users/self* API
            endpoint.
    """

    user_id: str
    """str: The user ID uniquely references an Awair user account.
    It is returned as a string, because API docs indicate it is
    a string.
    """

    email: Optional[str]
    """Optional[str]: The email addres on file for the user."""

    first_name: Optional[str]
    """Optional[str]: The first name of the user."""

    last_name: Optional[str]
    """Optional[str]: The last name of the user."""

    sex: Optional[str]
    """Optional[str]: The 'sex' of the user.

    Typical values seem to be 'MALE', 'FEMALE', or 'UNKNOWN'.
    """

    dob: Optional[date]
    """Optional[date]: The user's date of birth, if known."""

    tier: Optional[str]
    """Optional[str]: The account "tier".

    This broadly maps to a set of permissions and API quotas,
    but they are not currently well-defined.
    """

    usages: Dict[str, int]
    """Dict[str, int]: A mapping describing API usage.

    The keys represent the type of API call being described, and
    should be reflected in the user's *permissions* attribute.

    The values represent the number of times that the API call
    has been used in this usage window. Usage windows reset at
    midnight.

    .. todo::
        Document the timezone of the usage window reset.
    """

    permissions: Dict[str, int]
    """Dict[str, int]: A mapping describing API quotas.


    The keys represent the type of API call being described, and
    if the API call has been used in this usage window, then it
    will be represented in this user's *usages* attribute.

    The values represent the maximum number of times that the API
    call may be used in this usage window. Usage windwos reset at
    midnight.

    .. todo::
        Document the timezone of the usage window reset.
    """

    client: AwairClient
    """AwairClient: A reference to the configured AwairClient.

    This AwairClient will be used to query the API and validate
    HTTP responses. It's normally not something one would need to
    access.
    """

    def __init__(self, client: AwairClient, attributes: Dict[str, Any]) -> None:
        """Initialize an awair user from API attributes."""
        self.user_id = attributes["id"]
        self.email = attributes.get("email", None)
        self.first_name = attributes.get("firstName", None)
        self.last_name = attributes.get("lastName", None)

        self.sex = attributes.get("sex", None)
        self.dob: Optional[date]
        dob_day = attributes.get("dobDay", None)
        dob_month = attributes.get("dobMonth", None)
        dob_year = attributes.get("dobYear", None)

        if dob_day and dob_month and dob_year:
            self.dob = date(day=dob_day, month=dob_month, year=dob_year)
        else:
            self.dob = None

        self.tier = attributes.get("tier", None)
        self.usages = {
            item["scope"]: item["usage"] for item in attributes.get("usages", [])
        }
        self.permissions = {
            item["scope"]: item["quota"] for item in attributes.get("permissions", [])
        }

        self.client = client

    def __repr__(self) -> str:
        """Return a friendly representation."""
        parts = [f"user_id={self.user_id}"]
        if self.email is not None:
            parts.append(f"email={self.email}")

        return f"<AwairUser: {' '.join(parts)}>"

    async def devices(self) -> List[AwairDevice]:
        """Return a list of awair devices this user owns.

        .. note::
            For organization users, the underlying API endpoint
            that this method uses should show you devices that
            you have access to view. However, the organization
            API is not directly supported at this time.
        """
        response = await self.client.query(const.DEVICE_URL)
        return [
            AwairDevice(client=self.client, attributes=device)
            for device in response.get("devices", [])
        ]
