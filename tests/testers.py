#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-03-28
Updated: 2025-03-30
"""
# Import standard libraries
from abc import ABC

# Import local custom libraries
from gconanpy.maps import Cryptionary, DotDict


class Tester(ABC):

    def add_basics(self):
        self.adict = dict(a=1, b=2, c=3)
        self.alist = [1, 2, 3, 4, 5]
        self.bytes_nums = b"7815 11461 11468 11507 11516 17456 17457 17460"

    def add_cli_args(self):
        self.add_basics()
        self.cli_args = DotDict({"address": None, "password": "my_password",
                                 "debugging": True, "a dict": self.adict,
                                 "a list": [*self.alist, DotDict],
                                 "bytes_nums": self.bytes_nums})
        self.cli_args.creds = Cryptionary.from_subset_of(
            self.cli_args, "address", "debugging", "password",
            exclude_empties=True)

    def check_result(self, result, expected_result):
        succeeded = result == expected_result
        msg = f"`{expected_result}` {'=' if succeeded else '!'}= `{result}`"
        print(msg)
        assert succeeded
