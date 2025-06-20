
#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-05-24
Updated: 2025-06-20
"""
# Import local custom libraries
from gconanpy.meta.funcs import metaclass_hasmethod
from gconanpy.reg import DunderParser
from tests.testers import Tester


class TestDunderParser(Tester):
    def pascaltest(self, method_name: str, pascalized: str) -> None:
        self.check_result(self.dp.pascalize(method_name), pascalized)
        new_type = metaclass_hasmethod(method_name, include=True)
        self.check_result(new_type.__name__, f"Supports{pascalized}Meta")
        new_type = metaclass_hasmethod(method_name, include=False)
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
