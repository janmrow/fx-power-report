from __future__ import annotations

from datetime import date

import responses

from fxpower.analytics.cross_rates import generate_cross_rates_from_eur_series
from fxpower.providers.frankfurter import FrankfurterConfig, fetch_eur_timeseries, fetch_timeseries


@responses.activate
def test_cross_rate_matches_direct_api_for_pln_per_usd() -> None:
    cfg = FrankfurterConfig(base_url="https://api.frankfurter.dev/v1", timeout_s=1.0)
    d = date(2026, 2, 1)

    # 1) EUR-based series: need USD, PLN, GBP (EUR implicit)
    eur_url = f"{cfg.base_url}/{d.isoformat()}..{d.isoformat()}"
    responses.add(
        responses.GET,
        eur_url,
        match=[responses.matchers.query_param_matcher({"base": "EUR", "symbols": "GBP,PLN,USD"})],
        json={
            "base": "EUR",
            "start_date": d.isoformat(),
            "end_date": d.isoformat(),
            "rates": {
                d.isoformat(): {"USD": 1.10, "PLN": 4.40, "GBP": 0.88},
            },
        },
        status=200,
    )

    eur_df = fetch_eur_timeseries(start=d, end=d, symbols=["USD", "PLN", "GBP"], cfg=cfg)
    cross = generate_cross_rates_from_eur_series(eur_df)

    # Cross PLN per USD = 4.40 / 1.10 = 4.0
    pln_per_usd_cross = float(
        cross[(cross["base"] == "PLN") & (cross["quote"] == "USD")].iloc[0]["rate"]
    )

    # 2) Direct API: base=USD, quote=PLN => rate = PLN per 1 USD
    responses.add(
        responses.GET,
        eur_url,
        match=[responses.matchers.query_param_matcher({"base": "USD", "symbols": "PLN"})],
        json={
            "base": "USD",
            "start_date": d.isoformat(),
            "end_date": d.isoformat(),
            "rates": {
                d.isoformat(): {"PLN": 4.0},
            },
        },
        status=200,
    )

    direct_df = fetch_timeseries(start=d, end=d, base="USD", symbols=["PLN"], cfg=cfg)
    pln_per_usd_direct = float(direct_df.iloc[0]["rate"])

    assert abs(pln_per_usd_cross - pln_per_usd_direct) < 1e-12
