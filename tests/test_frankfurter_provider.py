from __future__ import annotations

from datetime import date

import responses

from fxpower.providers.frankfurter import FrankfurterConfig, fetch_eur_timeseries


@responses.activate
def test_fetch_eur_timeseries_parses_rates() -> None:
    cfg = FrankfurterConfig(base_url="https://api.frankfurter.dev/v1", timeout_s=1.0)

    start = date(2026, 2, 1)
    end = date(2026, 2, 2)
    url = f"{cfg.base_url}/{start.isoformat()}..{end.isoformat()}"

    responses.add(
        responses.GET,
        url,
        json={
            "base": "EUR",
            "start_date": "2026-02-01",
            "end_date": "2026-02-02",
            "rates": {
                "2026-02-01": {"USD": 1.1, "PLN": 4.4},
                "2026-02-02": {"USD": 1.2, "PLN": 4.5},
            },
        },
        status=200,
    )

    df = fetch_eur_timeseries(start=start, end=end, symbols=["USD", "PLN"], cfg=cfg)

    assert list(df.columns) == ["date", "quote", "rate"]
    assert len(df) == 4

    # spot-check one row
    row = df[(df["quote"] == "USD")].iloc[0]
    assert float(row["rate"]) == 1.1
