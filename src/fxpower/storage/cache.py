from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS: tuple[str, ...] = ("date", "base", "quote", "rate")


@dataclass(frozen=True, slots=True)
class CachePaths:
    cache_file: Path

    @staticmethod
    def default() -> CachePaths:
        return CachePaths(cache_file=Path("data") / "cache.parquet")


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _validate_cache_df(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Cache dataframe missing columns: {missing}. Required: {REQUIRED_COLUMNS}"
        )

    # Keep only required columns, in stable order
    out = df.loc[:, list(REQUIRED_COLUMNS)].copy()

    # Normalize date to date-only (no time component)
    out["date"] = pd.to_datetime(out["date"]).dt.date

    # Normalize types for stability
    out["base"] = out["base"].astype("string")
    out["quote"] = out["quote"].astype("string")
    out["rate"] = pd.to_numeric(out["rate"], errors="raise").astype("float64")

    return out


def read_cache(path: Path) -> pd.DataFrame:
    """Read cache parquet into a normalized dataframe.

    Returns empty dataframe with required columns if the file doesn't exist.
    """
    if not path.exists():
        return pd.DataFrame(columns=list(REQUIRED_COLUMNS))

    df = pd.read_parquet(path)
    return _validate_cache_df(df)


def write_cache(df: pd.DataFrame, path: Path) -> None:
    """Write dataframe to cache parquet after validation/normalization."""
    _ensure_parent_dir(path)
    normalized = _validate_cache_df(df)
    normalized.to_parquet(path, index=False)


def merge_cache(existing: pd.DataFrame, incoming: pd.DataFrame) -> pd.DataFrame:
    """Merge incoming rows into existing cache.

    - Deduplicate by (date, base, quote)
    - Incoming wins on conflicts
    - Sort by date, base, quote (stable)
    """
    left = (
        _validate_cache_df(existing)
        if not existing.empty
        else pd.DataFrame(columns=list(REQUIRED_COLUMNS))
    )
    right = (
        _validate_cache_df(incoming)
        if not incoming.empty
        else pd.DataFrame(columns=list(REQUIRED_COLUMNS))
    )

    if left.empty and right.empty:
        return pd.DataFrame(columns=list(REQUIRED_COLUMNS))

    combined = pd.concat([left, right], ignore_index=True)

    # Incoming wins: keep last occurrence of each key
    combined = combined.drop_duplicates(subset=["date", "base", "quote"], keep="last")

    combined = combined.sort_values(by=["date", "base", "quote"], kind="mergesort").reset_index(
        drop=True
    )
    return combined
