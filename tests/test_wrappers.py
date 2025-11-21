#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-04-24
Updated: 2025-11-19
"""
# Import standard libraries
from collections.abc import Callable, Generator, Iterable
import datetime as dt
import pdb
import random
import re
from typing import Any, cast, TypeVar

# Import third-party PyPI libraries
import bs4

# Import local custom libraries
from gconanpy.IO.web import URL
from gconanpy.iters import copy_range, invert_range, Randoms
from gconanpy.meta import name_of
from gconanpy.testers import Tester
from gconanpy.trivial import always_true
from gconanpy.wrappers import (Branches, Sets, SoupTree, stringify,
                               ToString, WrapFunction)


class TestSets(Tester):
    N_TESTS: int = 25
    randintsets: Callable[..., list[set[int]]] = \
        WrapFunction(Randoms.randintsets, min_n=10, max_n=20,
                     min_len=N_TESTS, max_len=N_TESTS)

    def asc_desc_Sets(self, n_tests: int = 20, max_int: int = 20,
                      ) -> Generator[tuple[Sets, Sets, Sets], None, None]:
        for each_int in Randoms.randints(min_n=n_tests, max_n=n_tests,
                                         min_int=2, max_int=max_int):
            asc_range = range(each_int)
            dsc_range = invert_range(asc_range)  # TODO FIX
            ascending = Sets[int]({a} for a in asc_range)
            assert ascending
            descending = Sets[int]({d} for d in dsc_range)
            assert descending
            both = Sets[int]({i, j} for i, j in zip(copy_range(asc_range),
                                                    copy_range(dsc_range)))
            assert both
            yield ascending, descending, both

    def test_differentiate_and_merge(self) -> None:
        sets = Sets[int](({1, 2, 3, 4, 5}, {4, 5, 6, 7, 8}, {6, 7, 8, 9, 10}))
        self.check_result(Sets[int](sets.differentiate()),
                          Sets[int](({1, 2, 3}, set(), {9, 10})))
        self.check_result(sets.merge(), set[int](range(1, 11)))

    def test_differentiate(self) -> None:
        for bigset in self.randintsets():
            randcount = Randoms.randcount()
            sets = Sets[int]((set(Randoms.randsublist(list(bigset)))
                              for _ in randcount))
            differentiated = sets.differentiate()
            for postdif in differentiated:
                for otherset in differentiated:
                    if postdif != otherset:
                        assert postdif.isdisjoint(otherset)

    def test_filter(self) -> None:
        sets = Sets[int](((1, 2, 3), (3, 4, 5, 6), (1, 9, 10)))
        self.check_result(Sets[int](sets.filter(lambda x: x > 5)),
                          Sets[int]((tuple(), (6, ), (9, 10))))

    def test_intersection(self) -> None:
        int_bounds = dict[str, int](min_int=-10, max_int=10)
        self.check_result(Sets[int](((1, 2, 3), (1, 4, 5), (1, 6, 7, 8),
                                     (1, 9, 10))).intersection(), {1})
        self.check_result(Sets[int](((1, 2, 3), (4, 5, 6), (6, 7, 8))
                                    ).intersection(), set())
        for set1 in self.randintsets(**int_bounds):
            others = Sets(Randoms.randintsets(**int_bounds))
            intersected = set(set1).copy()
            for eachset in (set1, *others):
                intersected.intersection_update(eachset)
            self.check_result(Sets((set1, *others)).intersection(),
                              intersected)

    def test_union_each(self) -> None:  # TODO FIX invert_range
        for ascending, descending, both in self.asc_desc_Sets():
            unioned = Sets(tuple(ascending.union_each(descending)))
            self.check_result(unioned, both)

    def test_unique(self) -> None:
        self.check_result(Sets(({1, 2}, {1, 3}, {1, 2, 4}, {1})
                               ).unique(), {3, 4})

        # Test that for Sets with no shared items, unique() == union()
        ints = set(Randoms.randints())  # get random unique integers
        intsets = Sets({i} for i in ints)  # split them, each in its own set
        self.check_result(intsets.union(), intsets.unique())

    def test_update_each(self) -> None:  # TODO FIX invert_range
        for ascending, descending, both in self.asc_desc_Sets():
            ascending.update_each(descending)
            self.check_result(ascending, both)


class TestSoupTree(Tester):
    def test_SoupTree_prettify(self) -> None:
        soup = self.get_soup()
        stree = SoupTree.from_soup(soup)
        branch = Branches()
        invalid = re.compile(f"({branch.T})(?:{branch.O})*"
                             f"({branch.I}|{branch.L}|{branch.T})")
        pretty = stree.prettify(branch=branch)
        assert invalid.match(pretty) is None


class TestStringify(Tester):
    _T = TypeVar("_T")
    HELLO_WORLD = ToString("hello world")

    def check_fromBeautifulSoup(self, soup: bs4.Tag, **expecteds: str
                                ) -> None:
        for el_name, first_tag in expecteds.items():
            el = cast(bs4.Tag, soup.find(el_name))
            self.check_ToString(ToString.fromBeautifulSoup(
                el), str(el))
            self.check_ToString(ToString.fromBeautifulSoup(
                el, tag="first"), first_tag)
            self.check_ToString(ToString.fromBeautifulSoup(
                el, tag="last"), f"</{el.name}>")

    def check_map(self, expected: str, **kwargs) -> None:
        self.add_basics()
        self.check_result(stringify(self.adict, **kwargs), expected)

    def check_ToString(self, actual_result: ToString, expected_result: str) -> None:
        self.check_result(actual_result, expected_result)
        assert type(actual_result) is ToString

    def stringify_WrapFunction(self, call: Callable, pre: Iterable = [],
                               post: Iterable = [], **kwargs: Any) -> str:
        kwargstrs = [f"{k}={v}" for k, v in kwargs.items()]
        stringified = f"{name_of(WrapFunction)}(call={name_of(call)}, " \
            f"pre={pre}, post={post}, {', '.join(kwargstrs)})"
        return stringified

    def test_add(self) -> None:
        self.check_result(type(stringify("hi") + " there"), ToString)
        # self.check_result(type("hi" + stringify(" there")), ToString)  # TODO?

    def test_affix(self) -> None:
        self.add_basics()
        affixes = ["{", "(", "[", "<",
                   "}", ")", "]", ">", "hello", " "]
        for _ in range(5):
            prefix = random.choice(affixes)
            suffix = random.choice(affixes)
            for an_iter in (self.alist, self.adict):
                stringified = stringify(an_iter, prefix=prefix, suffix=suffix)
                print(f"prefix: {prefix}\nsuffix: {suffix}\n"
                      f"stringified: {stringified}\n")
                assert str.startswith(stringified, prefix)
                assert str.endswith(stringified, suffix)

    def test_bytes(self) -> None:
        bytestring = b"hello"
        self.check_ToString(stringify(bytestring), "hello")

    def test_capitalize(self) -> None:
        self.check_ToString(ToString("hello").capitalize(),  # type: ignore
                            "Hello")  # TODO fix type annotation problem

    def test_defaults(self) -> None:
        self.check_map("'a': 1, 'b': 2, and 'c': 3")

    def test_dt(self) -> None:
        moment = dt.datetime.now()
        self.check_ToString(stringify(moment), moment.isoformat(
            sep="_", timespec="seconds").replace(":", "-"))

    def test_enclose(self) -> None:
        self.check_ToString(ToString("").enclosed_by("'"), "''")
        for args, out in {(None, "'"): "'", ("'", None): "'", (None, None): ""
                          }.items():
            self.check_ToString(ToString("").enclosed_in(*args), out)

    def test_filepath(self) -> None:
        str_fpath = ToString.filepath(
            "/home/gconan", file_name="delete-this-git-difference",
            file_ext=".txt", put_date_after="_", max_len=48)
        expected = "/home/gconan/delete-this-git-diff_" \
            f"{dt.date.today().isoformat()}.txt"
        self.check_ToString(str_fpath, expected)

    def test_fromAny_Callable(self) -> None:
        for fn in (all, any, callable, cast, dict, isinstance, issubclass,
                   list, map, name_of, reversed, str, stringify, tuple, type):
            self.check_ToString(stringify(fn), name_of(fn, "__qualname__"))

    def test_fromAny_str(self) -> None:
        for astr in ("hello", "world"):
            self.check_ToString(stringify(astr, prefix="[", suffix="]"),
                                f"[{astr}]")

    def test_fromBeautifulSoup_1(self) -> None:
        soup = self.get_soup()
        expecteds = {"a": "<a href='https://google.com'>",
                     "table": "<table>", "tr": "<tr>"}
        self.check_fromBeautifulSoup(soup, **expecteds)

    def test_fromBeautifulSoup_2(self) -> None:
        raw = "<html lang='en'><body><p class='test'>Hello <a href=" \
            "'https://google.com'>world</a></p></body></html>"
        soup = bs4.BeautifulSoup(raw, "html.parser")
        expecteds = {"a": "<a href='https://google.com'>",
                     "p": "<p class='test'>", "body": "<body>",
                     "html": "<html lang='en'>"}
        self.check_fromBeautifulSoup(soup, **expecteds)

    def test_join(self) -> None:
        joined = ToString(" ").join(("hello", "world"))
        self.check_ToString(joined, "hello world")  # type: ignore # TODO

    def test_join_on(self) -> None:
        self.check_map("'a'=1, 'b'=2, and 'c'=3", join_on="=")

    def test_lastly(self) -> None:
        self.check_map("'a': 1, 'b': 2, 'c': 3", lastly="")

    def test_max_len(self) -> None:
        self.check_map("'a': 1, 'b': 2...", max_len=17)

    def test_none(self) -> None:
        self.check_ToString(stringify(None), "")

    def test_fromCallable(self) -> None:
        self.add_basics()
        for _ in range(10):
            pre = Randoms.randsublist(self.alist)
            post = Randoms.randsublist(self.alist)
            kwargs = self.adict
            call = always_true
            self.check_result(ToString.fromCallable(
                WrapFunction, call=call, pre=pre, post=post, **kwargs),
                self.stringify_WrapFunction(call, pre, post, **kwargs))

    def test_rreplace(self, n: int = 50) -> None:
        OLD = " BAR"
        NEW = ""
        ABSENT = "not in the string"
        a_str = ToString(OLD.join(("Foo", " baz", " hello", " world", "")))
        # a_str = ToString("Foo BAR baz BAR hello BAR world BAR")
        self.check_ToString(a_str.rreplace(ABSENT, NEW), a_str)
        for i in Randoms.randints(min_n=n, max_n=n):
            self.check_ToString(a_str.rreplace(OLD, NEW, i),
                                NEW.join(a_str.rsplit(OLD, i)))
            self.check_ToString(a_str.rreplace(ABSENT, NEW, i), a_str)

    def test_quote(self) -> None:
        self.check_map('"a": 1, "b": 2, and "c": 3', quote='"')

    def test_quote_nums(self) -> None:
        self.check_map("'a': '1', 'b': '2', and 'c': '3'", quote_numbers=True)
        self.check_ToString(stringify(dict(a=2.5), quote_numbers=True),
                            "'a': '2.5'")

    def test_removeprefix(self) -> None:
        removed = self.HELLO_WORLD.removeprefix("hello ")
        self.check_ToString(removed, "world")  # type: ignore # TODO

    def test_removesuffix(self) -> None:
        removed = self.HELLO_WORLD.removesuffix(" world")
        self.check_ToString(removed, "hello")  # type: ignore # TODO

    def test_replace(self) -> None:
        replaced = self.HELLO_WORLD.replace("world", "there")
        self.check_ToString(replaced, "hello there")  # type: ignore # TODO

    def test_replace_all(self) -> None:
        self.add_basics()
        str_list = stringify(self.alist)
        replacements = {",": "", "1": "6", "4": "four", " and": ""}
        self.check_ToString(str_list.replace_all(replacements),
                            "6 2 3 four 5")

    def test_sub(self) -> None:
        self.add_basics()
        str_list = stringify(self.alist)
        self.check_ToString(str_list - "3, 4, and 5", "1, 2, ")
        self.check_ToString(str_list - "4, and 5", "1, 2, 3, ")
        self.check_ToString(str_list - "4, and", str_list)
        self.check_ToString(str_list - None, str_list)

    def test_sep(self) -> None:
        self.check_map("'a': 1; 'b': 2; and 'c': 3", sep="; ")

    def test_upper(self) -> None:
        self.check_ToString(ToString("hello").upper(),  # type: ignore
                            "HELLO")  # TODO fix type annotation problem


class TestURL(Tester):
    GDOCS_URL = "https://docs.google.com/document/d/a1b2c3/edit" \
        "?tab=t.abc123&heading=h.def456&key=12345"

    def test_from_parts(self):
        url = URL.from_parts("docs.google.com", "document",
                             "d", "a1b2c3", "edit",
                             tab="t.abc123", heading="h.def456", key=12345)
        self.check_result(str(url), self.GDOCS_URL)

    def test_without_params(self):
        url = URL(self.GDOCS_URL)
        self.check_result(url.without_params(),
                          self.GDOCS_URL.split("?", 1)[0])
