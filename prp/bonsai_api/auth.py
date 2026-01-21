"""Bonsai API authentication."""


from functools import wraps
from typing import Any, Callable
from pydantic import BaseModel
import requests
from requests.structures import CaseInsensitiveDict

USER_ENV = "BONSAI_USER"
PASSWD_ENV = "BONSAI_PASSWD"
TIMEOUT = 10


class TokenObject(BaseModel):  # pylint: disable=too-few-public-methods
    """Token object"""

    token: str
    type: str


class ConnectionInfo(BaseModel):
    """Container for connection information to Bonsai API."""

    api_url: str
    token: TokenObject | None = None


def authenticate(api_url: str, username: str, password: str) -> ConnectionInfo:
    """Get authentication token from api"""
    # configure header
    headers: CaseInsensitiveDict[str] = CaseInsensitiveDict()
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    url = f"{api_url}/token"
    resp = requests.post(
        url,
        data={"username": username, "password": password},
        headers=headers,
        timeout=TIMEOUT,
    )
    # controll that request
    resp.raise_for_status()
    json_res = resp.json()
    return ConnectionInfo(
        api_url=api_url,
        token=TokenObject(token=json_res["access_token"], type=json_res["token_type"]),
    )


def api_authentication(func: Callable[..., Any]) -> Callable[..., Any]:
    """Use authentication token for api.

    :param func: API function to wrap with API auth headers
    :type func: Callable
    :return: Wrapped API function
    :rtype: Callable
    """

    @wraps(func)
    def wrapper(
        token_obj: TokenObject, *args: list[Any], **kwargs: dict[str, Any]
    ) -> Callable[..., Any]:
        """Add authentication headers to API requests.

        :param token_obj: Auth token object
        :type token_obj: TokenObject
        :return: Wrapped API call function
        :rtype: Callable
        """
        headers: CaseInsensitiveDict[str] = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers["Authorization"] = f"{token_obj.type.capitalize()} {token_obj.token}"

        return func(headers=headers, *args, **kwargs)

    return wrapper