#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-04-24
Updated: 2026-03-05
"""
# Import standard libraries
from collections.abc import Callable, Iterable
import datetime as dt
import pdb
import random
from typing import Any, cast, TypeVar

# Import third-party PyPI libraries
import bs4

# Import local custom libraries
from gconanpy.iters import Randoms
from gconanpy.meta import name_of
from gconanpy.strings import FancyString, StrCase, stringify
from gconanpy.testers import Tester
from gconanpy.trivial import always_true
from gconanpy.wrappers import WrapFunction


class TestFancyString(Tester):
    _T = TypeVar("_T")
    HELLO_WORLD = FancyString("hello world")

    def check_fromBeautifulSoup(self, soup: bs4.Tag, **expecteds: str
                                ) -> None:
        for el_name, first_tag in expecteds.items():
            el = cast(bs4.Tag, soup.find(el_name))
            self.check_ToString(FancyString.fromBeautifulSoup(
                el), str(el))
            self.check_ToString(FancyString.fromBeautifulSoup(
                el, tag="first"), first_tag)
            self.check_ToString(FancyString.fromBeautifulSoup(
                el, tag="last"), f"</{el.name}>")

    def check_map(self, expected: str, **kwargs) -> None:
        self.add_basics()
        self.check_result(stringify(self.adict, **kwargs), expected)

    def check_ToString(self, actual_result: FancyString, expected_result: str
                       ) -> None:
        self.check_result(actual_result, expected_result)
        assert type(actual_result) is FancyString

    def stringify_WrapFunction(self, call: Callable, pre: Iterable = [],
                               post: Iterable = [], **kwargs: Any) -> str:
        kwargstrs = [f"{k}={v}" for k, v in kwargs.items()]
        stringified = f"{name_of(WrapFunction)}(call={name_of(call)}, " \
            f"pre={pre}, post={post}, {', '.join(kwargstrs)})"
        return stringified

    def test_add(self) -> None:
        self.check_result(type(stringify("hi") + " there"), FancyString)
        # self.check_result(type("hi" + stringify(" there")), FancyString)  # TODO?

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

    def test_case(self) -> None:
        # CASES = get_args(StrCase)
        CODE_CASES: set[StrCase] = {
            "camel", "kebab", "macro", "pascal", "snake"}
        NORMAL_CASES: set[StrCase] = {"capitalize", "lower", "title", "upper"}
        EXAMPLES: dict[str, FancyString] = {k: FancyString(v) for k, v in {
            "camel": "thisIsCamelCase",
            "capitalize": "This is capitalized.",
            "kebab": "this-is-kebab-case",
            "lower": "this is lowercase.",
            "macro": "THIS_IS_MACRO_CASE",
            "pascal": "ThisIsPascalCase",
            "snake": "this_is_snake_case",
            "title": "This Is Title Case.",
            "upper": "THIS IS UPPERCASE."
        }.items()}

        CODE_2_NORMAL = {
            "kebab": "lower", "snake": "lower", "macro": "upper"
        }

        each_example: dict[StrCase, dict[StrCase, bool]] = {}
        for code_case in CODE_CASES:
            each_example[code_case] = {other_case: code_case == other_case
                                       for other_case in CODE_CASES}

            code2normal = CODE_2_NORMAL.get(code_case, "")
            for normal_case in NORMAL_CASES:
                each_example[code_case][normal_case] = \
                    normal_case == code2normal

        # print(each_example)

        for code_case, answers in each_example.items():
            example = EXAMPLES[code_case]

            print(example.to_case(code_case), end=" is ")
            assert example.to_case(code_case).is_case(code_case)
            print(code_case + " case.")

            for other_case, is_other_case in answers.items():
                print(f"{example} is " + ("" if is_other_case else "not ")
                        + other_case, end=" case")
                assert example.is_case(other_case) is is_other_case
                print(".")
                

    def test_capitalize(self) -> None:
        self.check_ToString(FancyString("hello").capitalize(), "Hello")

    def test_defaults(self) -> None:
        self.check_map("'a': 1, 'b': 2, and 'c': 3")

    def test_dt(self) -> None:
        moment = dt.datetime.now()
        self.check_ToString(stringify(moment), moment.isoformat(
            sep="_", timespec="seconds").replace(":", "-"))

    def test_enclose(self) -> None:
        self.check_ToString(FancyString("").enclosed_by("'"), "''")
        for args, out in {(None, "'"): "'", ("'", None): "'", (None, None): ""
                          }.items():
            self.check_ToString(FancyString("").enclosed_in(*args), out)

    def test_eq(self, n_tests: int = random.randint(5, 10)) -> None:
        for _ in range(n_tests):
            a_str = Randoms.randstr()
            assert FancyString(a_str) == a_str
            assert a_str == FancyString(a_str)

    def test_filepath(self) -> None:
        str_fpath = FancyString.filepath(
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

    def test_iter_kwargs(self) -> None:
        self.add_basics()
        LEN_TO_TRUNCATE = 10
        new_dict = Randoms.randict(min_val=LEN_TO_TRUNCATE, value_types=str)
        FancyString.fromMapping(new_dict, iter_kwargs=dict[str, Any](
            max_len=LEN_TO_TRUNCATE))  # TypeError: multiple 'max_len' values

    def test_join(self) -> None:
        joined = FancyString(" ").join(("hello", "world"))
        self.check_ToString(joined, "hello world")

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
            self.check_result(FancyString.fromCallable(
                WrapFunction, call=call, pre=pre, post=post, **kwargs),
                self.stringify_WrapFunction(call, pre, post, **kwargs))

    def test_rreplace(self, n: int = 50) -> None:
        OLD = " BAR"
        NEW = ""
        ABSENT = "not in the string"
        a_str = FancyString(OLD.join(("Foo", " baz", " hello", " world", "")))
        # a_str = FancyString("Foo BAR baz BAR hello BAR world BAR")
        self.check_ToString(a_str.rreplace(ABSENT, NEW), a_str)
        for i in Randoms.randints(min_n=n, max_n=n):
            self.check_ToString(a_str.rreplace(OLD, NEW, i),
                                NEW.join(a_str.rsplit(OLD, i)))
            self.check_ToString(a_str.rreplace(ABSENT, NEW, i), a_str)

    def test_quote(self) -> None:
        self.check_map('"a": 1, "b": 2, and "c": 3', quote='"')

    def test_quote_nums(self) -> None:
        self.check_map("'a': '1', 'b': '2', and 'c': '3'", quote_numbers=True)
        self.check_ToString(stringify({"a": 2.5}, quote_numbers=True),
                            "'a': '2.5'")

    def test_removeprefix(self) -> None:
        removed = self.HELLO_WORLD.removeprefix("hello ")
        self.check_ToString(removed, "world")

    def test_removesuffix(self) -> None:
        removed = self.HELLO_WORLD.removesuffix(" world")
        self.check_ToString(removed, "hello")

    def test_replace(self) -> None:
        replaced = self.HELLO_WORLD.replace("world", "there")
        self.check_ToString(replaced, "hello there")

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
        self.check_ToString(FancyString("hello").upper(), "HELLO")
