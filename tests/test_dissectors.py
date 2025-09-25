#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-03-28
Updated: 2025-09-24
"""
# Import standard libraries
from typing import Any, cast

# Import local custom libraries
from gconanpy.access.dissectors import \
    Corer, DifferenceBetween, Shredder, Xray
from gconanpy.iters import SimpleShredder
from gconanpy.iters.filters import MapSubset
from gconanpy.mapping.dicts import Cryptionary, DotDict
from gconanpy.testers import Tester


class TestShredders(Tester):
    TEST_CLASSES: tuple[type[SimpleShredder], ...] = (
        Corer, Shredder, SimpleShredder)

    def test_1(self):
        self.add_basics()
        for shredder_type in self.TEST_CLASSES:  # (Shredder, SimpleShredder):
            shredder = shredder_type()
            shredded = shredder.shred(('OK', [self.bytes_nums]))
            self.check_result(shredded, {'OK', self.bytes_nums.strip()})

    def test_2(self):
        shreddables = [list, dict, set, tuple]
        soup = self.get_soup()
        for shredder_type in self.TEST_CLASSES:
            for chunk in shredder_type().shred(soup):
                for shreddable in shreddables:
                    assert not isinstance(chunk, shreddable)


class TestCorers(Tester):
    TEST_CLASSES: tuple[type[Corer], ...] = (Corer, )

    def core_tests(self, to_core: Any, expected_result: Any,
                   **corer_kwargs: Any):
        as_type = type(expected_result)
        for corer_type in self.TEST_CLASSES:
            corer = corer_type(**corer_kwargs)
            for cored in (corer.core(to_core),
                          corer.safe_core(to_core, as_type=as_type)):
                self.check_result(cored, expected_result)

    def check_excluder(self, subsetter: MapSubset, expected_result: Any,
                       **corer_kwargs: Any):
        self.core_tests(self.build_cli_args(DotDict, Cryptionary),
                        expected_result, map_filter=subsetter,
                        **corer_kwargs)

    def test_1(self):
        self.add_basics()
        corables = (self.adict, [self.adict, 0, 2])
        for to_core in corables:
            self.core_tests(to_core, 3)

    def test_2(self):
        self.add_basics()
        self.check_excluder(MapSubset(keys_arent="__doc__"),
                            self.bytes_nums.strip())

    def test_3(self):
        emailmsg = ['OK', [(  # Same structure as an IMAP message received
            b"12345 (RFC822 {123456}", b"Delivered-To: test@test.com\r\n"
            b"Received: by 1234:a01:1234:321a:a7:123:abcd:wxyz with SMTP id "
            b"a0b1c2d3e4f5g6h7;\r\n        Sat, 20 Apr 2069 04:20:52 -0700 "
            b"(PDT)\r\nX-Google-Smtp-Source: AGHT+ABCDEFGHIJKLMNOPQRSTUVWXYZ0"
            b"+abcdefghijklmnopqrstu+vwxyz123/1234567890xD\r\nX-Received: by "
            b"4321:a05:9876:5432:h8:6x9:420c:4hi7 with SMTP id 1234567890xyz"
            b"-a0b1c2d3e4f5g6h7i8j9k0l.42.1234567890123;\r\n        Sat, 20 "
            b"Apr 2069 04:44:52 -0700 (PDT)\r\nARC-Seal: i=1; a=rsa-sha256; "
            b"t=1234567890; cv=none;\r\n        d=googl"), b")"]]
        for to_core in (emailmsg, [0, emailmsg]):
            self.core_tests(to_core, emailmsg[1][0][1])

    def test_4(self):
        soup = self.get_soup()
        for corer_type in self.TEST_CLASSES:
            corer = corer_type()
            for cored in (corer.core(soup), corer.safe_core(soup, as_type=str)):
                print(cored)
                assert cast(str, cored).strip().startswith("Thank you")

    def test_5(self):
        cli_args = self.build_cli_args(DotDict, Cryptionary)
        print(f"cli_args: {cli_args}")
        excluder = MapSubset(keys_are="b")
        self.core_tests(cli_args, 2, map_filter=excluder)

    def test_6(self):
        emailIDs = b'17781 17785 18051 18052'
        id_container = ('OK', [emailIDs])
        self.core_tests(id_container, emailIDs)


class TestDifferenceBetween(Tester):
    def check_diff(self, a_diff: DifferenceBetween, what_differs: str,
                   *expected_diffs: Any):
        self.check_result(a_diff.difference, what_differs)
        for i in range(len(expected_diffs)):
            self.check_result(a_diff.diffs[i], expected_diffs[i])

    def test_no_diff(self):
        self.add_basics()
        for x in (self.alist, self.adict, self, 1, None, "the"):
            sames = DifferenceBetween(x, x)
            assert not sames.diffs
            sames = DifferenceBetween(x, x, x)
            assert not sames.diffs

    def test_len_diff(self):
        self.add_basics()
        longerlist = [*self.alist, max(self.alist) + 1]
        list_diff = DifferenceBetween(self.alist, longerlist)
        self.check_diff(list_diff, "length", len(self.alist), len(longerlist))
        summary = "Length differs between list1 and list2:\nLength of list1" \
            f" == {len(self.alist)} and length of list2 == {len(longerlist)}"
        self.check_result(str(list_diff), summary)
        self.check_result(len(list_diff.diffs), 2)

    def test_type_diff(self):
        self.add_basics()
        atuple = tuple(self.alist)
        list_diff = DifferenceBetween(self.alist, atuple)
        self.check_diff(list_diff, "type", list, tuple)

    def test_element_diff(self):
        self.add_basics()
        for ix in range(len(self.alist)):
            otherlist = self.alist.copy()
            otherlist[ix] = 270
            list_diff = DifferenceBetween(self.alist, otherlist)
            print(f"ix {ix}, {self.alist[ix]} ?= {otherlist[ix]}")
            self.check_diff(list_diff, f"element {ix}",
                            self.alist[ix], otherlist[ix])

    def test_attr_diff(self):
        self.add_basics()
        sub1 = MapSubset(keys_arent=self.alist)
        sub2 = MapSubset(values_arent=self.alist)
        sub_diff = DifferenceBetween(sub1, sub2)
        assert sub_diff.difference
        assert sub_diff.difference.startswith("unique attribute(s)")


class TestXray(Tester):
    def test_repr_recursion_err(self):
        class Dummy:
            def __init__(self, txt: str, start: int, end: int):
                self.txt = txt
                self.start = start
                self.end = end

        dummies = [Dummy("hello", 0, 100), Dummy("goodbye", 100, 200)]
        str(Xray(dummies[0]))
