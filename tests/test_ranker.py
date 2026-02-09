from __future__ import annotations

from datetime import date, timedelta

import pandas as pd

from fxpower.analytics.ranker import build_rankings, rank_targets
from fxpower.domain.models import Currency


def _mk_series(start: date, n: int, base: str, quote: str, rates: list[float]) -> pd.DataFrame:
    assert len(rates) == n
    rows = []
    for i in range(n):
        rows.append(
            {
                "date": (start + timedelta(days=i)).isoformat(),
                "base": base,
                "quote": quote,
                "rate": rates[i],
            }
        )
    return pd.DataFrame(rows)


def test_rank_targets_produces_scores_for_three_targets() -> None:
    start = date(2026, 1, 1)
    n = 260  # enough for SMA200, mom60, vol90

    # Base PLN: create three targets with different "cheapness" today.
    # USD: today low vs history => should rank high in value
    usd_rates = [4.5] * (n - 1) + [3.8]
    # EUR: stable
    eur_rates = [4.3] * n
    # GBP: today high vs history => should rank low in value
    gbp_rates = [5.0] * (n - 1) + [5.5]

    cache = pd.concat(
        [
            _mk_series(start, n, "PLN", "USD", usd_rates),
            _mk_series(start, n, "PLN", "EUR", eur_rates),
            _mk_series(start, n, "PLN", "GBP", gbp_rates),
        ],
        ignore_index=True,
    )

    scores = rank_targets(cache, base=Currency.PLN)
    assert set(scores["target"].tolist()) == {"USD", "EUR", "GBP"}
    assert len(scores) == 3

    rankings = build_rankings(scores)
    value_rank = rankings["value"]["target"].tolist()
    assert value_rank[0] == "USD"
    assert value_rank[-1] == "GBP"

    overall_rank = rankings["overall"]["target"].tolist()
    assert "USD" in overall_rank  # sanity
