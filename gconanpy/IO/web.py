#!/usr/bin/env python3

"""
Functions to import/export data from/to remote files/pages/APIs on the Web.
Greg Conan: gregmconan@gmail.com
Created: 2025-03-13
Updated: 2025-06-03
"""
# Import standard libraries
from collections.abc import Mapping
import requests
from typing import Any
from typing_extensions import Self
from urllib.parse import parse_qs, urlparse
import urllib.request

# Import local custom libraries
try:
    from ..ToString import stringify_map
except ModuleNotFoundError:  # TODO DRY?
    from gconanpy.ToString import stringify_map


def download_GET(path_URL: str, headers: Mapping[str, Any]) -> Any:
    """
    :param path_URL: String, full URL path to a file/resource to download
    :param headers: Mapping[str, Any] of header names to their values in the
                    HTTP GET request to send to path_URL
    :return: Object(s) retrieved from path_URL using HTTP GET request
    """
    # Make the request to the API
    response = requests.get(path_URL, headers=headers)

    # Check if the request was successful
    try:
        assert response.status_code == 200
        return response
    except (AssertionError, requests.JSONDecodeError) as err:
        # TODO replace print with log
        print(f"\nFailed to retrieve file(s) at {path_URL}\n"
              f"{response.status_code} Error: {response.reason}")


def read_webpage_at(a_URL: str) -> Any:  # -> urllib.request._UrlopenRet:
    return urllib.request.urlopen(a_URL).read()


class URL:
    """ `urllib.parse.ParseResult` wrapper with extra methods """

    def __init__(self, a_URL: str) -> None:
        """
        :param a_URL: str, a valid web URL
        """
        self.urlstr = a_URL
        self.parsed = urlparse(a_URL)

    def __repr__(self) -> str:
        return self.urlstr

    @classmethod
    def from_parts(cls, *parts: str, **url_params: Any) -> Self:
        """ Reusable convenience function to build HTTPS URL strings.

        :param parts: Iterable[str] of slash-separated URL path parts
        :param url_params: Mapping[str, Any] of variable names and their values \
                        to pass to the API endpoint as parameters
        :return: URL, full HTTPS URL built from parts & url_params
        """
        url = f"https://{'/'.join(parts)}"
        if url_params:
            url += stringify_map(url_params, quote=None, join_on="=",
                                 prefix="?", suffix=None, sep="&", lastly="")
        return cls(url)

    def get_params(self) -> dict[str, list]:
        return parse_qs(self.parsed.query)

    def without_params(self) -> str:
        """
        :return: str, URL but without any parameters
        """
        return f"{self.parsed.scheme}://{''.join(self.parsed[1:3])}"
