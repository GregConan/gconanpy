#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-03-25
Updated: 2025-03-25
"""
# Import standard libraries
import builtins
import datetime as dt
import pdb
import sys
from typing import Any, Iterable, List, Mapping


class ToString(str):
    NoneType = type(None)

    def enclosed_by(self, affix: str):
        return self.that_ends_with(affix).that_starts_with(affix)

    @classmethod
    def from_datetime(cls, moment: dt.date | dt.time | dt.datetime,
                      sep: str = "_", timespec: str = "seconds",
                      replace: Mapping[str, str] = {":": "-"}):
        match type(moment):
            case dt.date:
                stringified = dt.date.isoformat(moment)
            case dt.time:
                stringified = dt.time.isoformat(moment, timespec=timespec)
            case dt.datetime:
                stringified = dt.datetime.isoformat(moment, sep=sep,
                                                    timespec=timespec)
        for to_replace, replace_with in replace.items():
            stringified = stringified.replace(to_replace, replace_with)
        return cls(stringified)

    @classmethod
    def from_iterable(cls, an_obj: Iterable, quote: str | None = "'",
                      sep: str = ","):
        """

        :param a_list: list[Any]
        :param quote: str | None,_description_, defaults to "'"
        :param sep: str,_description_, defaults to ","
        :return: ToString of all items in a_list, {quote}-quoted and \
                 {sep}-separated if there are multiple 
        """
        result = an_obj
        if isinstance(an_obj, str):
            if quote:
                result = cls(an_obj).enclosed_by(quote)
        elif isinstance(an_obj, Iterable):  # TODO Refactor from LBLY to EAFP?
            list_with_str_els = cls.quotate_all(an_obj, quote)
            if len(an_obj) > 2:
                except_end = (sep + ' ').join(list_with_str_els[:-1])
                result = f"{except_end}{sep} and {list_with_str_els[-1]}"
            else:
                result = " and ".join(list_with_str_els)
        return cls(result)

    @classmethod
    def from_object(cls, an_obj: Any):  # TODO Make this __init__(self, an_obj) ?
        """ _summary_

        TODO Class pattern match? https://stackoverflow.com/questions/72295812

        :param an_obj: None | str | SupportsBytes | dt.datetime | list, _description_
        :param sep: str,_description_, defaults to "_"
        :param timespec: str,_description_, defaults to "seconds"
        :param encoding: str,_description_, defaults to sys.getdefaultencoding()
        :param errors: str,_description_, defaults to "ignore"
        :return: str, _description_
        """  #
        match type(an_obj):
            case builtins.bytes | builtins.bytes:
                stringified = cls(an_obj, encoding=sys.getdefaultencoding(),
                                  errors="ignore")
            case builtins.list | builtins.set | builtins.tuple:
                stringified = cls.from_iterable(an_obj)
            case dt.date | dt.time | dt.datetime:
                stringified = cls.from_datetime(an_obj)
            case cls.NoneType:
                stringified = cls()
            case _:  # str or other
                stringified = cls(an_obj)
        return stringified

    @classmethod
    def quotate_all(cls, things: Iterable[Any], quote: str | None = None
                    ) -> List["ToString"]:
        return [cls.enclosed_by(cls.from_object(obj), quote) for obj in things
                ] if quote else [cls.from_object(obj) for obj in things]

    def that_ends_with(self, suffix: str):
        return self if self.endswith(suffix) \
            else self.__class__(self + suffix)

    def that_starts_with(self, prefix: str):
        return self if self.startswith(prefix) \
            else self.__class__(prefix + self)


# Shorter names to export
stringify = ToString.from_object
stringify_dt = ToString.from_datetime
stringify_list = ToString.from_iterable
