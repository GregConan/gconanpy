#!/usr/bin/env python3

"""
Greg Conan: gregmconan@gmail.com
Created: 2026-03-03
Updated: 2026-05-01
"""
# Import third-party PyPI libraries
import pandas as pd

# Import local custom libraries
from gconanpy.iters import Randoms
from gconanpy.numpandas import randf
from gconanpy.testers import Tester


class TestRandf(Tester):
    def test_randf_init(self) -> None:
        """ Verify that `randf()` works without raising any Exceptions """
        for _ in Randoms.randcount():
            randf()

    def test_randf_monotype(self) -> None:
        """ Verify that every column in `randf()` is homogeneous wrt type """
        df = randf()
        assert df.map(type).apply(pd.Series.unique).shape[0] == 1
