#!/usr/bin/env python3

"""
Functions to import/export data from/to remote files/pages/apps on the Web.
Greg Conan: gregmconan@gmail.com
Created: 2025-03-13
Updated: 2025-03-14
"""
# Import standard libraries
import datetime as dt
import pdb
import requests
from typing import Any, Callable, Hashable, Iterable, Mapping
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
