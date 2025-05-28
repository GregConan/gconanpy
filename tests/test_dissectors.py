#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-03-28
Updated: 2025-05-26
"""
# Import standard libraries
from typing import Any

# Import local custom libraries
from gconanpy.dissectors import Corer, DifferenceBetween, Shredder, \
    SimpleShredder, Xray
from gconanpy.maptools import MapSubset
from tests.testers import Tester


class TestShredders(Tester):
    TEST_CLASSES = (Corer, Shredder, SimpleShredder)

    def test_1(self):
        self.add_basics()
        corer = Corer()
        for to_core in (self.adict, [self.adict, 0, 2]):
            cored = corer.core(to_core)
            self.check_result(cored, 3)

    def test_2(self):
        self.add_basics()
        for shredder_type in (Shredder, SimpleShredder):
            rolled = shredder_type().shred(('OK', [self.bytes_nums]))
            self.check_result(rolled, {'OK', self.bytes_nums.strip()})

    def test_3(self):
        cli_args = self.build_cli_args()
        excluder = MapSubset(keys={"__doc__"}, include_keys=False).filter
        cored = Corer(map_filter=excluder).core(cli_args)
        self.check_result(cored, self.bytes_nums.strip())

    def test_4(self):
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
            cored = Corer().core(to_core)  # exclude={"__doc__"}
            self.check_result(cored, emailmsg[1][0][1])

    def test_5(self):
        shreddables = [list, dict, set, tuple]
        soup = self.get_soup()
        for shredder_type in self.TEST_CLASSES:
            for chunk in shredder_type().shred(soup):
                for shreddable in shreddables:
                    assert not isinstance(chunk, shreddable)

    def test_6(self):
        soup = self.get_soup()
        cored = Corer().core(soup)
        print(cored)
        assert cored.strip().startswith("Thank you")  # type: ignore

    def test_7(self):
        cli_args = self.build_cli_args()
        excluder = MapSubset(keys={"b"}, include_keys=True).filter
        cored = Corer(map_filter=excluder).core(cli_args)
        print(cored)
        self.check_result(cored, 2)


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
        sub1 = MapSubset(keys=self.alist)
        sub2 = MapSubset(values=self.alist)
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
