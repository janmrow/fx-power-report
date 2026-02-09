from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from jinja2 import Environment, FileSystemLoader, select_autoescape

from fxpower.analytics.ranker import build_rankings, rank_targets
from fxpower.domain.models import Currency, targets_for_base


@dataclass(frozen=True, slots=True)
class ReportPaths:
    reports_dir: Path = Path("reports")

    def report_file(self, base: Currency) -> Path:
        return self.reports_dir / f"fxpower_{base.value}.html"


def _env() -> Environment:
    template_dir = Path(__file__).parent
    return Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html"]),
    )


def _df_to_html_table(df: pd.DataFrame, columns: list[str]) -> str:
    view = df.loc[:, columns].copy()
    # round float-ish columns for readability
    for c in view.columns:
        if pd.api.types.is_float_dtype(view[c]):
            view[c] = view[c].map(lambda x: f"{x:.4f}" if pd.notna(x) else "—")
    return view.to_html(index=False, escape=True)


def _chart_overall_bar(scores: pd.DataFrame) -> str:
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=scores["target"].tolist(),
            y=scores["overall_score"].astype(float).tolist(),
            name="Overall score",
        )
    )
    fig.update_layout(
        height=360,
        margin=dict(l=20, r=20, t=30, b=30),
        title="Overall score by target",
    )
    return fig.to_html(full_html=False, include_plotlyjs="cdn")


def _chart_rates(cache: pd.DataFrame, base: Currency, targets: list[Currency]) -> str:
    fig = go.Figure()
    for t in targets:
        df = cache[(cache["base"] == base.value) & (cache["quote"] == t.value)].copy()
        if df.empty:
            continue
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values(by="date", kind="mergesort")
        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["rate"].astype(float),
                mode="lines",
                name=f"{base.value}/{t.value}",
            )
        )

    fig.update_layout(
        height=420,
        margin=dict(l=20, r=20, t=30, b=30),
        title=f"Rates history ({base.value} per 1 target)",
        legend=dict(orientation="h"),
    )
    return fig.to_html(full_html=False, include_plotlyjs="cdn")


def generate_report_html(
    cache: pd.DataFrame,
    base: Currency,
    paths: ReportPaths | None = None,
) -> Path:
    paths = paths or ReportPaths()
    paths.reports_dir.mkdir(parents=True, exist_ok=True)

    scores = rank_targets(cache, base=base)
    if scores.empty:
        out_file = paths.report_file(base)
        out_file.write_text(f"No data for base={base.value}\n", encoding="utf-8")
        return out_file

    rankings = build_rankings(scores)

    as_of: date = scores["as_of"].max()

    overall = rankings["overall"]
    value = rankings["value"]
    trend = rankings["trend"]
    risk = rankings["risk"]

    kpi_best_overall = overall.iloc[0]["target"]
    kpi_best_value = value.iloc[0]["target"]
    kpi_lowest_risk = risk.iloc[0]["target"]

    explain = []
    for _, row in overall.iterrows():
        explain.append(
            {
                "target": row["target"],
                "overall_score": f"{float(row['overall_score']):.3f}",
                "rate_today": f"{float(row['rate_today']):.4f}",
                "percentile_5y": f"{float(row['percentile_5y']):.3f}",
                "zscore_5y": f"{float(row['zscore_5y']):.3f}",
                "mom_60d": f"{float(row['mom_60d']):.3f}" if pd.notna(row["mom_60d"]) else "—",
                "sma_200_diff": f"{float(row['sma_200_diff']):.3f}"
                if pd.notna(row["sma_200_diff"])
                else "—",
                "vol_90d": f"{float(row['vol_90d']):.3f}" if pd.notna(row["vol_90d"]) else "—",
            }
        )

    overall_table = _df_to_html_table(
        overall, ["target", "overall_score", "value_score", "trend_score", "risk_score"]
    )
    value_table = _df_to_html_table(value, ["target", "value_score", "percentile_5y", "zscore_5y"])
    trend_table = _df_to_html_table(trend, ["target", "trend_score", "mom_60d", "sma_200_diff"])
    risk_table = _df_to_html_table(risk, ["target", "risk_score", "vol_90d"])

    chart_overall_bar = _chart_overall_bar(overall)
    chart_rates = _chart_rates(cache, base=base, targets=list(targets_for_base(base)))

    env = _env()
    tpl = env.get_template("template.html")
    html = tpl.render(
        base=base.value,
        as_of=str(as_of),
        kpi_best_overall=kpi_best_overall,
        kpi_best_value=kpi_best_value,
        kpi_lowest_risk=kpi_lowest_risk,
        overall_table=overall_table,
        value_table=value_table,
        trend_table=trend_table,
        risk_table=risk_table,
        chart_overall_bar=chart_overall_bar,
        chart_rates=chart_rates,
        explain=explain,
    )

    out_file = paths.report_file(base)
    out_file.write_text(html, encoding="utf-8")
    return out_file
