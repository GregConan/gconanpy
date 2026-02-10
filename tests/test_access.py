#!/usr/bin/env python3

"""
Test functionality of the functions and classes defined in gconanpy/access/*.py
Greg Conan: gregmconan@gmail.com
Created: 2025-09-11
Updated: 2026-02-09
"""
# Import standard libraries
from collections import defaultdict
from collections.abc import Callable, Iterable
from copy import deepcopy
import datetime as dt
import itertools
import operator
import random
import string
from timeit import timeit
from typing import Any, cast

# Import third-party PyPI libraries
import bs4

# Import local custom libraries
from gconanpy.access import attributes
from gconanpy.access.find import iterfind, modifind, ReadyChecker, \
    Spliterator, UntilFound
from gconanpy.access.nested import Corer, DifferenceBetween, Shredder, Xray
from gconanpy.debug import ShowTimeTaken
from gconanpy.iters import SimpleShredder
from gconanpy.iters.filters import MapSubset
from gconanpy.mapping.dicts import Cryptionary, DotDict, Sortionary
from gconanpy.testers import Tester
from gconanpy.trivial import always_false, always_none, always_true

# NOTE: Classes below are in alphabetical order.


class TestAccessSpeed(Tester):
    # Remove initial underscore to test_access_speed to view time test
    def _test_access_speed(self) -> None:
        self.add_basics()
        randstr = "".join(random.choices(
            string.ascii_letters + string.digits, k=100))
        arbitraries = dict(anint=-1234, atup=(1, 2, 3), alist=self.alist,
                           adict=self.adict, afloat=-3.14159265358,
                           astr=f"'{randstr}'")
        # allattrs = ('anint', 'atup', 'alist', 'adict', 'afloat', 'astr')
        allattrs = tuple(arbitraries)
        to_test = ("obj.{}",  # Test default getters
                   "adict['{}']",
                   "adict.get('{}')",
                   "getattr(obj, '{}')",
                   "hasattr(obj, '{}')",
                   "operator.getitem(adict, '{}')",
                   "operator.contains(adict, '{}')",
                   "dict.__contains__(adict, '{}')",
                   "'{}' in adict",
                   "dict.__getitem__(adict, '{}')",
                   "dict.get(adict, '{}')",
                   "Mapping.get(adict, '{}')",
                   "object.__getattribute__(obj, '{}')",

                   # Test custom getters from meta/__init__.py
                   "getdefault(adict, '{}')",
                   "method_get(adict, '{}')",
                   "method_getattribute(obj, '{}')",
                   "method_getitem(adict, '{}')",

                   # Test custom getters from meta/access.py
                   "Access.item.get(adict, '{}')",
                   "Access.item.getdefault(adict, '{}')",
                   "Access.item.contains(adict, '{}')",
                   "Access.attribute.get(obj, '{}')",
                   "Access.attribute.contains(obj, '{}')",
                   "ACCESS['item'].get(adict, '{}')",
                   "ACCESS['item'].getdefault(adict, '{}')",
                   "ACCESS['item'].contains(adict, '{}')",
                   "ACCESS['attribute'].get(obj, '{}')",
                   "ACCESS['attribute'].contains(obj, '{}')",

                   # Test default setters
                   "setattr(obj, '{}', None)",
                   "object.__setattr__(obj, '{}', None)",
                   "dict.setdefault(adict, '{}', None)",
                   "adict.setdefault('{}', None)",
                   "setdefault(adict, '{}', None)",
                   "adict['{}'] = None",
                   "obj.{} = None",

                   # Test custom setters
                   "method_setattr(obj, '{}', None)",
                   "method_setitem(adict, '{}', None)",
                   "attributes.setdefault(obj, '{}', None)",
                   "Access.item.set_to(adict, '{}', None)",
                   "Access.attribute.set_to(obj, '{}', None)",
                   "ACCESS['item'].set_to(adict, '{}', None)",
                   "ACCESS['attribute'].set_to(obj, '{}', None)")

        SETUP = f"""import operator
from typing import Mapping

try:
    from gconanpy import attributes
    from gconanpy.meta import method
    from gconanpy.meta.access import ACCESS, Access, getdefault, setdefault
except (ImportError, ModuleNotFoundError):
    import attributes
    from meta import method
    from meta.access import ACCESS, Access, getdefault, setdefault


class BareObject():
    ''' Bare/empty object to freely add new attributes to. Must be defined in
        the same file where it is used. '''


method_get = method('get')
method_getattribute = method('__getattribute__')
method_getitem = method('__getitem__')
method_setattr = method('__setattr__')
method_setitem = method('__setitem__')

obj = BareObject()
obj.anint={arbitraries['anint']}
obj.atup={arbitraries['atup']}
obj.alist={arbitraries['alist']}
obj.adict={arbitraries['adict']}
obj.afloat={arbitraries['afloat']}
obj.astr={arbitraries['astr']}

adict={arbitraries}
allattrs={allattrs}
"""
        times = {eachcall: sum([
            timeit(eachcall.format(ex), setup=SETUP, number=200000)
            for ex in allattrs]) for eachcall in to_test}  # for _ in range(5)
        # sumtimes = {x: 0.0 for x in times.keys()}
        sumtimes = defaultdict(float)
        keys = defaultdict(set)
        newkeys = ("dict", "method", "operator", "Mapping", "adict", "access",
                   "Access", "ACCESS", "attributes")
        for k in times:
            new_key = None
            for new_k in newkeys:
                if k.startswith(new_k):
                    new_key = new_k
                    break
            if not new_key:
                new_key = "adict" if k.endswith("adict") \
                    else "attr" if len(k) > 7 and k[3:7] == "attr" \
                    else "access" if k[1:10] == "etdefault" else "default"
            keys[new_key].add(k)

        # Sort each access method, and category average thereof, by time taken
        for newkey, oldkeys in keys.items():
            for old in oldkeys:
                sumtimes[newkey] += times[old]
            sumtimes[newkey] /= len(oldkeys)
        to_print = [f"{k} = {round(v * 1000, 3)}" for d in (times, sumtimes)
                    for k, v in Sortionary(**d).sorted_by("values")]

        # Check how far to the right to justify the printed text so all of the
        # times line up in the output, then print them
        indent = max(len(eachline) for eachline in to_print)
        for eachline in to_print:
            print(eachline.rjust(indent))

        assert False


class TestAttributesFunctions(Tester):
    _LazyMeth = Callable[[Any, str, Callable], Any]
    NO_EXPECTED = object()
    TRIVIALS = {False: always_false, True: always_true, None: always_none}

    class HasFoo:
        foo: Any

    def check_lazy(self, an_obj: Any, name: str, lazy_meths:
                   Iterable[_LazyMeth], expected_result: Any = NO_EXPECTED,
                   **kwargs: Any):
        for lazy_meth in lazy_meths:
            for result, fn in self.TRIVIALS.items():
                self.check_result(lazy_meth(deepcopy(an_obj),
                                            name, fn, **kwargs),
                                  result if expected_result is
                                  self.NO_EXPECTED else expected_result)

    def test_lazyget_1(self) -> None:
        self.add_basics()
        obj = self.HasFoo()
        FOO = "hello"
        ATTR_LAZIES = (attributes.lazyget, attributes.lazysetdefault)
        self.check_lazy(obj, "foo", ATTR_LAZIES)
        setattr(obj, "foo", FOO)
        self.check_lazy(obj, "foo", ATTR_LAZIES, FOO)
        self.check_lazy(obj, "foo", ATTR_LAZIES, exclude={FOO})
        delattr(obj, "foo")
        self.check_lazy(obj, "foo", ATTR_LAZIES)


class TestAttrsOf(Tester):
    EXAMPLE_TYPES: tuple[type, ...] = (
        list, dict, int, float, str, tuple, bytes)

    def test_but_not_1(self) -> None:
        self.add_basics()
        self.check_result(attributes.AttrsOf(self.alist).but_not(self.adict),
                          set(dir(list)) - set(dir(dict)))

    def test_but_not_2(self) -> None:
        for type1, type2 in itertools.combinations(self.EXAMPLE_TYPES, 2):
            self.check_result(attributes.AttrsOf(type1).but_not(type2),
                              set(dir(type1)) - set(dir(type2)))

    def test_methods(self) -> None:
        for each_type in self.EXAMPLE_TYPES:
            for _, meth in attributes.AttrsOf(each_type).methods():
                assert callable(meth)

    def test_public(self) -> None:
        for each_type in self.EXAMPLE_TYPES:
            for name, _ in attributes.AttrsOf(each_type).public():
                assert not name.startswith("_")


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
            f" is {len(self.alist)} and length of list2 is {len(longerlist)}"
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


class TestIterFind(Tester):

    def test_iterfind(self):
        self.add_basics()
        for eachnum in self.alist:
            bigger = iterfind(self.alist, operator.gt, [eachnum],
                              default=max(self.alist) + 1)
            self.check_result(bigger, eachnum + 1)

    def test_UntilFound(self):
        self.add_basics()
        for eachnum in self.alist:
            bigger = UntilFound(operator.gt, post=[eachnum]).check_each(
                self.alist, default=max(self.alist) + 1)
            self.check_result(bigger, eachnum + 1)


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
        return {False, 1, '', 'font-bold', '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt; background-color: #ffffff;', 'rounded-[2px]', 'text-color-brand', 524, 'pb-2', 8210, 'py-3', 8726, 'dropzone', 13336, 13848, 13341, 'true', 'outline: none; text-decoration: none; -ms-interpolation-mode: bicubic; position: relative; display: inline-block; height: 64px; width: 64px; border-radius: 2px; background-color: #eae6df;', '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt; padding-left: 24px; padding-right: 24px; padding-bottom: 24px;', '84', 12331, '_blank', 15417, None, 9280, 15425, 'tbody', 'w-[84px]', '=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0 =CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0 =CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0 =CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0=CD=8F=C2=A0', 9288, 15430, 'middle', 'pb-3', 9293, 'cursor: pointer; display: inline-block; text-decoration: none; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; font-size: 16px; line-height: 1.25; color: #0a66c2;', 'h3', 'w-full', 'sizes', 7767, 'w-[32px]', 'border-color-divider', 5215, 'h-[21px]', 7775, 'accept-charset', self.DATE_PREFIX + self.DATE_STR, 7780, '!w-[512px]', 'border-0', 'outline: none; text-decoration: none; -ms-interpolation-mode: bicubic; height: 21px; width: 84px;', 'https://www.youtube.com', 'headers', 'pt-1', 'my-0', bs4.element.NavigableString('outline: none; text-decoration: none; -ms-interpolation-mode: bicubic; height: 32px; width: 32px; border-radius: 100%;'), '48', 10371, 'color: #0a66c2; cursor: pointer; display: inline-block; text-decoration: none; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; width: 84px;', 'https://commons.wikimedia.org/wiki/File:MtMcLoughlin.jpg', 'ltr', '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt; padding-bottom: 4px;', 'm-0', 'Your Name', 'invisible', '512', 4255, 4263, 'min-w-full', 'opacity-0', 4268, 'w-6', 11951, '!max-w-[512px]', 7345, 7350, 13496, 10937, 'leading-[20px]', 15549, 'p-0', 6846, 'rev', 8383, 'table', 'leading-regular', 15047, '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt; padding-top: 24px; padding-bottom: 24px;', 15052, '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt; min-width: 100%;', '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt; padding: 24px; text-align: center;', 'tr', 7899, 'pb-0.5', 'relative', 5857, 'max-h-[0]', bs4.element.AttributeValueList, 3817, '0', 5865, 5870, '32', 'rounded-[100%]', 3825, 'pre', 8945, 'text-md', 'text-system-gray-100', 3830, '21', 8950, 'mx-auto', 'text-sm', 'h-8', 'border-solid', 9487, 'class', '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt; padding-bottom: 2px;', 'w-8', 'pl-2', 'border-t-1', 14116, 'https://en.wikipedia.org/wiki/Main_Page', 14632, 14121, 'textarea', 828, 11069, 'ml-8', 4416, self.get_soup(), '100%', 'top', 14665, 'color: #0a66c2; cursor: pointer; display: inline-block; text-decoration: none; -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%;', 'w-0', 3408, 'center', 'pb-0.25', '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt; margin-left: auto; margin-right: auto; margin-top: 0px; margin-bottom: 0px; padding: 0px; width: 512px !important; max-width: 512px !important;', 3416, 'text-transparent', '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt;', 'bg-color-entity-ghost-background', 'Back End Developer', 'overflow-hidden', 3421, 'margin: 0; padding-top: 24px; padding-bottom: 24px; font-size: 16px; font-weight: 600; line-height: 1.25; color: #282828;', 5472, 'bg-color-background-canvas', 15206, 'mercado-container', 9069, 'rel', '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt; width: 32px;', 'margin: 0; font-weight: 400; margin-top: -16px; margin-left: 64px; padding-left: 16px; font-size: 14px; line-height: 20px; color: #666666;', 'margin: 0; font-weight: 400; font-size: 14px; line-height: 20px; color: #1f1f1f;', 7550, 'text-system-gray-90', 'presentation', 12162, 7556, '64', 'img', 12170, 'accesskey', 12175, 8594, "-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; margin: 0px; width: 100%; background-color: #f3f2f0; padding: 0px; padding-top: 8px; font-family: -apple-system, system-ui, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', 'Fira Sans', Ubuntu, Oxygen, 'Oxygen Sans', Cantarell, 'Droid Sans', 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Lucida Grande', Helvetica, Arial, sans-serif;", 'text-xl', 'px-3', 'p', 2969, 8602, 'visibility: hidden; height: 0px; max-height: 0; width: 0px; overflow: hidden; opacity: 0; mso-hide: all;', bs4.element.CData, 8607, '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt; width: 48px; padding-right: 16px;', 14240, 'font-sans', 8937, 'https://images.pexels.com/photos/443446/pexels-photo-443446.jpeg?cs=srgb&dl=daylight-forest-glossy-443446.jpg&fm=jpg', 4008, 6060, 'h-[32px]', 'archive', '[document]', 'h-0', 'a', 'https://yt3.ggpht.com/4ZD3HoTnJjKwn9HvPGC0wmFMFrOwhFSCqP8pqJPOBQe_L27c_YeQHupSp98uFY841DSUKCgvYXM=s200-w144-h200-c-k-c0x00ffffff-no-nd-rj', 'body', 'left', 14784, 'inline-block', 'pt-3', 'text-center', 'p-3', 3540, 'https://www.google.com/search?q=search+query&sca_esv=a1b2c3d4e5f6g78h&sxsrf=A1B2C3D4E5F6G7H8I9J0a1b2c3d4e5f6g7h8i90j1k2l3m4n5o6p&source=hi&ei=IQHvZ9z6JOev0PEP89yh6QE&iflsig=ACkRmUkAAAAAZ-8PMQpM7EOEMUWF-K4UO0Tr3r5A3QZp&ved=0ahUKEwicj4zY6ryMAxXnFzQIHXNuKB0Q4dUDCBo&uact=5&oq=search+query&gs_lp=E35rJPrgQ26SgDKUufnKP47gWVnUVV2649nC6pBvxU6dbhbp6fWJyG8Zq21zqmGTinT5iSYQKfgyF9zefd0d8ZGa3p86vVumCdhqyzPNJ2VPCj8W28BfhXL3J24fZQVjXykZiqCqAVbE6LPJ5eq6SqwqHrzkzb1Nm578dtaVKQNDE5EUS8YK66nnvc0rzXZTw4i5a28karKDBDSZFhxabm2ZfkpebtgdVdiXhXr6DShPXQVCqb8935qMWht5LCQmN6arqJBCZUffJZqddTtZ88ejCYm93cgnMNtJzRFfE6dA6ANBFuDh8F179YbEEqQxE6MyrjQb3wnj2kZ4TQrqBagS19VxdpzvEePSk0SXYHXn5CSPdWp7NhADLmXKR89DiRnTrKyPKiHBzYArHhnJRK7kKKiwRpV5nKGCLP5Rt1WrdyZYCV61pUJmRgYhuNN4FV8WPAFGUpN-hbBKwqQfNwJERPETXwnu50KbNJheeJ&sclient=gws-wiz', 'sandbox', 'for', 'td', 'div', 'pr-2', 8170, 'h2', '-webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; mso-table-lspace: 0pt; mso-table-rspace: 0pt; padding-bottom: 16px;', 'margin: 0; border-width: 0; border-top-width: 1px; border-style: solid; border-color: rgba(0, 0, 0, 0.08); padding-top: 24px; font-size: 24px; font-weight: 600; line-height: 1.25; color: #282828;', 'bg-color-background-container', 5621, 'text-system-gray-70', 'margin: 0; padding-top: 24px; font-size: 24px; font-weight: 600; line-height: 1.25;color: #282828;', 'right'}

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


class TestSpliterator(Tester):
    def test_spliterate_1(self):
        spliterator = Spliterator(max_len=20)
        self.check_result(spliterator.spliterate(["Hello", "World"])[0],
                          "Hello World")

    def test_spliterate_2(self):
        spliterator = Spliterator(max_len=10)
        self.check_result(spliterator.spliterate(["Hello", "World"])[0],
                          "Hello")


class TestXray(Tester):
    def test_repr_recursion_err(self):
        class Dummy:
            def __init__(self, txt: str, start: int, end: int):
                self.txt = txt
                self.start = start
                self.end = end

        dummies = [Dummy("hello", 0, 100), Dummy("goodbye", 100, 200)]
        str(Xray(dummies[0]))
