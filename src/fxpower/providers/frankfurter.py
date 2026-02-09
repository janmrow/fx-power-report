from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

import pandas as pd
import requests


@dataclass(frozen=True, slots=True)
class FrankfurterConfig:
    base_url: str = "https://api.frankfurter.dev/v1"
    timeout_s: float = 10.0


class FrankfurterError(RuntimeError):
    pass


def _date_str(d: date) -> str:
    return d.isoformat()


def fetch_eur_timeseries(
    start: date,
    end: date,
    symbols: Iterable[str],
    cfg: FrankfurterConfig | None = None,
) -> pd.DataFrame:
    """Fetch EUR-based time series for selected symbols.

    Returns DataFrame with columns: date, quote, rate
    Where rate = QUOTE per 1 EUR (e.g. USD per EUR).
    """
    cfg = cfg or FrankfurterConfig()
    symbols_list = sorted({s.strip().upper() for s in symbols if s.strip()})
    if not symbols_list:
        raise ValueError("symbols must not be empty")

    url = f"{cfg.base_url}/{_date_str(start)}..{_date_str(end)}"
    params = {"base": "EUR", "symbols": ",".join(symbols_list)}

    try:
        resp = requests.get(url, params=params, timeout=cfg.timeout_s)
    except requests.RequestException as exc:
        raise FrankfurterError(f"Network error calling Frankfurter: {exc}") from exc

    if resp.status_code != 200:
        raise FrankfurterError(f"Frankfurter returned HTTP {resp.status_code}: {resp.text}")

    payload = resp.json()
    if payload.get("base") != "EUR":
        raise FrankfurterError(f"Unexpected base in response: {payload.get('base')}")

    rates = payload.get("rates")
    if not isinstance(rates, dict):
        raise FrankfurterError("Invalid response payload: missing/invalid 'rates'")

    rows: list[dict[str, object]] = []
    for day_str, day_rates in rates.items():
        if not isinstance(day_rates, dict):
            continue
        for quote, rate in day_rates.items():
            rows.append({"date": day_str, "quote": quote, "rate": rate})

    df = pd.DataFrame(rows)
    if df.empty:
        # still return stable schema
        return pd.DataFrame(columns=["date", "quote", "rate"])

    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["quote"] = df["quote"].astype("string")
    df["rate"] = pd.to_numeric(df["rate"], errors="raise").astype("float64")

    df = df.sort_values(by=["date", "quote"], kind="mergesort").reset_index(drop=True)
    return df


def fetch_timeseries(
    start: date,
    end: date,
    base: str,
    symbols: Iterable[str],
    cfg: FrankfurterConfig | None = None,
) -> pd.DataFrame:
    """Fetch time series for a given base currency.

    Returns DataFrame with columns: date, base, quote, rate
    Where rate = QUOTE per 1 BASE (as provided by API).
    """
    cfg = cfg or FrankfurterConfig()
    base_norm = base.strip().upper()
    symbols_list = sorted({s.strip().upper() for s in symbols if s.strip()})
    if not symbols_list:
        raise ValueError("symbols must not be empty")

    url = f"{cfg.base_url}/{_date_str(start)}..{_date_str(end)}"
    params = {"base": base_norm, "symbols": ",".join(symbols_list)}

    try:
        resp = requests.get(url, params=params, timeout=cfg.timeout_s)
    except requests.RequestException as exc:
        raise FrankfurterError(f"Network error calling Frankfurter: {exc}") from exc

    if resp.status_code != 200:
        raise FrankfurterError(f"Frankfurter returned HTTP {resp.status_code}: {resp.text}")

    payload = resp.json()
    if payload.get("base") != base_norm:
        raise FrankfurterError(f"Unexpected base in response: {payload.get('base')}")

    rates = payload.get("rates")
    if not isinstance(rates, dict):
        raise FrankfurterError("Invalid response payload: missing/invalid 'rates'")

    rows: list[dict[str, object]] = []
    for day_str, day_rates in rates.items():
        if not isinstance(day_rates, dict):
            continue
        for quote, rate in day_rates.items():
            rows.append({"date": day_str, "base": base_norm, "quote": quote, "rate": rate})

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["date", "base", "quote", "rate"])

    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["base"] = df["base"].astype("string")
    df["quote"] = df["quote"].astype("string")
    df["rate"] = pd.to_numeric(df["rate"], errors="raise").astype("float64")

    df = df.sort_values(by=["date", "base", "quote"], kind="mergesort").reset_index(drop=True)
    return df
