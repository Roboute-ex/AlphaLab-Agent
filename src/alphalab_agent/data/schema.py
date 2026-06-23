"""Market data schema helpers."""

from __future__ import annotations

import pandas as pd

REQUIRED_OHLCV_COLUMNS = ["date", "symbol", "open", "high", "low", "close", "volume"]
OPTIONAL_MARKET_COLUMNS = [
    "amount",
    "turnover",
    "industry",
    "market_cap",
    "is_tradeable",
    "adjust_factor",
]
NUMERIC_MARKET_COLUMNS = [
    "open",
    "high",
    "low",
    "close",
    "volume",
    "amount",
    "turnover",
    "market_cap",
    "adjust_factor",
]


def normalize_market_data_frame(frame: pd.DataFrame, data_source: str, symbol: str | None = None) -> pd.DataFrame:
    """Normalize market data columns and dtypes without dropping optional fields."""

    normalized = frame.copy()
    normalized.columns = [_normalize_column_name(column) for column in normalized.columns]
    normalized = normalized.rename(
        columns={
            "datetime": "date",
            "timestamp": "date",
            "time": "date",
            "adj_close": "close",
            "adjclose": "close",
            "adjcloseprice": "close",
        }
    )
    if "symbol" not in normalized.columns and symbol:
        normalized["symbol"] = symbol
    if "date" in normalized.columns:
        normalized["date"] = pd.to_datetime(normalized["date"], errors="coerce")
    if "symbol" in normalized.columns:
        normalized["symbol"] = normalized["symbol"].astype("string")
    for column in NUMERIC_MARKET_COLUMNS:
        if column in normalized.columns:
            normalized[column] = pd.to_numeric(normalized[column], errors="coerce")
    normalized["data_source"] = data_source
    return normalized


def select_market_data_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Return required, optional, and provenance columns in a stable order."""

    columns = [
        *REQUIRED_OHLCV_COLUMNS,
        *(column for column in OPTIONAL_MARKET_COLUMNS if column in frame.columns),
        "data_source",
    ]
    return frame[columns].copy()


def _normalize_column_name(column: object) -> str:
    return str(column).strip().lower().replace(" ", "_").replace("-", "_")
