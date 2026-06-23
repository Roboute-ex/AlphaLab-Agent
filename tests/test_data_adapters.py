import sys
from pathlib import Path

import pandas as pd

from alphalab_agent.data.adapters import load_csv_ohlcv, load_market_data, load_yfinance_ohlcv


def test_csv_adapter_normalizes_columns_and_adds_symbol():
    path = Path("artifacts") / "test_data_adapters_input.csv"
    try:
        pd.DataFrame(
            {
                "Date": ["2021-01-04", "2021-01-05"],
                "Open": [10.0, 10.5],
                "High": [11.0, 11.5],
                "Low": [9.5, 10.2],
                "Close": [10.4, 11.1],
                "Volume": [1000, 1100],
                " Market Cap ": ["1000000", "bad"],
            }
        ).to_csv(path, index=False)

        frame = load_csv_ohlcv(path, symbol="AAA")

        assert list(frame.columns) == ["date", "symbol", "open", "high", "low", "close", "volume", "market_cap", "data_source"]
        assert frame.shape == (2, 9)
        assert frame["symbol"].tolist() == ["AAA", "AAA"]
        assert frame["data_source"].tolist() == ["csv", "csv"]
        assert frame["market_cap"].isna().sum() == 1
        assert pd.api.types.is_datetime64_any_dtype(frame["date"])
        assert (frame["high"] >= frame[["open", "close"]].max(axis=1)).all()
        assert (frame["low"] <= frame[["open", "close"]].min(axis=1)).all()
    finally:
        path.unlink(missing_ok=True)


def test_csv_adapter_requires_symbol_when_missing():
    path = Path("artifacts") / "test_data_adapters_missing_symbol.csv"
    try:
        pd.DataFrame(
            {
                "date": ["2021-01-04"],
                "open": [10.0],
                "high": [11.0],
                "low": [9.5],
                "close": [10.4],
                "volume": [1000],
            }
        ).to_csv(path, index=False)

        try:
            load_csv_ohlcv(path)
        except ValueError as exc:
            assert "symbol column" in str(exc)
        else:
            raise AssertionError("Expected ValueError for CSV data without symbol.")
    finally:
        path.unlink(missing_ok=True)


def test_market_data_synthetic_source_returns_none():
    assert load_market_data("synthetic") is None


def test_yfinance_adapter_has_graceful_missing_dependency_message():
    sentinel = sys.modules.get("yfinance")
    had_module = "yfinance" in sys.modules
    sys.modules["yfinance"] = None
    try:
        try:
            load_yfinance_ohlcv("AAPL", "2020-01-01", "2020-02-01")
        except ImportError as exc:
            message = str(exc)
            assert "yfinance is optional" in message
            assert ".[data]" in message
        else:
            raise AssertionError("Expected ImportError when yfinance is unavailable.")
    finally:
        if had_module:
            sys.modules["yfinance"] = sentinel
        else:
            sys.modules.pop("yfinance", None)
