"""Optional market data adapters.

These adapters are disabled by default. The synthetic data path remains the
default for tests, demos, and reports.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_OHLCV_COLUMNS = ["date", "symbol", "open", "high", "low", "close", "volume"]


def load_csv_ohlcv(path: str | Path, symbol: str | None = None) -> pd.DataFrame:
    """Load OHLCV data from a local CSV file."""

    raw = pd.read_csv(path)
    frame = _normalize_ohlcv_columns(raw)
    if "symbol" not in frame.columns:
        if not symbol:
            raise ValueError("CSV data must include a symbol column or receive an explicit symbol.")
        frame["symbol"] = symbol
    return _select_required_columns(frame)


def load_yfinance_ohlcv(
    ticker: str,
    start: str,
    end: str,
    interval: str = "1d",
) -> pd.DataFrame:
    """Load OHLCV data through yfinance when explicitly requested."""

    try:
        import yfinance as yf
    except ImportError as exc:
        raise ImportError(
            "yfinance is optional and not installed. Install it with "
            '`python -m pip install -e ".[data]"` before using --data-source yfinance.'
        ) from exc

    data = yf.download(ticker, start=start, end=end, interval=interval, auto_adjust=True, progress=False)
    if data.empty:
        raise ValueError(f"yfinance returned no rows for {ticker} from {start} to {end}.")
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    data = data.reset_index()
    frame = _normalize_ohlcv_columns(data)
    frame["symbol"] = ticker
    return _select_required_columns(frame)


def load_market_data(
    source: str,
    *,
    csv_path: str | Path | None = None,
    symbol: str | None = None,
    ticker: str | None = None,
    start: str | None = None,
    end: str | None = None,
    interval: str = "1d",
) -> pd.DataFrame | None:
    """Load optional market data for explicit non-synthetic sources."""

    if source == "synthetic":
        return None
    if source == "csv":
        if csv_path is None:
            raise ValueError("--csv-path is required when --data-source csv is used.")
        return load_csv_ohlcv(csv_path, symbol=symbol)
    if source == "yfinance":
        if not ticker or not start or not end:
            raise ValueError("--ticker, --start, and --end are required when --data-source yfinance is used.")
        return load_yfinance_ohlcv(ticker=ticker, start=start, end=end, interval=interval)
    raise ValueError(f"Unknown data source: {source}")


def _normalize_ohlcv_columns(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    normalized.columns = [str(column).strip().lower().replace(" ", "_") for column in normalized.columns]
    rename_map = {
        "datetime": "date",
        "timestamp": "date",
        "adj_close": "close",
        "adjclose": "close",
    }
    normalized = normalized.rename(columns=rename_map)
    return normalized


def _select_required_columns(frame: pd.DataFrame) -> pd.DataFrame:
    missing = set(REQUIRED_OHLCV_COLUMNS).difference(frame.columns)
    if missing:
        raise ValueError(f"Market data is missing required OHLCV columns: {sorted(missing)}")
    result = frame[REQUIRED_OHLCV_COLUMNS].copy()
    result["date"] = pd.to_datetime(result["date"])
    return result.sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)
