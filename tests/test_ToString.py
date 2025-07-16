#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-04-24
Updated: 2025-07-15
"""
# Import standard libraries
from collections.abc import Callable, Iterable
import datetime as dt
import random
from typing import Any, cast, TypeVar

# Import third-party PyPI libraries
import bs4

# Import local custom libraries
from gconanpy.IO.web import URL
from gconanpy.meta.funcs import name_of
from gconanpy.ToString import stringify, ToString
from gconanpy.testers import Randoms, Tester
from gconanpy.trivial import always_true
from gconanpy.wrap import WrapFunction


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

    def stringify_WrapFunction(self, call: Callable, pre: Iterable = list(),
                               post: Iterable = list(), **kwargs: Any) -> str:
        kwargstrs = [f"{k}={v}" for k, v in kwargs.items()]
        stringified = f"{name_of(WrapFunction)}(call={name_of(call)}, " \
            f"pre={pre}, post={post}, {', '.join(kwargstrs)})"
        return stringified

    def test_add(self) -> None:
        # TODO Why doesn't VSCode recognize x as a ToString instance?
        x = ToString("hello") - "o"
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
        for i in Randoms.randints(min_len=n, max_len=n):
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
