#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-03-26
Updated: 2025-03-27
"""
from typing import Any


class SkipException(BaseException):
    ...


class SkipOrNot:
    def __init__(self, parent: "KeepTryingUntilNoException",
                 *catch: type[BaseException]) -> None:
        self.catch = catch
        self.parent = parent

    def __enter__(self):
        return self

    def __exit__(self, exc_type: type[BaseException] | None = None, *_: Any):
        return (not self.catch) or (exc_type in self.catch)


class Skip(SkipOrNot):
    def __enter__(self):
        raise SkipException


class DontSkip(SkipOrNot):
    def __exit__(self, exc_type: type[BaseException] | None = None,
                 exc_val: BaseException | None = None, _: Any = None):
        if exc_val is None:
            self.parent.is_done = True
        else:
            self.parent.errors.append(exc_val)
        return super(DontSkip, self).__exit__(exc_type)


class KeepTryingUntilNoException:
    def __init__(self, *catch: type[BaseException]):
        self.catch = catch
        self.errors = list()
        self.is_done = False

    def __call__(self) -> Skip | DontSkip:
        return Skip(parent=self) if self.is_done else DontSkip(parent=self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type: type[BaseException] | None = None, *_: Any):
        return exc_type is SkipException
