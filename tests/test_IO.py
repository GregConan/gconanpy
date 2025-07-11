#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-07-08
Updated: 2025-07-10
"""
# Import standard libraries
import re

# Import local custom libraries
from gconanpy.IO.web import SoupTree
from gconanpy.testers import Tester
from gconanpy.ToString import Branches


class TestIOWeb(Tester):

    def test_SoupTree_prettify(self) -> None:
        soup = self.get_soup()
        stree = SoupTree.from_soup(soup)
        branch = Branches()
        invalid = re.compile(f"({branch.T})(?:{branch.X})*"
                             f"({branch.I}|{branch.L}|{branch.T})")
        pretty = stree.prettify(branch=branch)
        assert invalid.match(pretty) is None
