#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-07-06
Updated: 2025-07-07
"""
# Import standard libraries
from collections.abc import Sequence
from typing import Any, TypeVar

# Import local custom libraries
from gconanpy.seq import Recursively
from gconanpy.testers import Tester


class TestSeq(Tester):
    NEST_AT: int = -1
    NEW_VAL: Any = "hello"

    @classmethod
    def nested_list(cls, levels: int = 3, nest_at: int = NEST_AT,
                    to_nest: Any = NEW_VAL, others: Sequence = tuple()
                    ) -> list:
        return [*others[:nest_at], to_nest if levels < 1 else cls.nested_list(
            levels - 1, nest_at, to_nest, *others
        ), *others[nest_at:]]

    def get_nested_lists(self, ix: int = NEST_AT, diff: Any = NEW_VAL
                         ) -> tuple[list, list]:
        self.add_basics()
        nested = self.nested_list()
        expected = nested.copy()
        expected[ix][ix][ix] = diff
        return nested, expected

    def test_Recursively_setitem(self) -> None:
        IX = self.NEST_AT
        VAL = self.NEW_VAL
        nested, expected = self.get_nested_lists(IX, VAL)
        Recursively.setitem(nested, (IX, IX, IX), VAL)
        self.check_result(nested, expected)

    def test_Recursively_getitem(self) -> None:
        IX = self.NEST_AT
        VAL = self.NEW_VAL
        _, nested = self.get_nested_lists(IX, VAL)
        self.check_result(Recursively.getitem(nested, (IX, IX, IX)), VAL)
