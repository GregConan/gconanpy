
#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-05-24
Updated: 2025-07-28
"""
# Import local custom libraries
from gconanpy.meta.metaclass import MakeMetaclass
from gconanpy.reg import DunderParser, Regextract
from gconanpy.testers import Tester


class TestDunderParser(Tester):
    def pascaltest(self, method_name: str, pascalized: str) -> None:
        self.check_result(self.dp.pascalize(method_name), pascalized)
        new_type = MakeMetaclass.for_methods(method_name, include=True)
        self.check_result(new_type.__name__, f"Supports{pascalized}Meta")
        new_type = MakeMetaclass.for_methods(method_name, include=False)
        self.check_result(new_type.__name__, f"Lacks{pascalized}Meta")

    def test_pascalize(self) -> None:
        self.dp = DunderParser()
        for method_name, pascalized in (
            ("__class_instancecheck__", "ClassInstanceCheck"),
            ("__delattr__", "DelAttr"), ("__delitem__", "DelItem"),
            ("__getattr__", "GetAttr"), ("__getitem__", "GetItem"),
            ("__hash__", "Hash"), ("__iter__", "Iter"),
            ("__init_subclass__", "InitSubclass"),
            ("__instancecheck__", "InstanceCheck"),
            ("__next__", "Next"), ("__qualname__", "QualName"),
            ("__setattr__", "SetAttr"), ("__setitem__", "SetItem"),
            ("__sizeof__", "SizeOf"), ("__subclasscheck__", "SubclassCheck")
        ):
            self.pascaltest(method_name, pascalized)


class TestRegextract(Tester):
    def test_numbers_in(self) -> None:
        expecteds = [0.5, 50.0, 0.1, 0.0, 0.0, 666.6789, 0.0, 0.0, 0.0, 0.6]
        from_str = "0.5, 50, .1, 000, 0, 666.6789, hell0world, 0w0, var=.6:"
        self.check_result(Regextract.numbers_in(from_str), expecteds)
