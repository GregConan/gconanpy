#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-03-28
Updated: 2025-04-01
"""
# Import standard libraries
from abc import ABC
import os
import pdb

# Import third-party PyPI libraries
from bs4 import BeautifulSoup

# Import local custom libraries
from gconanpy.maps import Cryptionary, DotDict


class Tester(ABC):

    def add_basics(self):
        self.adict = dict(a=1, b=2, c=3)
        self.alist = [1, 2, 3, 4, 5]
        self.bytes_nums = b"7815 11461 11468 11507 11516 17456 17457 17460 " \
            b"7815 11461 11468 11507 11516 17456 17457 17460 12345 12345 " \
            b"7815 11461 11468 11507 11516 17456 17457 17460 12345 12345 " \
            b"7815 11461 11468 11507 11516 17456 17457 17460 12345 12345 "

    def build_cli_args(self):
        self.add_basics()
        cli_args = DotDict({"address": None, "password": "my_password",
                            "debugging": True, "a dict": self.adict,
                            "a list": [*self.alist, DotDict],
                            "bytes_nums": self.bytes_nums})
        cli_args.creds = Cryptionary.from_subset_of(
            cli_args, "address", "debugging", "password",
            exclude_empties=True)
        return cli_args

    def get_soup(self):
        fpath = os.path.join(os.path.dirname(__file__),
                             'sample-email-body-structure.html')
        with open(fpath) as infile:
            htmltxt = infile.read()
        return BeautifulSoup(htmltxt, features="html.parser")

    def check_result(self, result, expected_result):
        succeeded = result == expected_result
        msg = f"Result `{result}` {'=' if succeeded else '!'}= " \
            f"expected `{expected_result}`"
        print(msg)
        assert succeeded
