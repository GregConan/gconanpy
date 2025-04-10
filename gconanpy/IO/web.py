#!/usr/bin/env python3

"""
Functions to import/export data from/to remote files/pages/apps on the Web.
Greg Conan: gregmconan@gmail.com
Created: 2025-03-13
Updated: 2025-04-10
"""
# Import standard libraries
from collections.abc import Mapping
import datetime as dt
import pdb
import requests
from typing import Any
from urllib.parse import parse_qs, urlparse
import urllib.request


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


def extract_params_from_url(a_url: str) -> dict[str, Any]:
    return parse_qs(urlparse(a_url).query)


def read_webpage_at(a_URL: str) -> Any:  # urllib.request._UrlopenRet:
    return urllib.request.urlopen(a_URL).read()


class URL:
    """ `urllib.parse.ParseResult` with extra methods """

    def __init__(self, a_URL: str):
        self.urlstr = a_URL
        self.parsed = urlparse(a_URL)

    def __repr__(self):
        return self.urlstr

    def get_params(self) -> str:
        return parse_qs(self.parsed.query)

    def without_params(self) -> str:
        """
        :param a_url: str, a valid web URL
        :return: str, a_url but without any parameters
        """
        return f"{self.parsed.scheme}://{''.join(self.parsed[1:3])}"


def without_parameters(a_url: str) -> str:
    """
    :param a_url: str, a valid web URL
    :return: str, a_url but without any parameters
    """
    parsed = urlparse(a_url)
    return f"{parsed.scheme}://{''.join(parsed[1:3])}"
