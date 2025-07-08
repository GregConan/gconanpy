#!/usr/bin/env python3

"""
Matcher base class
Greg Conan: gregmconan@gmail.com
Created: 2025-06-28
Updated: 2025-06-29
"""
# Import standard libraries
from collections.abc import Iterable, Mapping, Sequence
import itertools
from typing import Any


class MatcherBase(dict[tuple[bool, ...], Any]):
    _CC = tuple[bool, ...]
    _KT = tuple[str, ...] | list[str] | dict | \
        _CC | str | bool | list[bool] | None
    conditions: Sequence[str]
    ConditionCombo: type[_CC]

    def __init__(self, matches: Mapping[_KT, Any] = dict()
                 ) -> None:
        for conds in itertools.product((True, False),
                                       repeat=len(self.conditions)):
            key = self.as_conds_combo(conds)
            self[key] = matches.get(key, None)

    @classmethod
    def as_conds_combo(cls, conds: _KT) -> tuple[bool, ...]:
        match conds:
            case dict():
                combo = cls.ConditionCombo(**conds)
            case tuple() | list():
                conds_types = {type(c) for c in conds}
                if conds_types == {bool}:
                    combo = cls.ConditionCombo(**{cls.conditions[i]: conds[i]
                                                  for i in range(len(conds))})
                elif conds_types == {str}:
                    combo = cls.conds_in(conds)
                else:
                    raise TypeError(f"Cannot parse conditions {conds}")
            case str():
                combo = cls.conds_in((conds, )) if conds in cls.conditions \
                    else cls.conds_in(conds.split())
            case cls.ConditionCombo():
                combo = conds
            case bool() | None:
                combo = cls.ConditionCombo(**{
                    k: bool(conds) for k in cls.conditions})
        return combo

    @classmethod
    def conds_in(cls, conds: Iterable) -> _CC:
        return cls.ConditionCombo(**{cond: cond in conds
                                     for cond in cls.conditions})
