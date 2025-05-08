#!/usr/bin/env python3

"""
Convenience/utility functions/classes only needed to ease/aid debugging.
Overlaps significantly with audit-ABCC/src/utilities.py and \
    abcd-bids-tfmri-pipeline/src/pipeline_utilities.py
Greg Conan: gregmconan@gmail.com
Created: 2025-01-23
Updated: 2025-05-07
"""
# Import standard libraries
from abc import ABC
from collections.abc import Callable, Mapping
import datetime as dt
from io import TextIOWrapper
import logging
import os
import pdb
import sys
import traceback
import tracemalloc
from typing import Any

# Import third-party PyPI libraries
import pandas as pd
from pympler.asizeof import asizeof

# Import local custom libraries
try:
    from metafunc import nameof
    from seq import uniqs_in
    from ToString import stringify_dt, stringify_iter
except ModuleNotFoundError:
    from gconanpy.metafunc import nameof
    from gconanpy.seq import uniqs_in
    from gconanpy.ToString import stringify_dt, stringify_iter

# Constants
LOGGER_NAME = __package__


# NOTE All classes and functions below are in alphabetical order.


def debug(an_err: Exception, local_vars: Mapping[str, Any]) -> None:
    """
    :param an_err: Exception (any)
    :param local_vars: Dict[str, Any] mapping variables' names to their \
                       values; locals() called from where an_err originated
    """
    errs = [an_err]
    locals().update(local_vars)
    try:
        logger = logging.getLogger(LOGGER_NAME)
        logger.exception(an_err)
        print("Local variables: " + stringify_iter([x for x in locals()]))
    except Exception as new_err:
        errs.append(new_err)
    # show_keys_in(locals(), level=logger.level)
    pdb.set_trace()
    pass


class Debuggable:
    """ I put the debugger function in a class so it can check its
        implementer classes' `self.debugging` variable to determine whether
        to raise errors/exceptions or pause and interactively debug them. """

    def __init__(self, debugging: bool = False):
        """
        :param debugging: bool, True to pause and interact on error, else \
            False to raise errors/exceptions; defaults to False.
        """
        self.debugging = debugging

    def debug_or_raise(self, an_err: Exception, local_vars: Mapping[str, Any]
                       ) -> None:
        """
        :param an_err: Exception (any)
        :param local_vars: Dict[str, Any] mapping variables' names to their \
                           values; locals() called from where an_err originated
        :raises an_err: if self.debugging is False; otherwise pause to debug
        """
        if getattr(self, "debugging", None):
            debug(an_err, local_vars)
        else:
            raise an_err


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


# TODO Replace "print()" calls with "log()" calls after making log calls
#      display in the Debug Console window when running pytest tests
def log(content: str, level: int = logging.INFO,
        logger_name: str = LOGGER_NAME) -> None:
    """
    :param content: String, the message to log/display
    :param level: int, the message's importance/urgency/severity level as \
                  defined by logging module's 0 (ignore) to 50 (urgent) scale
    """
    logging.getLogger(logger_name).log(msg=content, level=level)


def print_tb_of(err: BaseException) -> None:
    """ Print the traceback, type, and message of an error or exception.

    :param err: BaseException to print information about.
    """
    print(nameof(err), end=": ", file=sys.stderr)
    traceback.print_tb(err.__traceback__)
    print(err, file=sys.stderr)


def show_keys_in(a_map: Mapping[str, Any],  # show: Callable = print,
                 what_keys_are: str = "Local variables",
                 level: int = logging.INFO,
                 logger_name: str = LOGGER_NAME) -> None:
    """ Log all of the keys in a Mapping.

    :param a_map: Mapping[str, Any]
    :param what_keys_are: String naming what the keys in a_map are
    :param level: int, the severity level to log the message at (10 to 50)
    :param logger_name: str naming the logger to use for logging the message
    """
    log(f"{what_keys_are}: {stringify_iter(uniqs_in(a_map))}", level=level,
        logger_name=logger_name)


class ShowTimeTaken(ABC):
    """Context manager to time and log the duration of any block of code."""

    def __init__(self, doing_what: str, show: Callable = print) -> None:
        """
        :param doing_what: String describing what is being timed
        :param show: Function to print/log/show messages to the user
        """  # TODO Use "log" instead of "print" by default?
        self.doing_what = doing_what
        self.show = show

    def __enter__(self):
        """ Log the moment that script execution enters the context manager \
            and what it is about to do.
        """
        self.start = dt.datetime.now()
        self.show(f"Started {self.doing_what} at {self.start}")
        return self

    def __exit__(self, exc_type: type | None = None,
                 exc_val: BaseException | None = None, exc_tb=None):
        """ Log the moment that script execution exits the context manager \
            and what it just finished doing.

        :param exc_type: Exception type
        :param exc_val: Exception value
        :param exc_tb: Exception traceback
        """
        self.elapsed = dt.datetime.now() - self.start
        self.show(f"\nTime elapsed {self.doing_what}: {self.elapsed}")


def sizeof(an_obj: Any, precision: int = 3, metric: bool = True) -> str:
    """ 
    :param an_obj: Object (any)
    :param precision: int, number of digits of precision in the memory size
                      number to return, defaults to 3
    :param metric: True to return memory usage in metric units (e.g. KB for
                   1000 bytes) and False otherwise (e.g. KiB for 1024 bytes)
    :return: String, a human-readable representation of memory usage by an_obj
    """
    return HumanBytes.format(asizeof(an_obj), precision=precision,
                             metric=metric)


class SplitLogger(logging.getLoggerClass()):
    """Container class for message-logger and error-logger ("split" apart)"""
    FMT = "\n%(levelname)s %(asctime)s: %(message)s"
    LVL = dict(OUT={logging.DEBUG, logging.INFO, logging.NOTSET},
               ERR={logging.CRITICAL, logging.ERROR, logging.WARNING})
    NAME = LOGGER_NAME

    def __init__(self, verbosity: int, out: str | None = None,
                 err: str | None = None) -> None:
        """ Make logger to log status updates, warnings, & other useful info.
            SplitLogger can log errors/warnings/problems to one stream/file \
            and log info/outputs/messages to a different stream/file.

        :param verbosity: Int, the number of times that the user included the
                          --verbose flag when they started running the script.
        :param out: str, valid path to text file to write output logs into
        :param err: str, valid path to text file to write error logs into
        """  # TODO stackoverflow.com/a/33163197 ?
        log_level = verbosity_to_log_level(verbosity)
        # self = logging.getLogger(self.NAME)
        # self.setLevel(verbosity_to_log_level(verbosity))
        # self.addHandler(logging.Handler(log_level))
        super().__init__(self.NAME, level=log_level)
        # if self.level == 0 or (self.getEffectiveLevel() == 30 and verbosity != 1):
        self.addSubLogger("out", sys.stdout, out)
        self.addSubLogger("err", sys.stderr, err)

        # Force logging.getLogger(name) to return this object, since otherwise
        # it creates a different logging.Logger with the same name!
        self.manager.loggerDict[self.name] = self

    @classmethod
    def from_cli_args(cls, cli_args: Mapping[str, Any]) -> "SplitLogger":
        """ Get logger, and prepare it to log to a file if the user said to

        :param cli_args: Mapping[str, Any] of command-line input arguments
        :return: SplitLogger
        """
        log_to = dict()
        if cli_args.get("log"):
            log_file_name = f"log_{stringify_dt(dt.datetime.now())}.txt"
            log_file_path = os.path.join(cli_args["log"], log_file_name)
            log_to = dict(out=log_file_path, err=log_file_path)
        return cls(verbosity=cli_args["verbosity"], **log_to)

    def addSubLogger(self, sub_name: str, log_stream: TextIOWrapper,
                     log_file_path: str | None = None):
        """ Make a child Logger to handle 1 kind of message, namely err or out

        :param name: String naming the child logger, accessible as
                     self.getLogger(f"{self.NAME}.{sub_name}")
        :param log_stream: io.TextIOWrapper, namely sys.stdout or sys.stderr
        :param log_file_path: str, valid path to text file to write logs into
        """
        sublogger = self.getChild(sub_name)
        sublogger.setLevel(self.level)
        handler = (logging.FileHandler(log_file_path, encoding="utf-8")
                   if log_file_path else logging.StreamHandler(log_stream))
        handler.setFormatter(logging.Formatter(fmt=self.FMT))
        sublogger.addHandler(handler)

    @classmethod
    def logAtLevel(cls, level: int, msg: str) -> None:
        """ Log a message, using the sub-logger specific to the message level

        :param level: logging._levelToName key; level to log the message at
        :param msg: String, the message to log
        """
        logger = logging.getLogger(cls.NAME)
        if level in cls.LVL["ERR"]:
            sub_log_name = "err"
        elif level in cls.LVL["OUT"]:
            sub_log_name = "out"
        sublogger = logger.getChild(sub_log_name)
        sublogger.log(level, msg)


def start_debug() -> None:
    tracemalloc.start()


def take_snapshot(logger: logging.Logger, how: str = "lineno"
                  ) -> tracemalloc.Snapshot:
    snapshot = tracemalloc.take_snapshot()
    snap_stats = snapshot.statistics(how)
    snap_df = pd.DataFrame([{"Size": snap.size,
                             "Filename": snap.traceback._frames[0][0],
                             "Line No.": snap.traceback._frames[0][1],
                             "Object": snap} for snap in snap_stats])
    total_size = HumanBytes.format(int(snap_df['Size'].sum()), precision=2)
    logger.info(f"Total Memory Usage: {total_size}")
    pdb.set_trace()
    return snapshot


# TODO Maybe move into new "Loggable" class?
def verbosity_to_log_level(verbosity: int) -> int:
    """
    :param verbosity: Int, the number of times that the user included the
                      --verbose flag when they started running the script.
    :return: Level for logging, corresponding to verbosity like so:
             verbosity == 0 corresponds to logging.ERROR(==40)
             verbosity == 1 corresponds to logging.WARNING(==30)
             verbosity == 2 corresponds to logging.INFO(==20)
             verbosity >= 3 corresponds to logging.DEBUG(==10)
    """
    return max(10, logging.ERROR - (10 * verbosity))


def verbosity_is_at_least(verbosity: int, logger_name: str =
                          SplitLogger.NAME) -> bool:
    """
    :param verbosity: Int, the number of times that the user included the
                      --verbose flag when they started running the script.
    :return: Bool indicating whether the program is being run in verbose mode
    """
    return logging.getLogger(logger_name).getEffectiveLevel() \
        <= verbosity_to_log_level(verbosity)


if __name__ == "__main__":
    start_debug()
