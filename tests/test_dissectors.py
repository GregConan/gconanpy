#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-03-28
Updated: 2025-04-01
"""
# Import local custom libraries
from gconanpy.dissectors import Corer, Shredder
from tests.testers import Tester


class TestDissectors(Tester):
    def test_1(self):
        self.add_basics()
        corer = Corer()
        for to_core in (self.adict, [self.adict, 0, 2]):
            cored = corer.core(to_core)
            self.check_result(cored, 3)

    def test_2(self):
        self.add_basics()
        rolled = Shredder().shred(('OK', [self.bytes_nums]))
        self.check_result(rolled, {'OK', self.bytes_nums.strip()})

    def test_3(self):
        cli_args = self.build_cli_args()
        cored = Corer(exclude={"__doc__"}).core(cli_args)
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
        shredder = Shredder()
        shredded = shredder.shred(soup)
        for x in shredded:
            for shreddable in shreddables:
                assert not isinstance(x, shreddable)

    def test_6(self):
        soup = self.get_soup()
        cored = Corer().core(soup)
        print(cored)
        assert cored.strip().startswith("Thank you")

        # pdb.set_trace()
        # print()
