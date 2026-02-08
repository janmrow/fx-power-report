from __future__ import annotations

import pandas as pd

from fxpower.storage.cache import merge_cache


def test_merge_deduplicates_by_key_and_incoming_wins() -> None:
    existing = pd.DataFrame(
        [
            {"date": "2026-02-07", "base": "PLN", "quote": "USD", "rate": 4.10},
            {"date": "2026-02-07", "base": "PLN", "quote": "EUR", "rate": 4.30},
        ]
    )

    incoming = pd.DataFrame(
        [
            # overwrite same key (date, base, quote)
            {"date": "2026-02-07", "base": "PLN", "quote": "USD", "rate": 4.04},
            # new row
            {"date": "2026-02-08", "base": "PLN", "quote": "USD", "rate": 4.05},
        ]
    )

    merged = merge_cache(existing, incoming)

    # no duplicates by (date, base, quote)
    assert merged.duplicated(subset=["date", "base", "quote"]).sum() == 0

    # incoming wins
    row = merged[
        (merged["date"] == merged["date"].iloc[0])
        & (merged["base"] == "PLN")
        & (merged["quote"] == "USD")
    ]
    # easier: locate exact day
    row = merged[
        (merged["date"].astype(str) == "2026-02-07")
        & (merged["base"] == "PLN")
        & (merged["quote"] == "USD")
    ]
    assert len(row) == 1
    assert float(row.iloc[0]["rate"]) == 4.04


def test_merge_is_idempotent() -> None:
    df = pd.DataFrame(
        [
            {"date": "2026-02-07", "base": "PLN", "quote": "USD", "rate": 4.04},
            {"date": "2026-02-07", "base": "PLN", "quote": "EUR", "rate": 4.30},
        ]
    )

    once = merge_cache(df, df)
    twice = merge_cache(once, df)

    assert once.equals(twice)
