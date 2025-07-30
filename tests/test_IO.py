#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2025-07-08
Updated: 2025-07-29
"""
# Import standard libraries
import re

# Import local custom libraries
from gconanpy.testers import Tester
from gconanpy.wrappers import Branches, SoupTree


class TestIOWeb(Tester):

    def test_SoupTree_prettify(self) -> None:
        soup = self.get_soup()
        stree = SoupTree.from_soup(soup)
        branch = Branches()
        invalid = re.compile(f"({branch.T})(?:{branch.X})*"
                             f"({branch.I}|{branch.L}|{branch.T})")
        pretty = stree.prettify(branch=branch)
        assert invalid.match(pretty) is None
