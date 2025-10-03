#!/usr/bin/env python3

"""
Base classes for unit tests in ../tests/ dir
Greg Conan: gregmconan@gmail.com
Created: 2025-03-28
Updated: 2025-10-02
"""
# Import standard libraries
from abc import ABC
from collections.abc import Callable, Hashable
import datetime as dt
import os
from types import ModuleType
from typing import Any, TypeVar

# Import third-party PyPI libraries
from bs4 import BeautifulSoup

# Import local custom libraries
try:
    from gconanpy import mapping, ROOT_DIR
    from gconanpy.access.attributes import AttrsOf
    from gconanpy.extend import classes_in_module
    from gconanpy.iters import powers_of_ten
    from gconanpy.iters.filters import MapSubset
    from gconanpy.meta import has_method, name_of
    from gconanpy.trivial import always_false, always_none, always_true
except (ImportError, ModuleNotFoundError):
    from . import mapping, ROOT_DIR
    from access.attributes import AttrsOf
    from extend import classes_in_module
    from iters import powers_of_ten
    from iters.filters import MapSubset
    from meta import has_method, name_of
    from trivial import always_false, always_none, always_true

# Constant: Paragraph about Lorem ipsum to test Regextract &c
LIPSUM = """Lorem ipsum (/ˌlɔ:.rəm 'ip.səm/ LOR-əm IP-səm) is a dummy or 
placeholder text commonly used in graphic design, publishing, and web 
development. Its purpose is to permit a page layout to be designed, 
independently of the copy that will subsequently populate it, or to 
demonstrate various fonts of a typeface without meaningful text that 
could be distracting. Lorem ipsum is typically a corrupted version of 
De finibus bonorum et malorum, a 1st-century BC text by the Roman 
statesman and philosopher Cicero, with words altered, added, and 
removed to make it nonsensical and improper Latin. The first two words 
are the truncation of dolorem ipsum ('pain itself'). Versions of the 
Lorem ipsum text have been used in typesetting since the 1960s, when 
advertisements for Letraset transfer sheets popularized it.[1] Lorem 
ipsum was introduced to the digital world in the mid-1980s, when Aldus 
employed it in graphic and word-processing templates for its desktop 
publishing program PageMaker. Other popular word processors, including 
Pages and Microsoft Word, have since adopted Lorem ipsum,[2] as have 
many LaTeX packages,[3][4][5] web content managers such as Joomla! and 
WordPress, and CSS libraries such as Semantic UI."""


class Tester(ABC):
    _Dict = TypeVar("_Dict", bound=dict)  # _Dict is type(cli_args)
    _In = TypeVar("_In")
    _Out = TypeVar("_Out")
    ERR_OF = {"__setitem__": KeyError, "__setattr__": AttributeError}
    SOUP_FPATH = os.path.join(ROOT_DIR, "tests",
                              "sample-email-body-structure.html")
    TRIVIALS = {always_none: None, always_true: True, always_false: False}

    def add_basics(self):
        """ Add generic values to use in tester methods (namely `adict`, \
            `alist`, and `bytes_nums`) as attributes of `self`. """
        self.adict = dict(a=1, b=2, c=3)
        self.alist = [1, 2, 3, 4, 5]
        self.bytes_nums = b"7815 11461 11468 11507 11516 17456 17457 17460 " \
            b"7815 11461 11468 11507 11516 17456 17457 17460 12345 12345 " \
            b"7815 11461 11468 11507 11516 17456 17457 17460 12345 12345 " \
            b"7815 11461 11468 11507 11516 17456 17457 17460 12345 12345 "

    def build_cli_args(self, _class: type[_Dict], _creds_type: type[dict]
                       ) -> _Dict:
        """ Create a nested Mapping with various arbitrary values to use to \
            test data extraction methods. It mimics the arguments that a \
            user might provide via the command line ("address", "password", \
            and "debugging") plus a few other arbitrary values of various \
            types ("a list", "a dict", and "bytes_nums").

        :param _class: type[_Dict], type of dictionary to return.
        :param _creds_type: type[dict], type of dictionary to insert pretend \
            user credentials into, mapped to the key "creds".
        :return: _Dict, dictionary (of the `_class` type) with all of the \
            keys named in this docstring.
        """
        self.add_basics()
        cli_args = _class({"address": None, "password": "my_password",
                           "debugging": True, "a dict": self.adict,
                           "a list": [*self.alist, _class],
                           "to remove": True, "bytes_nums": self.bytes_nums})
        cli_args["creds"] = MapSubset(
            keys_are={"address", "debugging", "password"}, values_arent={None}
        ).of(cli_args, as_type=_creds_type)
        del cli_args["to remove"]  # Added to test Cryptionary.__del__
        return cli_args

    @classmethod
    def cannot_alter(cls, an_obj: Any, *names: Hashable) -> bool:
        """
        :param an_obj: Any, object with protected/immutable attributes
        :param names: Iterable[Hashable], `an_obj` protected attribute names
        :return: bool, True if `an_obj` cannot modify any of the protected \
            attributes named in `names`; else False 
        """
        result = True
        for method, err_type in cls.ERR_OF.items():
            result = has_method(an_obj, method)
            for name in names:
                if result:
                    try:
                        getattr(an_obj, method)(name, "NOT ALLOWED")
                        result = False
                    except err_type:
                        pass
        return result

    def check_result(self, actual_result: Any, expected_result: Any) -> None:
        """ Assert that `actual_result == expected_result`. If that's False, \
            then print a statement saying so. """
        if actual_result != expected_result:
            print(f"Result `{actual_result}` != expected"
                  f"`{expected_result}`")
            raise AssertionError

    def get_soup(self, fpath: str = SOUP_FPATH) -> BeautifulSoup:
        """ Load an example HTML file into a `BeautifulSoup` object.

        :param fpath: str, HTML file to load; defaults to SOUP_FPATH
        :return: BeautifulSoup loaded from `fpath`
        """
        with open(fpath) as infile:
            htmltxt = infile.read()
        return BeautifulSoup(htmltxt, features="html.parser")

    def xfm_test(self, func: Callable[[_In], _Out],
                 *pre_and_post: tuple[_In, _Out], **kwargs: Any) -> None:
        """ For every input-output pair in `pre_and_post`, assert that \
            calling `func` with the input and `**kwargs` returns the output.

        :param func: Callable[[_In: Any, **kwargs], _Out: Any], function to \
            repeatedly test; it should turn each input object into each \
            corresponding output object.
        :param pre_and_post: Iterable[tuple[_In, _Out]] listing the input \
            and output of each test to run; the first element is the input \
            to `func` and the second element is the expected output.
        :param kwargs: Mapping[str, Any], `func` keyword arguments
        """
        for pre, post in pre_and_post:
            self.check_result(func(pre, **kwargs), post)


class TimeTester:
    def repeat_tests(self, tester: Tester, n: int):
        """ Run `tester.test_*()` `n` times.

        :param tester: Tester
        :param n: int, number of times to run every method in `tester` that \
            starts with `test_`.
        """
        # start_time = dt.datetime.now()
        for _ in range(n):
            for method_name, method_to_test in AttrsOf(tester).methods():
                if method_name.startswith("test_"):
                    method_to_test()
        # elapsed = dt.datetime.now() - start_time
        # print(f"Time elapsed running {name_of(tester)} methods {n} times: {elapsed}")

    def test_all(self, test_module: ModuleType,
                 n_tests_orders_of_magnitude: int = 4) -> None:
        """ Run every `test_*` method of `test_module` many times.

        :param test_module: ModuleType, a module in the `tests/` directory.
        :param n_tests_orders_of_magnitude: int, the power to raise 10 to \
            in order to get the number of tests to run; defaults to 4 to run \
            10,000 tests.
        """
        test_Ns = powers_of_ten(n_tests_orders_of_magnitude)
        for class_name, tester_class in classes_in_module(test_module):
            if class_name.startswith("Test"):
                for n in test_Ns:
                    self.repeat_tests(tester_class(), n)

    def time_method(self, method_name: str, n_tests_orders_of_magnitude: int,
                    *testers: Tester) -> str:
        """ Time how long it takes for each of the different `testers` to \
            run a method called `method_name`. 

        :param method_name: str naming the method of all `testers` to run \
            many times.
        :param n_tests_orders_of_magnitude: int, the power to raise 10 to \
            in order to get the number of tests to run for all `testers`.
        :param testers: Iterable[Tester], objects to repeatedly run the \
            specified test method of.
        :return: str, human-readable description of how long it took for \
            each of the `testers` to run the named method.
        """
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
        for slower, slow_time in MapSubset(keys_arent=faster).of(avg_of).items():
            ratios.append(f"{slow_time/min_avg} times faster than {slower}")
        return f"{faster} is {' and '.join(ratios)}."
