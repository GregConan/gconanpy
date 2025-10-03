#!/usr/bin/env python3

"""
Classes to convert objects to/from bytes.
Greg Conan: gregmconan@gmail.com
Created: 2025-08-23
Updated: 2025-10-01
"""
# Import standard libraries
import base64
import hashlib
import os
from more_itertools import interleave_longest
import random
import re
import string
import sys
from typing import Any, Literal, overload, SupportsBytes, TypeVar

# Import third-party PyPI libraries
from cryptography.fernet import Fernet

DEFAULT_ENCODING = sys.getdefaultencoding()

# Type variable to export indicating that a value is acceptable by
# the Bytesifier.bytesify method
Bytesifiable = SupportsBytes | int | str | float | memoryview


class Bytesifier:
    # Type variables for bytesify function's input parameter type hints
    _T = TypeVar("_T")
    ErrOption = Literal["raise", "ignore", "print"]
    IgnoreErr = Literal["ignore", "print"]

    # Default values for bytesify function's input parameters
    DEFAULT_LEN = 8

    # String encoding error message
    ERR_MSG = "Cannot convert {} into bytes."
    ERR_RETRY = ERR_MSG + " Try calling `bytesify` again with "
    STR_ERR = ERR_RETRY + "`signed=True` or a higher `length`."

    @overload
    @classmethod
    def bytesify(cls, an_obj: str, *,
                 encoding: str = DEFAULT_ENCODING) -> bytes: ...

    @overload
    @classmethod
    def bytesify(cls, an_obj: str | float, errors: Literal["raise"], *,
                 encoding: str = DEFAULT_ENCODING) -> bytes: ...

    @overload
    @classmethod
    def bytesify(cls, an_obj: str, errors: IgnoreErr, *,
                 encoding: str = DEFAULT_ENCODING) -> bytes | str: ...

    @overload
    @classmethod
    def bytesify(cls, an_obj: float, errors: IgnoreErr, *,
                 encoding: str = DEFAULT_ENCODING) -> bytes | float: ...

    @overload
    @classmethod
    def bytesify(cls, an_obj: int, errors: Literal["raise"], *,
                 signed: bool = True, length: int = DEFAULT_LEN
                 ) -> bytes: ...

    @overload
    @classmethod
    def bytesify(cls, an_obj: int, errors: IgnoreErr, *,
                 signed: bool = True, length: int = DEFAULT_LEN
                 ) -> bytes | int: ...

    @overload
    @classmethod
    def bytesify(cls, an_obj: SupportsBytes | memoryview,
                 errors: ErrOption = "raise") -> bytes: ...

    @overload
    @classmethod
    def bytesify(cls, an_obj: _T, errors: IgnoreErr) -> _T: ...

    @overload
    @classmethod
    def bytesify(cls, an_obj: Any, errors: Literal["raise"]) -> bytes: ...

    @classmethod
    def bytesify(cls, an_obj, errors="raise", *, encoding=DEFAULT_ENCODING,
                 signed=True, length=DEFAULT_LEN):
        """ Convert `an_obj` to `bytes`.

        :param cls, an_obj: SupportsBytes | str | int, object to convert to bytes.
        :param strict: bool, True to raise TypeError on failure; else False \
            to return `an_obj` unchanged on failure. Defaults to True.
        :param encoding: str, the encoding in which to encode `an_obj` if \
            it's a `str`; otherwise does nothing. Defaults to the system's \
            default encoding, which should usually be "utf-8".
        :param length: int, number of bytes object to convert an `int` into. \
            Defaults to 8 to bytesify outputs of Python `hash()` function. \
            Does nothing if `an_obj` is not an `int`.
        :param signed: bool, whether two's complement is used to represent \
            `an_obj` if it's an `int`; otherwise does nothing. \
            `signed=False` cannot handle negative numbers.

        :raises TypeError: if `an_obj` cannot be converted into bytes.
        :return: bytes, `an_obj` converted to bytes.
        """
        err_msg = None
        match an_obj:
            case SupportsBytes() | memoryview():
                bytesified = bytes(an_obj)
            case int():
                try:
                    bytesified = an_obj.to_bytes(length, signed=signed)
                except OverflowError:
                    err_msg = cls.ERR_RETRY.format(f"integer {an_obj}") \
                        + "`signed=True` or a higher `length`."
            case str():
                try:
                    bytesified = an_obj.encode(encoding=encoding)
                except UnicodeEncodeError:
                    err_msg = cls.STR_ERR.format(f"string '{an_obj}'")
            case float():
                try:  # Store float as str to avoid headache/overcomplication
                    bytesified = str(an_obj).encode(encoding=encoding)
                except UnicodeEncodeError:
                    err_msg = cls.STR_ERR.format(f"float '{an_obj}'")
            case _:
                err_msg = cls.ERR_MSG.format(f"object `{an_obj}`")
        if err_msg is None:
            return bytesified
        elif errors == "raise":
            raise TypeError(err_msg)
        else:
            if errors == "print":
                print(err_msg)
            return an_obj

    @staticmethod
    def decode(bytestr: bytes, encoding: str = DEFAULT_ENCODING,
               altchars=b'-_') -> str:
        bytestr = re.sub(rb'[^a-zA-Z0-9%s]+' % altchars, b'', bytestr)

        # Calculate missing padding:
        missing_padding = len(bytestr) % 4

        # Add padding if needed:
        if missing_padding:
            bytestr += b'=' * (4 - missing_padding)
        return base64.urlsafe_b64decode(bytestr).decode(encoding)

    @staticmethod
    def encode(string: str, encoding: str = DEFAULT_ENCODING) -> bytes:
        return base64.urlsafe_b64encode(string.encode(encoding)
                                        )  # .strip(b"=")


class Encryptor(Bytesifier):
    KEY_LEN = 32

    def __init__(self, k: int, iterations: int = 1000, salt_len=16) -> None:
        # Create encryption mechanism
        self.encrypted: set[int] = set()
        self.iterations = iterations
        self.salt = os.urandom(salt_len)
        self.sep = random.choices(string.punctuation, k=k)

    def _keys2Fernet(self, keys: tuple[str, ...],
                     encoding: str = DEFAULT_ENCODING) -> Fernet:
        """ Adapted from https://stackoverflow.com/a/55147077 and \
            https://github.com/django/django/blob/main/django/utils/crypto.py

        :param keys: tuple[str, ...], keys/coordinates mapped to the value \
            to encrypt or decrypt. The keys are used in (en/de)cryption.
        :param encoding: str, the encoding with which to encode values from \
            `str` to `bytes`; defaults to the system default (usually "utf-8")
        :return: cryptography.fernet.Fernet to (en/de)crypt values.
        """  # TODO: This still seems overcustomized. Do it in a standard way?
        byte_data = base64.urlsafe_b64encode("".join(interleave_longest(
            keys, self.sep)).encode(encoding))
        byte_data = hashlib.pbkdf2_hmac("sha256", byte_data, self.salt,
                                        self.iterations, self.KEY_LEN)
        return Fernet(base64.urlsafe_b64encode(byte_data))


class HumanBytes:
    """ Shamelessly stolen from https://stackoverflow.com/a/63839503 """
    METRIC_LABELS: list[str] = ["B", "kB", "MB", "GB", "TB", "PB",
                                "EB", "ZB", "YB"]
    BINARY_LABELS: list[str] = ["B", "KiB", "MiB", "GiB", "TiB",
                                "PiB", "EiB", "ZiB", "YiB"]

    # PREDEFINED FOR SPEED
    PRECISION_OFFSETS: list[float] = [0.5, 0.05, 0.005, 0.0005]
    PRECISION_FORMATS: list[str] = ["{}{:.0f} {}", "{}{:.1f} {}",
                                    "{}{:.2f} {}", "{}{:.3f} {}"]

    @staticmethod
    def format(num: int | float, metric: bool = False,
               precision: int = 1) -> str:
        """
        Human-readable formatting of bytes, using binary (powers of 1024)
        or metric (powers of 1000) representation.
        """
        assert isinstance(num, (int, float)), "num must be an int or float"
        assert isinstance(metric, bool), "metric must be a bool"
        assert isinstance(precision, int) and 0 <= precision <= 3, \
            "precision must be an int (range 0-3)"

        unit_labels = (HumanBytes.METRIC_LABELS if metric
                       else HumanBytes.BINARY_LABELS)
        last_label = unit_labels[-1]
        unit_step = 1000 if metric else 1024
        unit_step_thresh = unit_step - HumanBytes.PRECISION_OFFSETS[precision]

        is_negative = num < 0
        if is_negative:  # Faster than ternary assignment or always running abs().
            num = abs(num)

        for unit in unit_labels:
            if num < unit_step_thresh:
                # VERY IMPORTANT:
                # Only accepts the CURRENT unit if we're BELOW the threshold where
                # float rounding behavior would place us into the NEXT unit: F.ex.
                # when rounding a float to 1 decimal, any number ">= 1023.95" will
                # be rounded to "1024.0". Obviously we don't want ugly output such
                # as "1024.0 KiB", since the proper term for that is "1.0 MiB".
                break
            if unit != last_label:
                # We only shrink the number if we HAVEN'T reached the last unit.
                # NOTE: These looped divisions accumulate floating point rounding
                # errors, but each new division pushes the rounding errors further
                # and further down in the decimals, so it doesn't matter.
                num /= unit_step

        return HumanBytes.PRECISION_FORMATS[precision].format(
            "-" if is_negative else "", num, unit)
