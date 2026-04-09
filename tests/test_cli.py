#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2026-04-08
Updated: 2026-04-08
"""
# Import standard libraries
from typing import Annotated, get_args, Literal

# Import third-party PyPI libraries
import pydantic

# Import local custom libraries
from gconanpy.cli import Arg, ArgumentParser, Valid
from gconanpy.testers import Tester

# Type variables for command-line input argument parsing
_RunMode = Literal["fetch", "send"]
CHOICES = get_args(_RunMode)

# Local file to use as default input argument
EMAIL_FILE = "sample-email-body-structure.html"


class CLIArgs(pydantic.BaseModel):  # NOTE: Dummy/test class
    """ Command-line input parameters saved into a custom dict class with extra
        functionality. All input parameters' types are explicitly defined here
        for static type checking/highlighting/etc. """
    # Required Arg
    run_mode: Annotated[_RunMode, pydantic.Field(), Arg(
        "run_mode", choices=CHOICES, help_msg=(
            "Modes to run this script in: 'fetch' or 'send'."))]

    # Optional Args
    fpaths: Annotated[list[str], pydantic.Field(), Arg(
        "fpaths", "-f", type=Valid.readable_file, default=[EMAIL_FILE],
        help_msg="Valid paths to existing readable files.")]
    username: Annotated[str | None, pydantic.Field(), Arg(
        "username", "-u", help_msg="Username.")]

    debugging: Annotated[bool, pydantic.Field(), Arg(
        "debugging", "-d", default=False,
        help_msg=("Include this flag to enter interactive debugging mode."))]
    how_many: Annotated[int | None, pydantic.Field(ge=0), Arg(
        "how_many", "-n", help_msg="Number of items to fetch.")]
    # output: str
    # password: str


def get_cli_args(*args: str) -> CLIArgs:
    # Collect and parse command-line input arguments
    parser = ArgumentParser("Python script tester.")
    return parser.parse_model_args(CLIArgs, *args)


class TestArgumentParser(Tester):
    def test_help(self) -> None:
        for choice in CHOICES:
            for help_flag in ("-h", "--help"):
                try:
                    get_cli_args(choice, help_flag)
                    raise ValueError(
                        f"Using the {help_flag} flag should raise SystemExit")
                except SystemExit:
                    pass

    def test_missing_required(self) -> None:
        try:
            get_cli_args()
            raise ValueError("Missing a required argument should crash.")
        except SystemExit:
            pass

    def test_required_only(self) -> None:
        for choice in CHOICES:
            get_cli_args(choice)
