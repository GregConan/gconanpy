#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2026-03-25
Updated: 2026-04-08
"""
# Import standard libraries
import argparse
from collections.abc import Callable, Iterable
from functools import partial
import os
from typing import Annotated, Any, cast, Literal, overload, TypeVar

# Import third-party PyPI libraries
import pydantic

# Type variables
PydanticModelT = TypeVar("PydanticModelT", bound=pydantic.BaseModel)


class Arg:
    """ Very simple data container representing 1 argparse parameter. """
    _option_slots = ("action", "nargs", "const", "default", "type", "choices",
                     "required", "help", "metavar", "version")
    _DEFAULT = object()  # Represents excluding an option that may be None

    def __init__(
        self, dest: str, *option_strings: str,
        action: str | type[argparse.Action] | None = None,
        nargs: int | str | None = None,
        const: Any = _DEFAULT,
        default: Any = _DEFAULT,
        dtype: type | Callable[[str], Any] |
            argparse.FileType | str | None = None,
        choices: Iterable | None = None,
        required: bool | None = None,
        help_msg: str | None = None,
        metavar: str | tuple[str, ...] | None = None,
        # dest: str | None = None,
        **kwargs: Any
    ) -> None:
        self.dest = dest
        self.option_strings = option_strings

        if action is not None:
            self.action = action
        if choices is not None:
            self.choices = choices

        if const is not self._DEFAULT:
            self.const = const
        if default is not self._DEFAULT:
            self.default = default

        if dtype is not None:
            self.type = dtype
        if help_msg is not None:
            self.help = help_msg
        if metavar is not None:
            self.metavar = metavar
        if nargs is not None:
            self.nargs = nargs

        if required is not None:
            self.required = required
        if not getattr(self, "required", False):
            option_strings = (self.dest2param(), *option_strings)
        # self.required = (not dest.startswith("-")) if required is None else required

    def dest2param(self) -> str:
        return "--" + self.dest.replace("_", "-")

    def options(self) -> dict[str, Any]:
        options = {}
        for slot_name in self._option_slots:
            try:
                options[slot_name] = getattr(self, slot_name)
            except AttributeError:
                pass
        return options


class Valid:
    """ Tools to validate command-line input arguments. """
    # Type hints for _validate method
    _F = TypeVar("_F")  # Reformatted validated input object
    _T = TypeVar("_T")  # Input object to validate

    # Predefined validator functions (with default parameter values)
    dir_made = partial(os.makedirs, exist_ok=True)  # Dir exists
    readable = partial(os.access, mode=os.R_OK)  # Can read existing obj
    writable = partial(os.access, mode=os.W_OK)  # Can write existing obj

    @overload
    @staticmethod
    def _validate(to_validate: _T, *conditions: Callable[[_T], bool],
                  err_msg: str,
                  first_ensure: Callable[[_T], Any] | None = None,
                  final_format: Callable[[_T], _F]) -> _F: ...

    @overload
    @staticmethod
    def _validate(to_validate: _T, *conditions: Callable[[_T], bool],
                  err_msg: str,
                  first_ensure: Callable[[_T], Any] | None = None) -> _T: ...

    @staticmethod
    def _validate(to_validate: _T, *conditions: Callable[[_T], bool],
                  # conditions: Iterable[Callable] = list(),
                  err_msg: str = "`{}` is invalid.",
                  first_ensure: Callable[[_T], Any] | None = None,
                  final_format: Callable[[_T], _F] | None = None):
        """ Parent/base function used by different type validation functions.

        :param to_validate: _T: Any, object to validate
        :param conditions: Iterable[Callable[[_T], bool]] that each accept
            `to_validate` and returns True if and only if `to_validate`
            passes some specific condition, otherwise returning False
        :param final_format: Callable[[_T], _F: Any] that accepts
            `to_validate` and returns it after fully validating it
        :param err_msg: str to show to user to tell them what is invalid
        :param first_ensure: Callable[[_T], Any] to run on `to_validate` to
            prepare/ready it for validation
        :raise: argparse.ArgumentTypeError if `to_validate` is somehow invalid
        :return: _T | _F, `to_validate` but fully validated
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
        """ Try to make or access a directory for new files at `path`.

        :param path: str, valid (not necessarily real) directory path
        :raise: argparse.ArgumentTypeError if directory path is not writable
        :return: str, validated absolute path to real writable folder
        """
        return cls._validate(path, os.path.isdir, cls.writable,
                             err_msg="Cannot create directory at `{}`",
                             first_ensure=cls.dir_made,  # [cls.dir_made],
                             final_format=os.path.abspath)

    @classmethod
    def readable_dir(cls, path: Any) -> str:
        """ Verify that `path` is a valid directory path.

        :param path: Any, object that should be a valid directory path
        :return: str representing a valid directory path
        """
        return cls._validate(path, os.path.isdir, cls.readable,
                             err_msg="Cannot read directory at `{}`",
                             final_format=os.path.abspath)

    @classmethod
    def readable_file(cls, path: Any) -> str:
        """ Use this instead of `argparse.FileType('r')` because the latter
            leaves an open file handle.

        :param path: Any, object that should be a valid file (or dir) path.
        :raise: argparse.ArgumentTypeError if `path` isn't a path to a valid
            readable file (or directory).
        :return: str representing a valid file (or directory) path.
        """
        return cls._validate(path, cls.readable,
                             err_msg="Cannot read file at `{}`",
                             final_format=os.path.abspath)

    @classmethod
    def whole_number(cls, to_validate: Any) -> int:
        """ Throw argparse exception unless to_validate is a positive integer

        :param to_validate: Any, obj to test whether it is a positive integer
        :return: int, to_validate if it is a positive integer
        """
        return cls._validate(to_validate, lambda x: int(x) >= 0,
                             err_msg="{} is not a positive integer",
                             final_format=int)


class ArgumentParser(argparse.ArgumentParser):
    """ ArgumentParser subclass with a method to automatically import every
        Field in a Pydantic Model as its own argparse argument/parameter.

    Also includes pre-defined input args I tend to reuse for convenience. """

    def add_new_out_dir_arg(self, name: str, **kwargs: Any) -> None:
        """ Specifies argparse.ArgumentParser.add_argument for a valid path
            to an output directory that must either exist or be created.

        :param name: str naming the directory to access (and create if needed)
        :param kwargs: Mapping[str, Any], keyword arguments for the method
            `argparse.ArgumentParser.add_argument`
        """
        if not kwargs.get("default"):
            kwargs["default"] = os.path.join(os.getcwd(), name)
        if not kwargs.get("dest"):
            kwargs["dest"] = name
        if not kwargs.get("help"):
            kwargs["help"] = "Valid path to local directory to save " \
                f"{name} files into. If no directory exists at this path " \
                "yet, then one will be created. By default, this script " \
                "will save output files into a directory at this path: " \
                + kwargs["default"]
        self.add_argument(
            f"-{name[0]}", f"-{name}", f"--{name}", f"--{name}-dir",
            f"--{name}-dir-path", type=Valid.output_dir, **kwargs
        )

    def parse_model_args(self, model: type[PydanticModelT], *args: str
                         ) -> PydanticModelT:
        """ Load arguments defined in a Pydantic Model into this
            `ArgumentParser`, parse them from the command line, and then load
            the results into an instance of that Pydantic Model.

        :param model: type[PydanticModelT], Pydantic Model to parse args into.
        :param *args: str, arguments for this `ArgumentParser` to accept as if
            they were passed in via the command line.
        :return: PydanticModelT, a `model` instance containing data parsed from
            the command line via this `ArgumentParser`.
        """
        for field in model.model_fields.values():
            field_arg: Arg = field.metadata[-1]
            self.add_argument(*field_arg.option_strings, dest=field_arg.dest,
                              **field_arg.options())
        return model(**vars(self.parse_args(args)))
