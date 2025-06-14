#!/usr/bin/env python3

"""
Classes that parse strings and text data, especially using Regex.
Greg Conan: gregmconan@gmail.com
Created: 2025-05-24
Updated: 2025-06-10
"""
# Import standard libraries
from collections.abc import Container, Generator
import re
from typing import Any

# Import third-party PyPI libraries
import inflection
import regex

# Import local custom libraries
try:
    import mapping
except ModuleNotFoundError:  # TODO DRY?
    from gconanpy import mapping


class Abbreviator:

    @staticmethod
    def abbreviate(name: str, max_len: int, **shortenings: str) -> str:
        for old, new in shortenings.items():
            if len(name) <= max_len:
                break
            else:
                name = name.replace(old, new).strip()
        return name


class Abbreviations(Abbreviator):
    def __init__(self, **shortenings: str) -> None:
        self.shortenings = shortenings

    def abbreviate(self, name: str, max_len: int) -> str:
        return super().abbreviate(name, max_len, **self.shortenings)


class Regextract:
    _NOT_LETTERS = r"[^a-zA-Z]"
    _PARENTHETICALS = r"""\((  # Get everything after the opening parenthesis
        ?:[^()]+|(?R) # Nested parentheticals don't get their own groups
        )*+  # Match everything possible inside the outermost parentheses
        \)"""  # Get everything before the closing parenthesis
    # _PARENTHETICALS = r"\((?:[^()]*(?R)?)*+\)"  # NOTE Functionally same?

    @classmethod
    def iter_parentheticals(cls, txt: str) -> Generator[regex.Match[str], None, None]:
        """ Get all parentheticals, ignoring nested parentheticals.
        Adapted from https://stackoverflow.com/a/35271017

        :param txt: str, _description_
        :yield: Generator[regex.Match, None, None], _description_
        """
        yield from regex.finditer(cls._PARENTHETICALS, txt)

    @classmethod
    def letters_in(cls, txt: str) -> str:
        return re.sub(cls._NOT_LETTERS, "", txt)

    @classmethod
    def parentheticals_in(cls, txt: str) -> list:
        return regex.findall(cls._PARENTHETICALS, txt, flags=re.X)

    @staticmethod
    def parse(pattern: re.Pattern, txt: str, default: Any = None,
              exclude: Container = set()) -> dict[str, str | None]:
        """ _summary_

        :param pattern: re.Pattern to find matches of in `txt`
        :param txt: str to scan through looking for matches to the `pattern`
        :param default: Any,_description_, defaults to None
        :param exclude: Container of values to exclude from the returned dict
        :return: dict[str, str | None], _description_
        """
        parsed = pattern.search(txt)
        parsed = parsed.groupdict(default=default) if parsed else dict()
        return mapping.Subset(keys=parsed.keys(), include_keys=True,
                              values=exclude, include_values=False).of(parsed)


class DunderParser:
    _ANY = r"(?P<name>.*)"  # Anything (to get method names)

    _DUNDER = r"(?:\_{2})"  # Double underscore regex token

    _PREFIXES = r"(?P<prefixes>.*_)*"  # e.g. "class" in __class_getitem__

    # Match the name of core operation dunder methods: getitem, delattr, etc
    _CORE_OP = r"""(?P<verb>[gs]et|del)  # "get", "set", or "del"
        (?P<noun>[a-zA-Z]+)"""  # what is being accessed or modified

    # Match other operation dunder method names: sizeof, subclasscheck, etc.
    _OTHER_OP = r"""(?P<subject>[a-zA-Z]+)
        (?P<predicate>of|name|check|size|hook)"""

    def __init__(self) -> None:
        self.CoreOp = self._dundermatch(self._CORE_OP)
        self.OtherOp = self._dundermatch(self._OTHER_OP)
        self.AnyDunder = self._dundermatch(self._ANY, pfx="")

    @classmethod
    def _dundermatch(cls, reg_str: str, pfx: str = _PREFIXES) -> re.Pattern:
        return re.compile(f"^{cls._DUNDER}{pfx}{reg_str}{cls._DUNDER}$", re.X)

    def parse(self, dunder_name: str) -> list[str]:
        # First, try to match dunder_name to a core operation method name
        matched = Regextract.parse(self.CoreOp, dunder_name)
        if matched:
            words = [matched["verb"], matched["noun"]]

        # Second, try to match dunder_name to another operation method name
        else:
            matched = Regextract.parse(self.OtherOp, dunder_name)
            if matched:
                words = [matched["subject"], matched["predicate"]]

        # Otherwise, just trim the double underscores in dunder_name and \
        # split on single underscores
            else:
                words = list()
        if not words:
            matched = Regextract.parse(self.AnyDunder, dunder_name)
            if matched:
                words = matched["name"].split("_")  # type: ignore
            else:
                words = [dunder_name]

        # If any words preceded the operation name, then prepend those
        else:
            pfxs = matched.get("prefixes")
            if pfxs:
                words = pfxs.split("_")[:-1] + words

        return words  # type: ignore

    def pascalize(self, dunder_name: str):
        """ Given a dunder method/attribute name such as `__getitem__`, \
            `__delattr__`, or `__slots__`, convert that method/attribute \
            name into PascalCase and capitalize all of the abbreviated words \
            in the name.

        :param dunder_name: str naming a Python dunder attribute/method
        :return: str, `dunder_name` in PascalCase capitalizing its words
        """
        return inflection.camelize("_".join(self.parse(dunder_name)))
