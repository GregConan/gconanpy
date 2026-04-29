#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2026-03-03
Updated: 2026-03-03
"""
# Import standard libraries
from collections.abc import Iterable

# Import third-party PyPI libraries
import pandas as pd

# Import local custom libraries
from gconanpy.iters import Randoms
from gconanpy.testers import Tester


class TryFilterDFTester(Tester):
    def randf(self) -> pd.DataFrame:
        COL_NAMES = Randoms.randtuples()
        return pd.DataFrame()

    def test_1(self) -> None:
        ...
