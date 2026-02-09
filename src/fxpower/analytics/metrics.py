from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True, slots=True)
class MetricDefaults:
    vol_window: int = 90
    mom_window: int = 60
    sma_window: int = 200
    annualization_factor: int = 252  # trading days


def _as_series(values: pd.Series) -> pd.Series:
    s = pd.to_numeric(values, errors="coerce").astype("float64")
    return s


def percentile_rank(history: pd.Series, value: float) -> float:
    """Return percentile rank in [0, 1] of `value` within `history` (ignoring NaNs)."""
    h = _as_series(history).dropna()
    if h.empty:
        return float("nan")
    # "percent of values <= value"
    return float((h.le(value)).mean())


def zscore(history: pd.Series, value: float) -> float:
    """Z-score of `value` relative to `history` (ignoring NaNs)."""
    h = _as_series(history).dropna()
    if h.empty:
        return float("nan")
    mu = float(h.mean())
    sigma = float(h.std(ddof=0))
    if sigma == 0.0:
        return 0.0
    return (value - mu) / sigma


def sma(series: pd.Series, window: int) -> pd.Series:
    s = _as_series(series)
    return s.rolling(window=window, min_periods=window).mean()


def momentum(series: pd.Series, window: int) -> float:
    """Return simple momentum: last / value_window_ago - 1."""
    s = _as_series(series).dropna()
    if len(s) <= window:
        return float("nan")
    last = float(s.iloc[-1])
    prev = float(s.iloc[-(window + 1)])
    if prev == 0.0:
        return float("nan")
    return last / prev - 1.0


def log_returns(series: pd.Series) -> pd.Series:
    s = _as_series(series)
    return (s / s.shift(1)).apply(lambda x: math.log(x) if pd.notna(x) and x > 0 else float("nan"))


def volatility(series: pd.Series, window: int, annualization_factor: int = 252) -> float:
    """Annualized volatility based on rolling window of log returns."""
    r = log_returns(series).dropna()
    if len(r) < window:
        return float("nan")
    window_r = r.iloc[-window:]
    sigma = float(window_r.std(ddof=0))
    return sigma * math.sqrt(annualization_factor)
