#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2026-03-25
Updated: 2026-04-12
"""
# Import standard libraries
import argparse
from collections.abc import Callable, Iterable
from functools import partial
import os
from typing import Annotated, Any, cast, Literal, overload, Self, TypeVar

# Import third-party PyPI libraries
import pydantic

# Type variables
PydanticModelT = TypeVar("PydanticModelT", bound=pydantic.BaseModel)


class Valid:
    """ Tools to validate command-line input arguments. """
    # Type hints for _validate method
    _F = TypeVar("_F")  # Reformatted validated input object
    _T = TypeVar("_T")  # Input object to validate

    # Predefined validator functions (with default parameter values)
    dir_made = partial[None](os.makedirs, exist_ok=True)  # Dir exists
    readable = partial[bool](os.access, mode=os.R_OK)  # Can read existing obj
    writable = partial[bool](os.access, mode=os.W_OK)  # Can write existing obj

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


class Arg:
    """ Very simple data container representing 1 argparse parameter. """
    _option_slots = ("action", "nargs", "const", "default", "type", "choices",
                     "required", "help", "metavar", "version")
    _EXCLUDE = object()  # Represents excluding an option that may be None

    def __init__(
        self, dest: str, *option_strings: str,
        action: str | type[argparse.Action] | None = None,
        nargs: int | str | None = None,
        const: Any = _EXCLUDE,
        default: Any = _EXCLUDE,
        dtype: type | Callable[[str], Any] |
            argparse.FileType | str | None = None,
        choices: Iterable | None = None,
        required: bool | None = None,
        help_msg: str | None = None,
        metavar: str | tuple[str, ...] | None = None,
        # dest: str | None = None,
        **kwargs: Any
    ) -> None:
        """ Save `argparse.ArgumentParser.add_argument` parameters.

        :param dest: str, the name of the argument and of the attribute to be
            added to the object returned by `parse_args()`.
        :param *option_strings: str, option nicknames/shorthand strings, e.g.
            '--foo' or '-f' for the argument 'foo'.
        :param action: str | type[argparse.Action], the basic type of action to
            be taken when this argument is encountered at the command line.
        :param nargs: int | str, the number of command-line arguments that
            should be consumed for this argument.
        :param const: Any, a constant value required by some `action` and
            `nargs` selections.
        :param default: Any, the value produced if the argument is absent from
            the command line and if it is absent from the namespace object.
        :param dtype: type | Callable[[str], Any] | argparse.FileType | str,
            the Python data type to which the command-line argument
            should be converted, or a function to convert it to that type.
        :param choices: Iterable, a sequence of the allowable values for
            the argument.
        :param required: bool, whether or not the command-line option
            may be omitted for optional arguments.
        :param help_msg: str, a brief description of what the argument does.
        :param metavar: str | tuple[str, ...], a name for the argument in
            usage messages.
        """
        self.dest = dest
        self.option_strings = option_strings

        if action is not None:
            self.action = action
        if choices is not None:
            self.choices = choices

        if const is not self._EXCLUDE:
            self.const = const
        if default is not self._EXCLUDE:
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


class OutputDirArg(Arg):
    """ Data container representing an output directory argparse parameter. """

    def __init__(self, dest: str = "output", *option_strings: str,
                 **kwargs: Any) -> None:
        """ Specifies argparse.ArgumentParser.add_argument for a valid path
        to an output directory that must either exist or be created.

        :param dest: str naming the directory to access (and create if needed).
        :param *option_strings: str, option nicknames/shorthand strings, e.g.
            '--foo' or '-f' for the argument 'foo'.
        :param **kwargs: Any, all other `Arg` class keyword arguments.
        """
        if not option_strings:
            option_strings = (
                f"-{dest[0]}", f"-{dest}", f"--{dest}", f"--{dest}-dir",
                f"--{dest}-dir-path")

        if not kwargs.get("default"):  # not kwargs.setdefault because if a
            # default is given, then we can skip unneeded OS method calls below
            try:
                THIS_DIR = os.path.dirname(os.path.abspath(__file__))
            except (NameError, OSError):
                THIS_DIR = os.getcwd()
            kwargs["default"] = os.path.join(THIS_DIR, dest)

        kwargs.setdefault(
            "help_msg", f"Valid path to a local directory to save {dest} "
            f"files into. If no directory exists at the path yet, then one "
            f"will be created. By default, this script will save {dest} files "
            f"into a directory at this path: {kwargs['default']}")

        kwargs.setdefault("dtype", Valid.output_dir)

        super().__init__(dest, *option_strings, **kwargs)


class ArgumentParser(argparse.ArgumentParser):
    """ ArgumentParser subclass with a method to automatically import every
    Field in a Pydantic Model as its own argparse argument/parameter. """

    def parse_args_to_model(self, model: type[PydanticModelT], *args: str
                            ) -> PydanticModelT:
        """ After defining argparse arguments as fields in a Pydantic Model,
        load them into this `ArgumentParser`, parse their values from the
        command line, and then load the results into an instance of that
        Pydantic Model.

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
        parsed = self.parse_args(args) if args else self.parse_args()
        return model(**vars(parsed))
