from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from fxpower.domain.models import SUPPORTED_CURRENCIES, Currency


@dataclass(frozen=True, slots=True)
class EurSeriesContract:
    """Contract for EUR-based series.

    Input df must have columns:
      - date (date-like)
      - quote (currency code, e.g. USD)
      - rate  (QUOTE per 1 EUR)

    Example: quote=USD rate=1.10 means 1 EUR = 1.10 USD.
    """

    date_col: str = "date"
    quote_col: str = "quote"
    rate_col: str = "rate"


def generate_cross_rates_from_eur_series(
    eur_series: pd.DataFrame,
    contract: EurSeriesContract | None = None,
) -> pd.DataFrame:
    """Generate cross rates for all supported currency pairs.

    Output columns: date, base, quote, rate
    Where rate = BASE per 1 QUOTE (e.g. PLN per USD).
    """
    contract = contract or EurSeriesContract()

    if eur_series.empty:
        return pd.DataFrame(columns=["date", "base", "quote", "rate"])

    df = eur_series.copy()
    df[contract.date_col] = pd.to_datetime(df[contract.date_col]).dt.date
    df[contract.quote_col] = df[contract.quote_col].astype("string").str.upper()
    df[contract.rate_col] = pd.to_numeric(df[contract.rate_col], errors="raise").astype("float64")

    # Pivot to wide: date -> currency -> (currency per 1 EUR)
    wide = df.pivot(index=contract.date_col, columns=contract.quote_col, values=contract.rate_col)

    # Ensure EUR column exists with value 1.0 (1 EUR = 1 EUR)
    wide[Currency.EUR.value] = 1.0

    # Ensure we only use supported currencies and all required columns exist
    for c in SUPPORTED_CURRENCIES:
        if c.value not in wide.columns:
            raise ValueError(f"Missing EUR-based rate for currency: {c.value}")

    wide = wide[[c.value for c in SUPPORTED_CURRENCIES]].sort_index()

    rows: list[dict[str, object]] = []
    currencies = list(SUPPORTED_CURRENCIES)

    for day, series in wide.iterrows():
        # series[currency] = currency per 1 EUR
        for base in currencies:
            for quote in currencies:
                if base == quote:
                    continue
                base_per_eur = float(series[base.value])
                quote_per_eur = float(series[quote.value])
                base_per_quote = base_per_eur / quote_per_eur
                rows.append(
                    {
                        "date": day,
                        "base": base.value,
                        "quote": quote.value,
                        "rate": base_per_quote,
                    }
                )

    out = pd.DataFrame(rows)
    out["date"] = pd.to_datetime(out["date"]).dt.date
    out["base"] = out["base"].astype("string")
    out["quote"] = out["quote"].astype("string")
    out["rate"] = out["rate"].astype("float64")

    out = out.sort_values(by=["date", "base", "quote"], kind="mergesort").reset_index(drop=True)
    return out
