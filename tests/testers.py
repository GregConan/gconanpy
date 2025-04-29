#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-03-28
Updated: 2025-04-16
"""
# Import standard libraries
from abc import ABC
from collections.abc import Hashable, Iterable
import os
import pdb
from typing import Any

# Import third-party PyPI libraries
from bs4 import BeautifulSoup

# Import local custom libraries
from gconanpy.find import ErrIterChecker
from gconanpy.maps import Cryptionary, DotDict, MapSubset
from gconanpy.metafunc import has_method


class Tester(ABC):
    ERR_OF = {"__setitem__": KeyError, "__setattr__": AttributeError}

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
        cli_args.creds = MapSubset(
            keys={"address", "debugging", "password"},
            values={None}, include_keys=True, include_values=False
        ).of(cli_args, as_type=Cryptionary)
        return cli_args

    @classmethod
    def cannot_alter(cls, an_obj, *names: Hashable) -> bool:
        result = True
        for method, err_type in cls.ERR_OF.items():
            result = cls.obj_has_but_cannot(an_obj, method, names, err_type)
        return result

    def check_result(self, actual_result: Any, expected_result: Any) -> None:
        succeeded = actual_result == expected_result
        msg = f"Result `{actual_result}` {'=' if succeeded else '!'}= " \
            f"expected `{expected_result}`"
        print(msg)
        assert succeeded

    def get_soup(self):
        fpath = os.path.join(os.path.dirname(__file__),
                             'sample-email-body-structure.html')
        with open(fpath) as infile:
            htmltxt = infile.read()
        return BeautifulSoup(htmltxt, features="html.parser")

    @staticmethod
    def obj_has_but_cannot(an_obj: Any, method: str,
                           attr_names: Iterable[Hashable],
                           *catch: type[BaseException]) -> bool:
        result = has_method(an_obj, method)
        with ErrIterChecker(attr_names, not result, *catch) as check:
            while check.is_not_ready():
                getattr(an_obj, method)(next(check), "NOT ALLOWED")
                result = False
                check.is_done = True
        return result
