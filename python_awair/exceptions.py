"""Various exceptions for the Awair API."""

from typing import Optional


class AwairError(Exception):
    """Base awair exception class."""

    message = "Error querying the Awair API."

    def __init__(self, extra_message: Optional[str] = None) -> None:
        """Add extra messages to our base message."""
        final_message = self.message
        if extra_message:
            final_message += f" {extra_message}"

        super().__init__(final_message)


class AuthError(AwairError):
    """Some kind of authorization or authentication failure."""

    message = (
        "The supplied access token is invalid or "
        + "does not have access to the requested data"
    )


class QueryError(AwairError):
    """The query was somehow malformed."""

    message = "The supplied parameters were invalid."


class NotFoundError(AwairError):
    """The requested endpoint is gone."""

    message = "The Awair API returned an unexpected HTTP 404."


class RatelimitError(AwairError):
    """The API quota was exceeded."""

    message = (
        "The ratelimit for the Awair API has been " + "exceeded. Please try again later"
    )
