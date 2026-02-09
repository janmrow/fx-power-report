from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from fxpower.analytics.metrics import (
    MetricDefaults,
    momentum,
    percentile_rank,
    sma,
    volatility,
    zscore,
)
from fxpower.domain.models import Currency, targets_for_base


@dataclass(frozen=True, slots=True)
class Scores:
    target: Currency
    as_of: date
    rate_today: float

    # value vs history
    percentile_5y: float
    zscore_5y: float
    value_score: float

    # trend
    mom_60d: float
    sma_200_diff: float
    trend_score: float

    # risk
    vol_90d: float
    risk_score: float

    # final
    overall_score: float


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def _score_value(pctl: float, z: float) -> float:
    # Lower percentile => cheaper => higher score
    if pd.isna(pctl) or pd.isna(z):
        return float("nan")
    cheapness = 1.0 - pctl  # 0..1
    z_component = _clamp((-z) / 3.0, 0.0, 1.0)  # z=-3 => ~1
    return 0.6 * cheapness + 0.4 * z_component


def _score_trend(mom: float, sma_diff: float) -> float:
    # TrendScore: prefer not strongly negative momentum and not far below SMA.
    # Map to [0,1] with gentle clipping.
    if pd.isna(mom) or pd.isna(sma_diff):
        return float("nan")

    # momentum: -20%..+20% -> 0..1
    mom_component = _clamp((mom + 0.20) / 0.40, 0.0, 1.0)

    # sma_diff: -10%..+10% -> 0..1
    sma_component = _clamp((sma_diff + 0.10) / 0.20, 0.0, 1.0)

    return 0.6 * mom_component + 0.4 * sma_component


def _score_risk(vol: float) -> float:
    # RiskScore: higher volatility => higher risk score.
    # Map typical FX vols (~0.05..0.25) into 0..1.
    if pd.isna(vol):
        return float("nan")
    return _clamp((vol - 0.05) / (0.25 - 0.05), 0.0, 1.0)


def _score_overall(value_score: float, trend_score: float, risk_score: float) -> float:
    if pd.isna(value_score) or pd.isna(trend_score) or pd.isna(risk_score):
        return float("nan")
    # risk: lower is better => use (1 - risk_score)
    return 0.55 * value_score + 0.25 * trend_score + 0.20 * (1.0 - risk_score)


def _series_for_pair(cache: pd.DataFrame, base: Currency, quote: Currency) -> pd.Series:
    df = cache[(cache["base"] == base.value) & (cache["quote"] == quote.value)].copy()
    if df.empty:
        return pd.Series(dtype="float64")
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df = df.sort_values(by="date", kind="mergesort")
    s = pd.Series(df["rate"].astype("float64").to_numpy(), index=df["date"].to_list())
    s.name = f"{base.value}/{quote.value}"
    return s


def rank_targets(
    cache: pd.DataFrame,
    base: Currency,
    defaults: MetricDefaults | None = None,
) -> pd.DataFrame:
    """Return per-target metrics and scores as a dataframe."""
    defaults = defaults or MetricDefaults()
    targets = targets_for_base(base)

    rows: list[dict[str, object]] = []
    for t in targets:
        s = _series_for_pair(cache, base=base, quote=t)
        if s.empty:
            continue

        as_of = s.index[-1]
        today_rate = float(s.iloc[-1])

        pctl = percentile_rank(s, today_rate)
        z = zscore(s, today_rate)
        value_score = _score_value(pctl, z)

        mom = momentum(s, window=defaults.mom_window)

        sma_series = sma(s, window=defaults.sma_window)
        sma_last = (
            float(sma_series.dropna().iloc[-1]) if not sma_series.dropna().empty else float("nan")
        )
        sma_diff = (
            (today_rate / sma_last - 1.0)
            if (not pd.isna(sma_last) and sma_last != 0.0)
            else float("nan")
        )

        trend_score = _score_trend(mom, sma_diff)

        vol = volatility(
            s, window=defaults.vol_window, annualization_factor=defaults.annualization_factor
        )
        risk_score = _score_risk(vol)

        overall = _score_overall(value_score, trend_score, risk_score)

        rows.append(
            {
                "target": t.value,
                "as_of": as_of,
                "rate_today": today_rate,
                "percentile_5y": pctl,
                "zscore_5y": z,
                "value_score": value_score,
                "mom_60d": mom,
                "sma_200_diff": sma_diff,
                "trend_score": trend_score,
                "vol_90d": vol,
                "risk_score": risk_score,
                "overall_score": overall,
            }
        )

    out = pd.DataFrame(rows)
    if out.empty:
        return out

    # Stable column order
    cols = [
        "target",
        "as_of",
        "rate_today",
        "percentile_5y",
        "zscore_5y",
        "value_score",
        "mom_60d",
        "sma_200_diff",
        "trend_score",
        "vol_90d",
        "risk_score",
        "overall_score",
    ]
    out = out.loc[:, cols]
    return out


def build_rankings(scores_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Return named ranking tables: value, trend, risk, overall."""
    if scores_df.empty:
        return {"value": scores_df, "trend": scores_df, "risk": scores_df, "overall": scores_df}

    value = scores_df.sort_values(
        by=["value_score", "target"], ascending=[False, True], kind="mergesort"
    )
    trend = scores_df.sort_values(
        by=["trend_score", "target"], ascending=[False, True], kind="mergesort"
    )
    risk = scores_df.sort_values(
        by=["risk_score", "target"], ascending=[True, True], kind="mergesort"
    )
    overall = scores_df.sort_values(
        by=["overall_score", "target"], ascending=[False, True], kind="mergesort"
    )

    return {
        "value": value.reset_index(drop=True),
        "trend": trend.reset_index(drop=True),
        "risk": risk.reset_index(drop=True),
        "overall": overall.reset_index(drop=True),
    }
