import importlib.metadata
import platform

import httpx

from . import constants
from .metadata import get_distribution_metadata

BASE_URL = f"https://discord.com/api/v{constants.API_VERSION}"
"""The versioned discord API URL to use when making HTTP requests."""

USER_AGENT_TEMPLATE = "DiscordBot ({homepage} {version}) Python/{python_version}"
"""The template to use when creating the user agent to be sent to Discord."""


def _get_project_url(
    metadata: importlib.metadata.PackageMetadata,
    label: str,
) -> str:
    """Returns the project URL with the given label.

    :param metadata: The metadata to get project URLs from.
    :param label: The label of the URL to return.

    .. seealso:: https://packaging.python.org/en/latest/specifications/core-metadata/#project-url-multiple-use

    """
    for type_url in metadata.get_all("Project-URL"):
        type_, url = type_url.split(", ", 1)
        if type_ == label:
            return url
    raise ValueError(f"Could not find project url for: {label!r}")


def _create_headers(
    *,
    token: str | None = None,
) -> dict[str, str]:
    """Returns the headers to use for the discord API.

    :param token: The token to use for authentication, if desired.

    """
    metadata = get_distribution_metadata()
    headers = {
        "User-Agent": USER_AGENT_TEMPLATE.format(
            homepage=_get_project_url(metadata, "Homepage"),
            version=metadata["Version"],
            python_version=platform.python_version(),
        )
    }

    if token is not None:
        headers["Authorization"] = token

    return headers


def create_httpx_client(
    *,
    token: str | None = None,
) -> httpx.AsyncClient:
    """Creates an HTTP client suitable for making requests to the discord API.

    :param token: The token to use for authentication, if desired.

    """
    headers = _create_headers(token=token)
    return httpx.AsyncClient(
        base_url=BASE_URL,
        headers=headers,
    )
