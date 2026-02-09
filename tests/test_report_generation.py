from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from fxpower.domain.models import Currency
from fxpower.reporting.report import ReportPaths, generate_report_html


def _mk_series(start: date, n: int, base: str, quote: str, rate: float) -> pd.DataFrame:
    rows = []
    for i in range(n):
        rows.append(
            {
                "date": (start + timedelta(days=i)).isoformat(),
                "base": base,
                "quote": quote,
                "rate": rate,
            }
        )
    return pd.DataFrame(rows)


def test_generate_report_html_writes_file(tmp_path: Path) -> None:
    start = date(2026, 1, 1)
    n = 260

    cache = pd.concat(
        [
            _mk_series(start, n, "PLN", "USD", 4.2),
            _mk_series(start, n, "PLN", "EUR", 4.3),
            _mk_series(start, n, "PLN", "GBP", 5.1),
        ],
        ignore_index=True,
    )

    paths = ReportPaths(reports_dir=tmp_path / "reports")
    out = generate_report_html(cache, base=Currency.PLN, paths=paths)

    assert out.exists()
    html = out.read_text(encoding="utf-8")
    assert "fxpower report" in html
    assert "Overall ranking" in html
    assert "Explain" in html
    assert "Charts" in html
