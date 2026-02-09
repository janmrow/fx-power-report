from __future__ import annotations

import pandas as pd

from fxpower.analytics.cross_rates import generate_cross_rates_from_eur_series


def test_generate_cross_rates_from_eur_series_produces_12_pairs_per_day() -> None:
    eur_series = pd.DataFrame(
        [
            {"date": "2026-02-01", "quote": "USD", "rate": 1.10},  # 1 EUR = 1.10 USD
            {"date": "2026-02-01", "quote": "PLN", "rate": 4.40},  # 1 EUR = 4.40 PLN
            {"date": "2026-02-01", "quote": "GBP", "rate": 0.88},  # 1 EUR = 0.88 GBP
            {"date": "2026-02-02", "quote": "USD", "rate": 1.20},
            {"date": "2026-02-02", "quote": "PLN", "rate": 4.50},
            {"date": "2026-02-02", "quote": "GBP", "rate": 0.90},
        ]
    )

    out = generate_cross_rates_from_eur_series(eur_series)

    # 4 currencies => 4*3 = 12 directed pairs per day
    assert len(out[out["date"].astype(str) == "2026-02-01"]) == 12
    assert len(out[out["date"].astype(str) == "2026-02-02"]) == 12

    assert list(out.columns) == ["date", "base", "quote", "rate"]


def test_cross_rate_math_pln_per_usd_and_usd_per_pln() -> None:
    eur_series = pd.DataFrame(
        [
            {"date": "2026-02-01", "quote": "USD", "rate": 1.10},
            {"date": "2026-02-01", "quote": "PLN", "rate": 4.40},
            {"date": "2026-02-01", "quote": "GBP", "rate": 0.88},
        ]
    )

    out = generate_cross_rates_from_eur_series(eur_series)

    # PLN per 1 USD = (PLN per EUR) / (USD per EUR) = 4.40 / 1.10 = 4.0
    pln_usd = out[(out["base"] == "PLN") & (out["quote"] == "USD")].iloc[0]
    assert abs(float(pln_usd["rate"]) - 4.0) < 1e-12

    # USD per 1 PLN = (USD per EUR) / (PLN per EUR) = 1.10 / 4.40 = 0.25
    usd_pln = out[(out["base"] == "USD") & (out["quote"] == "PLN")].iloc[0]
    assert abs(float(usd_pln["rate"]) - 0.25) < 1e-12

    # GBP per 1 EUR should equal the raw EUR series (0.88)
    gbp_eur = out[(out["base"] == "GBP") & (out["quote"] == "EUR")].iloc[0]
    assert abs(float(gbp_eur["rate"]) - 0.88) < 1e-12
