#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-04-22
Updated: 2025-04-22
"""
# Import standard libraries
from collections.abc import Iterable
import inspect

# Import local custom libraries
from gconanpy.extend import weak_dataclass, all_annotations_of
from gconanpy.metafunc import nameof
from gconanpy.seq import stringify_list
from tests.testers import Tester


class TestExtend(Tester):
    def check_args_err(self, a_class: type, err_type: type[BaseException],
                       err_msg: str | None = None, args: Iterable = list(),
                       **kwargs) -> None:
        passed = True
        try:
            a_class(*args, **kwargs)
            passed = False
        except err_type as err:
            if err_msg:
                self.check_result(str(err), err_msg)
        assert passed

    def test_weak_dataclass(self) -> None:
        @weak_dataclass
        class Person:
            # Input parameters without default values
            name: str

            # Attributes and input parameters with default values
            description: str = "Description"
            age: int = 21

        @weak_dataclass
        class Sibling(Person):
            siblings: int = 0

        @weak_dataclass
        class Parent(Person):
            children: list[Person]

        err_1 = "__init__() missing 1 required positional argument: 'name'"
        self.check_args_err(Person, TypeError, err_1)
        self.check_args_err(Sibling, TypeError, err_1)
        err_2 = ("__init__() missing 2 required positional arguments: "
                 "'name' and 'children'")
        self.check_args_err(Parent, TypeError, err_2)

        for person_class in (Person, Sibling, Parent):
            self.check_args_err(person_class, TypeError, wrong="WRONG")

        james = Sibling("James", siblings=1)
        jim = Parent("Jimothy", [james])
        self.check_result(len(jim.children), 1)
        self.check_result(jim.children[0], james)
        jamesstr = "Sibling(name=James, description=Description, age=21, " \
            "and siblings=1)"
        self.check_result(str(james), jamesstr)
        assert jim != james
