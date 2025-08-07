#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-04-03
Updated: 2025-07-06
"""
# Import standard libraries
import datetime as dt
from typing import Any

# Import local custom libraries
from gconanpy.debug import ShowTimeTaken
from gconanpy.iters.find import iterfind, modifind, ReadyChecker, UntilFound
from gconanpy.testers import Tester

# Import third-party PyPI libraries
import bs4


class TestModifind(Tester):
    DATE_FORMATS: tuple[str, ...] = (
        "%B %d, %Y", "%b %d", "%b %d, %Y", "%B %d")
    DATE_PREFIX = "Date is "
    DATE_STR = "April 3, 2025"

    @classmethod
    def get_date_from_el(cls, date_str: str) -> dt.date | None:
        datesplit = str.split(date_str, cls.DATE_PREFIX)
        return None if len(datesplit) < 2 else modifind(
            find_in=cls.DATE_FORMATS,
            modify=lambda x: dt.datetime.strptime(datesplit[1], x).date()
        )

    def get_big_set(self):
        return {False, 1, '', 'font-bold', '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #ffffff;', 'rounded-[2px]', 'text-color-brand', 524, 'pb-2', 8210, 'py-3', 8726, 'dropzone', 13336, 13848, 13341, 'true', 'outline: none; text-decoration: none; -ms-interpolation-mode: bicubic; position: relative; display: inline-block; height: 64px; width: 64px; border-radius: 2px; background-color: #eae6df;', '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt; padding-left: 24px; padding-right: 24px; padding-bottom: 24px;', '84', 12331, '_blank', 15417, None, 9280, 15425, 'tbody', 'w-[84px]', '=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0 =CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0 =CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0 =CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0', 9288, 15430, 'middle', 'pb-3', 9293, 'cursor: pointer; display: inline-block; text-decoration: none; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; font-size: 16px; line-height: 1.25; color: #0a66c2;', 'h3', 'w-full', 'sizes', 7767, 'w-[32px]', 'border-color-divider', 5215, 'h-[21px]', 7775, 'accept-charset', self.DATE_PREFIX + self.DATE_STR, 7780, '!w-[512px]', 'border-0', 'outline: none; text-decoration: none; -ms-interpolation-mode: bicubic; height: 21px; width: 84px;', 'https://www.youtube.com', 'headers', 'pt-1', 'my-0', bs4.element.NavigableString('outline: none; text-decoration: none; -ms-interpolation-mode: bicubic; height: 32px; width: 32px; border-radius: 100%;'), '48', 10371, 'color: #0a66c2; cursor: pointer; display: inline-block; text-decoration: none; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; width: 84px;', 'https://commons.wikimedia.org/wiki/File:MtMcLoughlin.jpg', 'ltr', '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt; padding-bottom: 4px;', 'm-0', 'Your Name', 'invisible', '512', 4255, 4263, 'min-w-full', 'opacity-0', 4268, 'w-6', 11951, '!max-w-[512px]', 7345, 7350, 13496, 10937, 'leading-[20px]', 15549, 'p-0', 6846, 'rev', 8383, 'table', 'leading-regular', 15047, '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt; padding-top: 24px; padding-bottom: 24px;', 15052, '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt; min-width: 100%;', 'Your application was sent to HireTalent - Staffing & Recruiting Firm', '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt; padding: 24px; text-align: center;', 'tr', 7899, 'pb-0.5', 'relative', 5857, 'max-h-[0]', bs4.element.AttributeValueList, 3817, '0', 5865, 5870, '32', 'rounded-[100%]', 3825, 'pre', 8945, 'text-md', 'text-system-gray-100', 3830, '21', 8950, 'mx-auto', 'text-sm', 'h-8', 'border-solid', 9487, 'class', '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt; padding-bottom: 2px;', 'w-8', 'pl-2', 'border-t-1', 14116, 'https://en.wikipedia.org/wiki/Main_Page', 14632, 14121, 'textarea', 828, 11069, 'ml-8', 4416, self.get_soup(), '100%', 'top', 14665, 'color: #0a66c2; cursor: pointer; display: inline-block; text-decoration: none; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%;', 'w-0', 3408, 'center', 'pb-0.25', '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt; margin-left: auto; margin-right: auto; margin-top: 0px; margin-bottom: 0px; padding: 0px; width: 512px !important; max-width: 512px !important;', 3416, 'text-transparent', '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt;', 'bg-color-entity-ghost-background', 'Back End Developer', 'overflow-hidden', 3421, 'margin: 0; padding-top: 24px; padding-bottom: 24px; font-size: 16px; font-weight: 600; line-height: 1.25; color: #282828;', 5472, 'bg-color-background-canvas', 15206, 'mercado-container', 9069, 'rel', '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt; width: 32px;', 'margin: 0; font-weight: 400; margin-top: -16px; margin-left: 64px; padding-left: 16px; font-size: 14px; line-height: 20px; color: #666666;', 'margin: 0; font-weight: 400; font-size: 14px; line-height: 20px; color: #1f1f1f;', 7550, 'text-system-gray-90', 'presentation', 12162, 7556, '64', 'img', 12170, 'accesskey', 12175, 8594, "-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; margin: 0px; width: 100%; background-color: #f3f2f0; padding: 0px; padding-top: 8px; font-family: -apple-system, system-ui, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', 'Fira Sans', Ubuntu, Oxygen, 'Oxygen Sans', Cantarell, 'Droid Sans', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Lucida Grande', Helvetica, Arial, sans-serif;", 'text-xl', 'px-3', 'p', 2969, 8602, 'visibility: hidden; height: 0px; max-height: 0; width: 0px; overflow: hidden; opacity: 0; mso-hide: all;', bs4.element.CData, 8607, '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt; width: 48px; padding-right: 16px;', 14240, 'font-sans', 8937, 'https://images.pexels.com/photos/443446/pexels-photo-443446.jpeg?cs=srgb&dl=daylight-forest-glossy-443446.jpg&fm=jpg', 4008, 6060, 'h-[32px]', 'archive', '[document]', 'h-0', 'a', 'https://yt3.ggpht.com/4ZD3HoTnJjKwn9HvPGC0wmFMFrOwhFSCqP8pqJPOBQe_L27c_YeQHupSp98uFY841DSUKCgvYXM=s200-w144-h200-c-k-c0x00ffffff-no-nd-rj', 'body', 'left', 14784, 'inline-block', 'pt-3', 'text-center', 'p-3', 3540, 'https://www.google.com/search?q=search+query&sca_esv=a1b2c3d4e5f6g78h&sxsrf=A1B2C3D4E5F6G7H8I9J0a1b2c3d4e5f6g7h8i90j1k2l3m4n5o6p&source=hi&ei=IQHvZ9z6JOev0PEP89yh6QE&iflsig=ACkRmUkAAAAAZ-8PMQpM7EOEMUWF-K4UO0Tr3r5A3QZp&ved=0ahUKEwicj4zY6ryMAxXnFzQIHXNuKB0Q4dUDCBo&uact=5&oq=search+query&gs_lp=E35rJPrgQ26SgDKUufnKP47gWVnUVV2649nC6pBvxU6dbhbp6fWJyG8Zq21zqmGTinT5iSYQKfgyF9zefd0d8ZGa3p86vVumCdhqyzPNJ2VPCj8W28BfhXL3J24fZQVjXykZiqCqAVbE6LPJ5eq6SqwqHrzkzb1Nm578dtaVKQNDE5EUS8YK66nnvc0rzXZTw4i5a28karKDBDSZFhxabm2ZfkpebtgdVdiXhXr6DShPXQVCqb8935qMWht5LCQmN6arqJBCZUffJZqddTtZ88ejCYm93cgnMNtJzRFfE6dA6ANBFuDh8F179YbEEqQxE6MyrjQb3wnj2kZ4TQrqBagS19VxdpzvEePSk0SXYHXn5CSPdWp7NhADLmXKR89DiRnTrKyPKiHBzYArHhnJRK7kKKiwRpV5nKGCLP5Rt1WrdyZYCV61pUJmRgYhuNN4FV8WPAFGUpN-hbBKwqQfNwJERPETXwnu50KbNJheeJ&sclient=gws-wiz', 'sandbox', 'for', 'td', 'div', 'pr-2', 8170, 'h2', '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt; padding-bottom: 16px;', 'margin: 0; border-width: 0; border-top-width: 1px; border-style: solid; border-color: rgba(0, 0, 0, 0.08); padding-top: 24px; font-size: 24px; font-weight: 600; line-height: 1.25; color: #282828;', 'bg-color-background-container', 5621, 'text-system-gray-70', 'margin: 0; padding-top: 24px; font-size: 24px; font-weight: 600; line-height: 1.25;color: #282828;', 'right'}

    def test_modifind(self):
        with ShowTimeTaken("testing Modifind"):
            bigset = self.get_big_set()
            datefrom = self.get_date_from_el(self.DATE_PREFIX + self.DATE_STR)
            self.validatedate(datefrom)
            gotten = modifind(find_in=bigset, modify=self.get_date_from_el,
                              default="wrong")
            self.validatedate(gotten)

    def validatedate(self, date_obj: Any):
        assert isinstance(date_obj, dt.date)
        assert date_obj.year == 2025
        assert date_obj.month == 4
        assert date_obj.day == 3
        print(f"Validated {date_obj}")


class TestReadyChecker(Tester):
    REMOVABLES = (", Extra.", "Extra", "A.B.C", "ABC", "The")

    def test_ready_checker(self):
        full_name = "The Big Shortenable Thing Name ABC, Extra."
        for max_len, result in ((30, "Big Shortenable Thing Name"),
                                (40, "The Big Shortenable Thing Name ABC")):
            with ReadyChecker(to_check=full_name, iter_over=self.REMOVABLES,
                              ready_if=lambda x: len(x) < max_len) as check:
                while check.is_not_ready():
                    check(str.replace(check.to_check, str(next(check)),
                                      " ").strip())
            self.check_result(check.to_check, result)


class TestIterFind(Tester):
    @staticmethod
    def greater(x, y):
        return x > y

    def test_iterfind(self):
        self.add_basics()
        for eachnum in self.alist:
            bigger = iterfind(self.alist, self.greater, [eachnum],
                              default=max(self.alist) + 1)
            self.check_result(bigger, eachnum + 1)

    def test_UntilFound(self):
        self.add_basics()
        for eachnum in self.alist:
            bigger = UntilFound(self.greater, post=[eachnum]).check_each(
                self.alist, default=max(self.alist) + 1)
            self.check_result(bigger, eachnum + 1)
