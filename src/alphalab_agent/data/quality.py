"""Deterministic market data quality checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from alphalab_agent.data.schema import NUMERIC_MARKET_COLUMNS, REQUIRED_OHLCV_COLUMNS, normalize_market_data_frame


@dataclass(frozen=True)
class MarketDataQualityIssue:
    """A single market data quality issue."""

    check: str
    severity: str
    message: str
    affected_rows: int = 0
    ratio: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": self.check,
            "severity": self.severity,
            "message": self.message,
            "affected_rows": int(self.affected_rows),
            "ratio": float(self.ratio),
        }


@dataclass(frozen=True)
class MarketDataQualityReport:
    """Structured market data quality report."""

    status: str
    summary: dict[str, Any]
    issues: list[MarketDataQualityIssue]
    column_missing_rates: dict[str, float]
    symbol_coverage: dict[str, int]
    date_coverage: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "summary": self.summary,
            "issues": [issue.to_dict() for issue in self.issues],
            "column_missing_rates": self.column_missing_rates,
            "symbol_coverage": self.symbol_coverage,
            "date_coverage": self.date_coverage,
        }


def run_market_data_quality_checks(
    df: pd.DataFrame,
    *,
    data_source: str = "synthetic",
    return_outlier_threshold: float = 0.50,
    min_symbol_history: int = 40,
    min_dates: int = 40,
) -> MarketDataQualityReport:
    """Run deterministic quality checks over OHLCV-style market data."""

    frame = normalize_market_data_frame(df, data_source=data_source)
    issues: list[MarketDataQualityIssue] = []
    n_rows = int(len(frame))

    missing_required = [column for column in REQUIRED_OHLCV_COLUMNS if column not in frame.columns]
    if missing_required:
        for column in missing_required:
            issues.append(_issue("schema", "error", f"Missing required column: {column}.", n_rows, 1.0))
        return _build_report(frame, issues, data_source=data_source)

    if n_rows == 0:
        issues.append(_issue("schema", "error", "Market data contains no rows.", 0, 1.0))
        return _build_report(frame, issues, data_source=data_source)

    _schema_checks(frame, issues)
    _duplicate_checks(frame, issues)
    _ohlc_checks(frame, issues)
    _volume_checks(frame, issues)
    _return_outlier_checks(frame, issues, return_outlier_threshold)
    _history_checks(frame, issues, min_symbol_history, min_dates)
    _tradeability_checks(frame, issues)
    return _build_report(frame, issues, data_source=data_source)


def _schema_checks(frame: pd.DataFrame, issues: list[MarketDataQualityIssue]) -> None:
    n_rows = max(1, len(frame))
    invalid_dates = int(frame["date"].isna().sum())
    if invalid_dates == len(frame):
        issues.append(_issue("schema_date", "error", "No valid date values were parsed.", invalid_dates, 1.0))
    elif invalid_dates:
        issues.append(_issue("schema_date", "warning", "Some date values could not be parsed.", invalid_dates, invalid_dates / n_rows))

    missing_symbols = int(frame["symbol"].isna().sum() + frame["symbol"].astype(str).str.strip().eq("").sum())
    if missing_symbols == len(frame):
        issues.append(_issue("schema_symbol", "error", "No valid symbol values were found.", missing_symbols, 1.0))
    elif missing_symbols:
        issues.append(
            _issue("schema_symbol", "warning", "Some symbol values are missing.", missing_symbols, missing_symbols / n_rows)
        )

    for column in ["open", "high", "low", "close", "volume"]:
        missing = int(frame[column].isna().sum())
        if missing == len(frame):
            severity = "error"
            message = f"No valid numeric values were found in {column}."
        elif missing:
            severity = "warning"
            message = f"Some {column} values are missing or non-numeric."
        else:
            continue
        issues.append(_issue(f"schema_{column}", severity, message, missing, missing / n_rows))


def _duplicate_checks(frame: pd.DataFrame, issues: list[MarketDataQualityIssue]) -> None:
    duplicate_count = int(frame.duplicated(["date", "symbol"]).sum())
    if not duplicate_count:
        return
    ratio = duplicate_count / max(1, len(frame))
    severity = "error" if ratio > 0.01 else "warning"
    issues.append(_issue("duplicate_date_symbol", severity, "Duplicate date-symbol rows found.", duplicate_count, ratio))


def _ohlc_checks(frame: pd.DataFrame, issues: list[MarketDataQualityIssue]) -> None:
    n_rows = max(1, len(frame))
    checks = [
        ("high_low", frame["high"] < frame["low"], "Rows where high is below low."),
        ("open_range", (frame["open"] > frame["high"]) | (frame["open"] < frame["low"]), "Rows where open is outside high-low range."),
        (
            "close_range",
            (frame["close"] > frame["high"]) | (frame["close"] < frame["low"]),
            "Rows where close is outside high-low range.",
        ),
        ("low_positive", frame["low"] <= 0, "Rows where low is non-positive."),
        ("close_positive", frame["close"] <= 0, "Rows where close is non-positive."),
    ]
    for name, mask, message in checks:
        count = int(mask.fillna(False).sum())
        if not count:
            continue
        ratio = count / n_rows
        severity = "error" if name in {"low_positive", "close_positive"} or ratio > 0.01 else "warning"
        issues.append(_issue(name, severity, message, count, ratio))


def _volume_checks(frame: pd.DataFrame, issues: list[MarketDataQualityIssue]) -> None:
    n_rows = max(1, len(frame))
    negative = int((frame["volume"] < 0).fillna(False).sum())
    if negative:
        issues.append(_issue("negative_volume", "error", "Rows with negative volume found.", negative, negative / n_rows))
    zero_ratio = float((frame["volume"] == 0).fillna(False).mean())
    if zero_ratio > 0.10:
        issues.append(_issue("zero_volume_ratio", "warning", "Zero-volume ratio is elevated.", int(zero_ratio * n_rows), zero_ratio))
    missing_ratio = float(frame["volume"].isna().mean())
    if missing_ratio > 0.10:
        issues.append(
            _issue("volume_missing_rate", "warning", "Volume missing rate is elevated.", int(missing_ratio * n_rows), missing_ratio)
        )


def _return_outlier_checks(frame: pd.DataFrame, issues: list[MarketDataQualityIssue], threshold: float) -> None:
    returns = frame.sort_values(["symbol", "date"], kind="mergesort").groupby("symbol", sort=False)["close"].pct_change()
    outliers = int(returns.abs().gt(threshold).fillna(False).sum())
    if outliers:
        ratio = outliers / max(1, len(frame))
        issues.append(
            _issue(
                "return_outlier",
                "warning",
                f"Daily absolute return exceeded {threshold:.0%}.",
                outliers,
                ratio,
            )
        )


def _history_checks(frame: pd.DataFrame, issues: list[MarketDataQualityIssue], min_symbol_history: int, min_dates: int) -> None:
    valid_dates = frame["date"].dropna()
    n_dates = int(valid_dates.nunique())
    if n_dates == 0:
        issues.append(_issue("history_dates", "error", "No valid trading dates are available.", 0, 1.0))
    elif n_dates < min_dates:
        issues.append(_issue("history_dates", "warning", f"Only {n_dates} valid trading dates are available.", n_dates, 0.0))

    counts = frame.dropna(subset=["symbol"]).groupby("symbol", sort=True)["date"].nunique()
    short_symbols = int((counts < min_symbol_history).sum()) if not counts.empty else 0
    if short_symbols:
        ratio = short_symbols / max(1, len(counts))
        issues.append(
            _issue("history_symbol", "warning", "Some symbols have short trading history.", short_symbols, ratio)
        )


def _tradeability_checks(frame: pd.DataFrame, issues: list[MarketDataQualityIssue]) -> None:
    if "is_tradeable" not in frame:
        return
    tradeable = frame["is_tradeable"].astype("string").str.lower().isin({"1", "true", "yes"})
    unavailable_ratio = float((~tradeable).mean())
    if unavailable_ratio > 0.20:
        issues.append(
            _issue(
                "tradeability",
                "warning",
                "Unavailable or non-tradeable ratio is elevated.",
                int(unavailable_ratio * len(frame)),
                unavailable_ratio,
            )
        )


def _build_report(
    frame: pd.DataFrame,
    issues: list[MarketDataQualityIssue],
    *,
    data_source: str,
) -> MarketDataQualityReport:
    status = "PASS"
    if any(issue.severity == "error" for issue in issues):
        status = "FAIL"
    elif any(issue.severity == "warning" for issue in issues):
        status = "WARN"

    column_missing_rates = {
        column: float(frame[column].isna().mean())
        for column in frame.columns
        if column in {*REQUIRED_OHLCV_COLUMNS, *NUMERIC_MARKET_COLUMNS, "industry", "is_tradeable"}
    }
    if "symbol" in frame.columns:
        symbol_counts = frame.dropna(subset=["symbol"]).groupby("symbol", sort=True).size()
    else:
        symbol_counts = pd.Series(dtype=int)
    if "date" in frame.columns and "symbol" in frame.columns:
        date_counts = frame.dropna(subset=["date"]).groupby("date", sort=True)["symbol"].nunique()
    else:
        date_counts = pd.Series(dtype=int)
    summary = {
        "data_source": data_source,
        "rows": int(len(frame)),
        "dates": int(frame["date"].nunique()) if "date" in frame.columns else 0,
        "symbols": int(frame["symbol"].nunique()) if "symbol" in frame.columns else 0,
        "issues": int(len(issues)),
        "error_issues": int(sum(issue.severity == "error" for issue in issues)),
        "warning_issues": int(sum(issue.severity == "warning" for issue in issues)),
    }
    return MarketDataQualityReport(
        status=status,
        summary=summary,
        issues=issues,
        column_missing_rates=column_missing_rates,
        symbol_coverage={str(symbol): int(count) for symbol, count in symbol_counts.items()},
        date_coverage={str(date.date()): int(count) for date, count in date_counts.items()},
    )


def _issue(check: str, severity: str, message: str, affected_rows: int, ratio: float) -> MarketDataQualityIssue:
    return MarketDataQualityIssue(
        check=check,
        severity=severity,
        message=message,
        affected_rows=affected_rows,
        ratio=ratio,
    )
