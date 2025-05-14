#!/usr/bin/env python3

"""
Tools to define, accept, and validate command-line input arguments.
Greg Conan: gregmconan@gmail.com
Created: 2024-09-23
Updated: 2025-05-13
"""
# Import standard libraries
from collections.abc import Callable
import argparse
import os
import pdb
from typing import Any

# Import local custom libraries
try:
    from metafunc import WrapFunction
except ModuleNotFoundError:
    from gconanpy.metafunc import WrapFunction


# NOTE: Functions and classes below are in alphabetical order.


def add_new_out_dir_arg_to(parser: argparse.ArgumentParser, name: str,
                           **kwargs: Any) -> argparse.ArgumentParser:
    """ Specifies argparse.ArgumentParser.add_argument for a valid path to\
    an output directory that must either exist or be created.

    :param name: str naming the directory to ensure exists
    :param kwargs: Mapping[str, Any], ArgumentParser.add_argument keyword args
    :return: argparse.ArgumentParser, now with the output directory argument
    """
    if not kwargs.get("default"):
        kwargs["default"] = os.path.join(os.getcwd(), name)
    if not kwargs.get("dest"):
        kwargs["dest"] = name
    if not kwargs.get("help"):
        kwargs["help"] = f"Valid path to local directory to save {name} " \
            "files into. If no directory exists at this path yet, then one " \
            "will be created. By default, this argument's value will be: " \
            + kwargs["default"]
    parser.add_argument(
        f"-{name[0]}", f"-{name}", f"--{name}", f"--{name}-dir",
        f"--{name}-dir-path", type=Valid.output_dir, **kwargs
    )
    return parser


class ArgParser(argparse.ArgumentParser):

    def __init__(self, *args, **kwargs: Any) -> None:
        """
        Extends argparse.ArgumentParser functions to include default
        values that I tend to re-use. Purely for convenience.
        """
        self.cwd = os.getcwd()
        super().__init__(*args, **kwargs)

    def add_new_out_dir_arg(self, name: str, default: str | None = None) -> None:
        """
        Specifies argparse.ArgumentParser.add_argument for a valid path to
        an output directory that must either exist or be created.
        :param name: str naming the directory to ensure exists
        :param default: Optional[str], _description_, defaults to None
        """
        if not default:
            default = os.path.join(self.cwd, name)
        self.add_argument(
            f"-{name[0]}", f"-{name}", f"--{name}", f"--{name}-dir",
            f"--{name}-dir-path",
            default=default,
            dest=name,
            type=Valid.output_dir,
            help=(f"Valid path to local directory to save {name} files "
                  "into. If no directory exists at this path yet, then "
                  "one will be created. By default, the value for this "
                  f"argument will be `{default}`."),
        )


class Valid:
    # TODO Do this in a more standard way
    dir_made = WrapFunction(os.makedirs, exist_ok=True)
    readable = WrapFunction(os.access, mode=os.R_OK)
    writable = WrapFunction(os.access, mode=os.W_OK)

    @staticmethod
    def _validate(to_validate: Any, *conditions: Callable,
                  # conditions: Iterable[Callable] = list(),
                  err_msg: str = "`{}` is invalid.",
                  first_ensure: Callable | None = None,
                  final_format: Callable | None = None) -> Callable:
        """
        Parent/base function used by different type validation functions. Raises an
        argparse.ArgumentTypeError if the input object is somehow invalid.
        :param to_validate: String to check if it represents a valid object 
        :param is_real: Function which returns true iff to_validate is real
        :param make_valid: Function which returns a fully validated object
        :param err_msg: String to show to user to tell them what is invalid
        :param prepare: Function to run before validation
        :return: to_validate, but fully validated
        """
        try:
            if first_ensure:
                first_ensure(to_validate)
            '''
            for prepare in first_ensure:
                prepare(to_validate)
            '''
            for is_valid in conditions:
                assert is_valid(to_validate)
            return final_format(to_validate) if final_format else to_validate
        except (argparse.ArgumentTypeError, AssertionError, OSError,
                TypeError, ValueError):
            raise argparse.ArgumentTypeError(err_msg.format(to_validate))

    @classmethod
    def output_dir(cls, path: Any) -> str:
        """
        Try to make a folder for new files at path; throw exception if that fails
        :param path: String which is a valid (not necessarily real) folder path
        :return: String which is a validated absolute path to real writeable folder
        """
        return cls._validate(path, os.path.isdir, cls.writable,
                             err_msg="Cannot create directory at `{}`",
                             first_ensure=cls.dir_made,  # [cls.dir_made],
                             final_format=os.path.abspath)

    @classmethod
    def readable_dir(cls, path: Any) -> str:
        """
        :param path: Parameter to check if it represents a valid directory path
        :return: String representing a valid directory path
        """
        return cls._validate(path, os.path.isdir, cls.readable,
                             err_msg="Cannot read directory at `{}`",
                             final_format=os.path.abspath)

    @classmethod
    def readable_file(cls, path: Any) -> str:
        """
        Throw exception unless parameter is a valid readable filepath string. Use
        this, not argparse.FileType('r') which leaves an open file handle.
        :param path: Parameter to check if it represents a valid filepath
        :return: String representing a valid filepath
        """
        return cls._validate(path, cls.readable,
                             err_msg="Cannot read file at `{}`",
                             final_format=os.path.abspath)

    @classmethod
    def whole_number(cls, to_validate: Any):
        """
        Throw argparse exception unless to_validate is a positive integer
        :param to_validate: Object to test whether it is a positive integer
        :return: to_validate if it is a positive integer
        """
        return cls._validate(to_validate, lambda x: int(x) >= 0,
                             err_msg="{} is not a positive integer",
                             final_format=int)
