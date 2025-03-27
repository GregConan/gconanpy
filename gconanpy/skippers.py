#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-03-26
Updated: 2025-03-26
"""


class SkipException(BaseException):
    ...


class SkipOrNot:
    def __init__(self, parent: "KeepTryingUntilNoException") -> None:
        self.parent = parent

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return True


class Skip(SkipOrNot):
    def __enter__(self):
        raise SkipException


class DontSkip(SkipOrNot):
    def __exit__(self, exc_type: type | None = None,
                 exc_val: BaseException | None = None, exc_tb=None):
        if exc_val is None:
            self.parent.is_done = True
        else:
            self.parent.errors.append(exc_val)
        return True


class KeepTryingUntilNoException:
    def __init__(self):
        self.errors = list()
        self.is_done = False

    def __call__(self) -> Skip | DontSkip:
        return Skip(parent=self) if self.is_done else DontSkip(parent=self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type: type | None = None, *_):
        return exc_type is SkipException
