"""Optional market data adapters.

These adapters are disabled by default. The synthetic data path remains the
default for tests, demos, and reports.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from alphalab_agent.data.schema import (
    REQUIRED_OHLCV_COLUMNS,
    normalize_market_data_frame,
    select_market_data_columns,
)


def load_csv_ohlcv(path: str | Path, symbol: str | None = None) -> pd.DataFrame:
    """Load OHLCV data from a local CSV file."""

    raw = pd.read_csv(path)
    frame = normalize_market_data_frame(raw, data_source="csv", symbol=symbol)
    if "symbol" not in frame.columns:
        if not symbol:
            raise ValueError("CSV data must include a symbol column or receive an explicit symbol.")
        frame["symbol"] = symbol
    return _select_required_columns(frame)


def load_yfinance_ohlcv(
    ticker: str | list[str],
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

    tickers = _parse_tickers(ticker)
    frames: list[pd.DataFrame] = []
    for single_ticker in tickers:
        data = yf.download(single_ticker, start=start, end=end, interval=interval, auto_adjust=True, progress=False)
        if data.empty:
            raise ValueError(f"yfinance returned no rows for {single_ticker} from {start} to {end}.")
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        data = data.reset_index()
        frame = normalize_market_data_frame(data, data_source="yfinance", symbol=single_ticker)
        frame["symbol"] = single_ticker
        frames.append(_select_required_columns(frame))
    return pd.concat(frames, ignore_index=True).sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)


def load_market_data(
    source: str,
    *,
    csv_path: str | Path | None = None,
    symbol: str | None = None,
    ticker: str | None = None,
    tickers: str | list[str] | None = None,
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
        requested = tickers or ticker
        if not requested or not start or not end:
            raise ValueError(
                "--tickers, --start-date, and --end-date are required when --data-source yfinance is used."
            )
        return load_yfinance_ohlcv(ticker=requested, start=start, end=end, interval=interval)
    raise ValueError(f"Unknown data source: {source}")


def _select_required_columns(frame: pd.DataFrame) -> pd.DataFrame:
    missing = set(REQUIRED_OHLCV_COLUMNS).difference(frame.columns)
    if missing:
        raise ValueError(f"Market data is missing required OHLCV columns: {sorted(missing)}")
    result = select_market_data_columns(frame)
    result["date"] = pd.to_datetime(result["date"], errors="coerce")
    result["symbol"] = result["symbol"].astype("string")
    return result.sort_values(["date", "symbol"], kind="mergesort").reset_index(drop=True)


def _parse_tickers(ticker: str | list[str]) -> list[str]:
    if isinstance(ticker, str):
        tickers = [part.strip() for part in ticker.split(",")]
    else:
        tickers = [str(part).strip() for part in ticker]
    tickers = [part for part in tickers if part]
    if not tickers:
        raise ValueError("At least one ticker is required for yfinance data.")
    return tickers
