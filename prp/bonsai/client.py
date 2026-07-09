"""Interact with the Bonsai API."""

from bonsai_libs.api_client import BonsaiApiClient
from bonsai_libs.api_client.core.auth import BearerTokenAuth


def make_bonsai_client(base_url: str, token: str | None = None):
    """Create bonsai API client."""

    return BonsaiApiClient(base_url=base_url, auth=BearerTokenAuth(token))
