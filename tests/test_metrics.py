from __future__ import annotations

import math

import pandas as pd

from fxpower.analytics.metrics import momentum, percentile_rank, volatility, zscore


def test_percentile_rank_basic() -> None:
    h = pd.Series([1, 2, 3, 4, 5])
    assert percentile_rank(h, 3) == 3 / 5
    assert percentile_rank(h, 1) == 1 / 5
    assert percentile_rank(h, 10) == 1.0


def test_zscore_constant_series_is_zero() -> None:
    h = pd.Series([2, 2, 2, 2])
    assert zscore(h, 2) == 0.0
    assert zscore(h, 10) == 0.0  # sigma==0 => 0


def test_momentum_simple() -> None:
    s = pd.Series([100, 110, 121])
    # window=2: last=121, value 2 steps ago=100 -> 0.21
    m = momentum(s, window=2)
    assert abs(m - 0.21) < 1e-12


def test_volatility_known_log_returns() -> None:
    # If prices double each step: log return = ln(2) constant => vol = 0
    s = pd.Series([1, 2, 4, 8, 16, 32])
    v = volatility(s, window=3, annualization_factor=252)
    assert abs(v - 0.0) < 1e-12

    # If returns vary, volatility should be > 0
    s2 = pd.Series([1, 2, 3, 2, 4, 3])
    v2 = volatility(s2, window=3, annualization_factor=252)
    assert not math.isnan(v2)
    assert v2 > 0.0
