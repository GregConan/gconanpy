#!/usr/bin/env python3

"""
Classes and metaclasses to define generic types in other classes
Greg Conan: gregmconan@gmail.com
Created: 2025-03-25
Updated: 2025-03-25
"""
# Import standard libraries
from abc import ABC
import pdb
from typing import Any, Callable, TypeVar

# Import local custom libraries
try:
    from seq import find_an_attr_in
except ModuleNotFoundError:
    from gconanpy.seq import find_an_attr_in


class BoolableMeta(type):  # https://realpython.com/python-interface/
    """ A metaclass that will be used for Boolable class creation.
    """
    def __instancecheck__(cls, instance):
        try:
            bool(instance)
            return True
        except (TypeError, ValueError):
            return False

    def __subclasscheck__(cls, subclass):
        methods = ("__bool__", "__len__")
        return find_an_attr_in(subclass, methods, None, set(methods))


class Boolable(metaclass=BoolableMeta):
    ...


class FinderTypes(ABC):
    # TODO Figure out standard way to centralize, reuse, & document TypeVars?
    """ Type vars to specify which attributes of finders.py classes' methods' \
    input arguments need to be the same type/class as which other(s).

    :param D: Any, default value to return if nothing was found
    :param F: Any, `found_if(..., *args: F)` function extra arguments
    :param M: Any, `modify(thing: S, ...) -> M` function output
    :param R: Any, `ready_if(..., *args: R)` function extra arguments
    :param S: Any, element in iter_over Sequence[S]
    :param T: Any, input argument to "whittle down"
    :param X: Any, `modify(..., *args: X)` function extra arguments
    :param W: Any, `whittle(thing: W, ...)` function argument (?)
    :param Found: Callable[[S, tuple[F, ...]], bool], found_if function
    :param Modify: Callable[[S, tuple[X, ...]], M], modify function
    :param Viable: Callable[[M], bool], is_viable function
    """
    D = TypeVar("D")
    F = TypeVar("F")
    M = TypeVar("M")
    R = TypeVar("R")
    S = TypeVar("S")
    T = TypeVar("T")
    X = TypeVar("X")
    W = TypeVar("W")
    Errors = (AttributeError, IndexError, KeyError, TypeError, ValueError)
    Found = TypeVar("Found", bound=Callable[[S, tuple[F, ...]], bool])
    Modify = TypeVar("Modify", bound=Callable[[S, tuple[X, ...]], M])
    Ready = TypeVar("Ready", bound=Callable[[T], bool])
    Viable = TypeVar("Viable", bound=Callable[[M], bool])
    Whittled = TypeVar("Whittled", bound=Callable[[T], Boolable])
    Whittler = TypeVar("Whittler", bound=Callable[[T, S, tuple[W, ...]], T])
