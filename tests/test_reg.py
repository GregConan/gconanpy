
#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-05-24
Updated: 2025-08-11
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
    LIPSUM = "Lorem ipsum (/ˌlɔ:.rəm 'ip.səm/ LOR-əm IP-səm) is a dummy or placeholder text commonly used in graphic design, publishing, and web development. Its purpose is to permit a page layout to be designed, independently of the copy that will subsequently populate it, or to demonstrate various fonts of a typeface without meaningful text that could be distracting. Lorem ipsum is typically a corrupted version of De finibus bonorum et malorum, a 1st-century BC text by the Roman statesman and philosopher Cicero, with words altered, added, and removed to make it nonsensical and improper Latin. The first two words are the truncation of dolorem ipsum ('pain itself'). Versions of the Lorem ipsum text have been used in typesetting since the 1960s, when advertisements for Letraset transfer sheets popularized it.[1] Lorem ipsum was introduced to the digital world in the mid-1980s, when Aldus employed it in graphic and word-processing templates for its desktop publishing program PageMaker. Other popular word processors, including Pages and Microsoft Word, have since adopted Lorem ipsum,[2] as have many LaTeX packages,[3][4][5] web content managers such as Joomla! and WordPress, and CSS libraries such as Semantic UI."

    def test_numbers_in(self) -> None:
        expecteds = [0.5, 50.0, 0.1, 0.0, 0.0, 666.6789, 0.0, 0.0, 0.0, 0.6]
        from_str = "0.5, 50, .1, 000, 0, 666.6789, hell0world, 0w0, var=.6:"
        self.check_result(Regextract.numbers_in(from_str), expecteds)

    def test_iter_parentheticals(self) -> None:
        for parenthetical in Regextract.iter_parentheticals(self.LIPSUM):
            pass  # TODO FIX iter_parenthetials!
