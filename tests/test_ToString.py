#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-04-24
Updated: 2025-06-02
"""
# Import standard libraries
import datetime as dt
import random

# Import local custom libraries
from gconanpy.IO.web import URL
from gconanpy.ToString import stringify, ToString
from tests.testers import Tester


class TestStringify(Tester):
    HELLO_WORLD = ToString("hello world")

    def check_map(self, expected: str, **kwargs) -> None:
        self.add_basics()
        self.check_result(stringify(self.adict, **kwargs), expected)

    def check_ToString(self, actual_result: ToString, expected_result: str) -> None:
        self.check_result(actual_result, expected_result)
        assert type(actual_result) is ToString

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

    def test_defaults(self) -> None:
        self.check_map("'a': 1, 'b': 2, and 'c': 3")

    def test_dt(self) -> None:
        moment = dt.datetime.now()
        self.check_ToString(stringify(moment), moment.isoformat(
            sep="_", timespec="seconds").replace(":", "-"))

    def test_filepath(self) -> None:
        str_fpath = ToString.filepath(
            "/home/gconan", file_name="delete-this-git-difference",
            file_ext=".txt", put_date_after="_", max_len=48)
        expected = "/home/gconan/delete-this-git-diff_" \
            f"{dt.date.today().isoformat()}.txt"
        self.check_ToString(str_fpath, expected)

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

    def test_replacements(self) -> None:
        self.add_basics()
        str_list = stringify(self.alist)
        replacements = {",": "", "1": "6", "4": "four", " and": ""}
        self.check_ToString(str_list.replacements(replacements),
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
