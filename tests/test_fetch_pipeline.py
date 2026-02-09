from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from fxpower.app.fetch import FetchPolicy, compute_fetch_range, update_cache_from_eur_source
from fxpower.storage.cache import read_cache, write_cache


def test_compute_fetch_range_empty_cache_uses_lookback() -> None:
    today = date(2026, 2, 8)
    empty = pd.DataFrame(columns=["date", "base", "quote", "rate"])

    rng = compute_fetch_range(empty, today=today, policy=FetchPolicy(lookback_days=10))
    assert rng == (date(2026, 1, 29), date(2026, 2, 8))


def test_compute_fetch_range_nonempty_cache_fetches_from_next_day() -> None:
    today = date(2026, 2, 8)
    cache = pd.DataFrame(
        [
            {"date": "2026-02-06", "base": "PLN", "quote": "USD", "rate": 4.0},
            {"date": "2026-02-07", "base": "PLN", "quote": "USD", "rate": 4.1},
        ]
    )

    rng = compute_fetch_range(cache, today=today)
    assert rng == (date(2026, 2, 8), date(2026, 2, 8))


def test_update_cache_writes_merged_pairs(tmp_path: Path) -> None:
    cache_file = tmp_path / "cache.parquet"

    # Seed cache with one day (already in final schema)
    seed = pd.DataFrame(
        [
            {"date": "2026-02-01", "base": "PLN", "quote": "USD", "rate": 4.0},
        ]
    )
    write_cache(seed, cache_file)

    calls: list[tuple[date, date]] = []

    def fake_fetch(start: date, end: date) -> pd.DataFrame:
        calls.append((start, end))
        # Return EUR-based series for two dates; must include USD, PLN, GBP (EUR is implicit)
        return pd.DataFrame(
            [
                {"date": "2026-02-02", "quote": "USD", "rate": 1.10},
                {"date": "2026-02-02", "quote": "PLN", "rate": 4.40},
                {"date": "2026-02-02", "quote": "GBP", "rate": 0.88},
                {"date": "2026-02-03", "quote": "USD", "rate": 1.20},
                {"date": "2026-02-03", "quote": "PLN", "rate": 4.50},
                {"date": "2026-02-03", "quote": "GBP", "rate": 0.90},
            ]
        )

    updated = update_cache_from_eur_source(
        cache_path=cache_file,
        fetch_eur_series=fake_fetch,
        today=date(2026, 2, 8),
        policy=FetchPolicy(lookback_days=365 * 5),
    )

    # Should fetch from max_date+1 (seed max is 2026-02-01) to today
    assert calls == [(date(2026, 2, 2), date(2026, 2, 8))]

    # Updated cache should include cross rates for 2026-02-02 and 2026-02-03 (12 per day)
    # plus the original seed row (may get deduped/kept)
    loaded = read_cache(cache_file)

    day2 = loaded[loaded["date"].astype(str) == "2026-02-02"]
    day3 = loaded[loaded["date"].astype(str) == "2026-02-03"]
    assert len(day2) == 12
    assert len(day3) == 12

    # Ensure returned dataframe matches what's on disk
    assert len(updated) == len(loaded)
