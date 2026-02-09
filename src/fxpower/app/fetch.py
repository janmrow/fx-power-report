from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from fxpower.analytics.cross_rates import generate_cross_rates_from_eur_series
from fxpower.storage.cache import merge_cache, read_cache, write_cache


@dataclass(frozen=True, slots=True)
class FetchPolicy:
    lookback_days: int = 365 * 5  # ~5 years, intentionally approximate
    min_start_date: date | None = None  # optional hard floor


def _normalize_today(today: date | None) -> date:
    return today or date.today()


def _max_cache_date(cache_df: pd.DataFrame) -> date | None:
    if cache_df.empty:
        return None
    # cache 'date' is stored as datetime.date already (validated), but be defensive
    d = pd.to_datetime(cache_df["date"]).dt.date.max()
    return d if isinstance(d, date) else None


def compute_fetch_range(
    cache_df: pd.DataFrame,
    today: date,
    policy: FetchPolicy | None = None,
) -> tuple[date, date] | None:
    """Return (start, end) range to fetch, or None if nothing to fetch."""
    policy = policy or FetchPolicy()
    max_date = _max_cache_date(cache_df)

    if max_date is None:
        start = today - timedelta(days=policy.lookback_days)
    else:
        start = max_date + timedelta(days=1)

    if policy.min_start_date is not None and start < policy.min_start_date:
        start = policy.min_start_date

    end = today

    if start > end:
        return None
    return start, end


# Type: fetch EUR-based time series (date, quote, rate where rate=QUOTE per 1 EUR)
EurFetchFn = Callable[[date, date], pd.DataFrame]


def update_cache_from_eur_source(
    cache_path: Path,
    fetch_eur_series: EurFetchFn,
    today: date | None = None,
    policy: FetchPolicy | None = None,
) -> pd.DataFrame:
    """Update local cache by fetching missing EUR-based rates and computing cross pairs.

    Returns updated cache dataframe.
    """
    t = _normalize_today(today)
    existing = read_cache(cache_path)
    fetch_range = compute_fetch_range(existing, today=t, policy=policy)
    if fetch_range is None:
        return existing

    start, end = fetch_range
    eur_series = fetch_eur_series(start, end)

    incoming = generate_cross_rates_from_eur_series(eur_series)
    merged = merge_cache(existing, incoming)
    write_cache(merged, cache_path)
    return merged
