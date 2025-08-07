#!/usr/bin/env python3

"""
Base classes for unit tests in ../tests/ dir
Greg Conan: gregmconan@gmail.com
Created: 2025-03-28
Updated: 2025-07-28
"""
# Import standard libraries
from abc import ABC
from collections.abc import Hashable, Iterable
import datetime as dt
import os
from types import ModuleType
from typing import Any, TypeVar

# Import third-party PyPI libraries
from bs4 import BeautifulSoup

# Import local custom libraries
try:
    from attributes import AttrsOf
    from extend import classes_in_module
    from iters import MapSubset, powers_of_ten
    from iters.find import ErrIterChecker
    from . import mapping, ROOT_DIR
    from meta import has_method, name_of
except (ImportError, ModuleNotFoundError):
    from gconanpy.attributes import AttrsOf
    from gconanpy.extend import classes_in_module
    from gconanpy.iters.find import ErrIterChecker
    from gconanpy.iters import MapSubset, powers_of_ten
    from gconanpy import mapping, ROOT_DIR
    from gconanpy.meta import has_method, name_of


class Tester(ABC):
    _Dict = TypeVar("_Dict", bound=dict)  # _Dict == type(cli_args)
    ERR_OF = {"__setitem__": KeyError, "__setattr__": AttributeError}

    def add_basics(self):
        self.adict = dict(a=1, b=2, c=3)
        self.alist = [1, 2, 3, 4, 5]
        self.bytes_nums = b"7815 11461 11468 11507 11516 17456 17457 17460 " \
            b"7815 11461 11468 11507 11516 17456 17457 17460 12345 12345 " \
            b"7815 11461 11468 11507 11516 17456 17457 17460 12345 12345 " \
            b"7815 11461 11468 11507 11516 17456 17457 17460 12345 12345 "

    def build_cli_args(self, _class: type[_Dict], _creds_type: type[dict]
                       ) -> _Dict:
        self.add_basics()
        cli_args = _class({"address": None, "password": "my_password",
                           "debugging": True, "a dict": self.adict,
                           "a list": [*self.alist, _class],
                           "to remove": True, "bytes_nums": self.bytes_nums})
        cli_args["creds"] = MapSubset(
            keys={"address", "debugging", "password"},
            values={None}, include_keys=True, include_values=False
        ).of(cli_args, as_type=_creds_type)
        del cli_args["to remove"]  # test Cryptionary.__del__
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
        fpath = os.path.join(ROOT_DIR, "tests",
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


class TimeTester:
    def repeat_tests(self, tester: Tester, n: int):
        # start_time = dt.datetime.now()
        for _ in range(n):
            for method_name, method_to_test in AttrsOf(tester).methods():
                if method_name.startswith("test_"):
                    method_to_test()
        # elapsed = dt.datetime.now() - start_time
        # print(f"Time elapsed running {name_of(tester)} methods {n} times: {elapsed}")

    def test_all(self, test_module: ModuleType,
                 n_tests_orders_of_magnitude: int = 4) -> None:
        test_Ns = powers_of_ten(n_tests_orders_of_magnitude)
        for class_name, tester_class in classes_in_module(test_module):
            if class_name.startswith("Test"):
                for n in test_Ns:
                    self.repeat_tests(tester_class(), n)

    def time_method(self, method_name: str, n_tests_orders_of_magnitude: int,
                    *testers: Tester) -> str:
        avg_of = dict()
        elapsed = dict()  # {name_of(which): 0.0 for which in tester_classes}
        test_Ns = powers_of_ten(n_tests_orders_of_magnitude)
        n_tests = sum(test_Ns)

        for tester in testers:
            tester_name = name_of(tester)
            start_time = dt.datetime.now()
            for n in test_Ns:
                for _ in range(n):
                    getattr(tester, method_name)()
            elapsed[tester_name] = (
                dt.datetime.now() - start_time).total_seconds()

            avg_of[tester_name] = elapsed[tester_name] / n_tests
            print(f"{tester_name} took {avg_of[tester_name]} seconds")

        which_avg = mapping.invert(avg_of)
        min_avg = min(which_avg)
        faster = which_avg[min_avg]
        ratios = list()
        for slower, slow_time in MapSubset(keys={faster}, include_keys=False
                                           ).of(avg_of).items():
            ratios.append(f"{slow_time/min_avg} times faster than {slower}")
        return f"{faster} is {' and '.join(ratios)}."
