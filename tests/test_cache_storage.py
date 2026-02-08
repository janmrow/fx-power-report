from __future__ import annotations

from pathlib import Path

import pandas as pd

from fxpower.storage.cache import read_cache, write_cache


def test_cache_roundtrip_parquet(tmp_path: Path) -> None:
    cache_file = tmp_path / "cache.parquet"

    original = pd.DataFrame(
        [
            {"date": "2026-02-07", "base": "PLN", "quote": "USD", "rate": 4.04},
            {"date": "2026-02-07", "base": "PLN", "quote": "EUR", "rate": 4.30},
        ]
    )

    write_cache(original, cache_file)
    loaded = read_cache(cache_file)

    assert list(loaded.columns) == ["date", "base", "quote", "rate"]
    assert len(loaded) == 2
    assert loaded.loc[0, "base"] == "PLN"
    assert loaded.loc[0, "quote"] == "USD"
    assert float(loaded.loc[0, "rate"]) == 4.04


def test_read_cache_returns_empty_df_if_missing(tmp_path: Path) -> None:
    cache_file = tmp_path / "does_not_exist.parquet"
    df = read_cache(cache_file)
    assert list(df.columns) == ["date", "base", "quote", "rate"]
    assert df.empty
