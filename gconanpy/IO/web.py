#!/usr/bin/env python3

"""
Functions to import/export data from/to remote files/pages/APIs on the Web.
Greg Conan: gregmconan@gmail.com
Created: 2025-03-13
Updated: 2026-01-26
"""
# Import standard libraries
from collections.abc import Mapping
import requests
from typing import Any, Self
from urllib.parse import parse_qs, ParseResult, urlparse
import urllib.request

# Import local custom libraries
try:
    from gconanpy.meta import cached_property
    from gconanpy.wrappers import ToString
except (ImportError, ModuleNotFoundError):  # TODO DRY?
    from meta import cached_property
    from wrappers import ToString


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


class URL(ToString):

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
            url += cls.fromMapping(
                url_params, quote=None, join_on="=", prefix="?",
                suffix=None, sep="&", lastly="")
        return cls(url)

    @cached_property[dict[str, list]]
    def params(self) -> dict[str, list]:
        return parse_qs(self.parsed.query)

    parsed = cached_property[ParseResult](urlparse)

    @cached_property[str]
    def without_params(self) -> str:
        """
        :return: str, URL but without any parameters
        """
        return f"{self.parsed.scheme}://{''.join(self.parsed[1:3])}"


class Link:

    def __init__(self, text: str, url: str) -> None:
        self.text = text
        self.url = URL(url)

    @classmethod
    def from_markdown(cls, markdown_link_text: str) -> Self:
        try:
            markdown_link_text = markdown_link_text.strip()
            assert markdown_link_text[0] == "[" \
                and markdown_link_text[-1] == ")"
            md_link_parts = markdown_link_text[1:-1].split("](")
            self = cls(md_link_parts[0], md_link_parts[1])
        except (AssertionError, IndexError, TypeError) as err:
            raise ValueError(*err.args)
        return self

    def to_markdown(self) -> str:
        a_string = self.text.replace("[", r"\[").replace("]", r"\]")
        a_URL = self.url.replace("(", r"\(").replace(")", r"\)")
        return f"[{a_string}]({a_URL})"
