from __future__ import annotations

from datetime import date
from pathlib import Path

import typer

from fxpower.app.fetch import FetchPolicy, update_cache_from_eur_source
from fxpower.domain.models import Currency, parse_currency
from fxpower.providers.frankfurter import FrankfurterConfig, fetch_eur_timeseries
from fxpower.reporting.report import generate_report_html
from fxpower.storage.cache import CachePaths, read_cache

app = typer.Typer(
    add_completion=False,
    help="fxpower: FX opportunity ranking report (not a forecast).",
)


def _fetch_eur_series_fn(cfg: FrankfurterConfig):
    def _fn(start: date, end: date):
        return fetch_eur_timeseries(
            start=start,
            end=end,
            symbols=["USD", "PLN", "GBP"],
            cfg=cfg,
        )

    return _fn


@app.command()
def fetch(
    cache_path: Path | None = typer.Option(
        default=None,
        help="Path to cache parquet file.",
    ),
    lookback_days: int = typer.Option(
        default=365 * 5,
        help="Approximate lookback window in days.",
    ),
) -> None:
    """Fetch missing FX data and update local cache."""
    paths = CachePaths.default()
    path = cache_path or paths.cache_file

    cfg = FrankfurterConfig()
    policy = FetchPolicy(lookback_days=lookback_days)

    updated = update_cache_from_eur_source(
        cache_path=path,
        fetch_eur_series=_fetch_eur_series_fn(cfg),
        today=date.today(),
        policy=policy,
    )

    typer.echo(f"Cache updated: {path}")
    typer.echo(f"Rows: {len(updated)}")


@app.command()
def report(
    base: str = typer.Option(
        ...,
        "--base",
        "-b",
        help="Base currency (PLN, USD, EUR, GBP).",
    ),
    cache_path: Path | None = typer.Option(
        default=None,
        help="Path to cache parquet file.",
    ),
) -> None:
    """Generate a single-page HTML report for the chosen base currency."""
    base_cur: Currency = parse_currency(base)

    paths = CachePaths.default()
    path = cache_path or paths.cache_file

    cache_df = read_cache(path)
    out_file = generate_report_html(cache_df, base=base_cur)

    typer.echo(f"Report generated: {out_file}")
