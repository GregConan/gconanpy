#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-03-28
Updated: 2025-03-30
"""
# Import local custom libraries
from gconanpy.dissectors import Corer, RollingPin
from tests.testers import Tester


class TestDissectors(Tester):
    def test_1(self):
        self.add_basics()
        corer = Corer()
        cored = corer.core(self.adict)
        self.check_result(cored, 1)

    def test_2(self):
        self.add_basics()
        rolled = RollingPin().flatten(('OK', [self.bytes_nums]))
        self.check_result(rolled, ['OK', self.bytes_nums])

    def test_3(self):
        self.add_cli_args()
        cored = Corer(exclude={"__doc__"}).core(self.cli_args)
        self.check_result(cored, self.bytes_nums)

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
        cored = Corer(exclude={"__doc__"}).core(emailmsg)
        self.check_result(cored, emailmsg[1][0][1])
