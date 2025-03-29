#!/usr/bin/env python3

"""
Classes to inspect/examine/unwrap complex/nested data structures.
Extremely useful and convenient for debugging.
Greg Conan: gregmconan@gmail.com
Created: 2025-03-28
Updated: 2025-03-28
"""

# Import local custom libraries
from gconanpy.debug import *
from gconanpy.dissectors import *
from gconanpy.finders import *
from gconanpy.maps import *
from gconanpy.seq import *


class Tester(Debuggable):
    def __init__(self, debugging: bool = False):
        self.debugging = debugging

        self.adict = dict(a=1, b=2, c=3)
        self.alist = [1, 2, 3, 4, 5]
        self.bytes_nums = b'7815 11461 11468 11507 11516 17456 17457 17460'

    def test1(self):
        rolled = RollingPin().flatten(('OK', [self.bytes_nums]))
        self.check_result(rolled, ['OK', self.bytes_nums])

    def test2(self):
        self.cli_args = DotDict({"address": None, "password": "my_password",
                                 "debugging": True, "a dict": self.adict,
                                 "a list": [*self.alist, Peeler],
                                 "bytes_nums": self.bytes_nums})
        self.cli_args.creds = Cryptionary.from_subset_of(
            self.cli_args, "address", "debugging", "password",
            exclude_empties=True)
        cored = Corer(debugging=True).core(self.cli_args)
        self.check_result(cored, self.bytes_nums)

    def check_result(self, result, expected_result):
        succeeded = result == expected_result
        msg = f"`{expected_result}` {'=' if succeeded else '!'}= `{result}`"
        if succeeded:
            print(msg)
        else:
            self.debug_or_raise(ValueError(msg), locals())


def main():
    tester = Tester(debugging=True)
    tester.test1()
    tester.test2()


if __name__ == "__main__":
    main()
