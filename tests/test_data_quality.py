import pandas as pd

from alphalab_agent.data.quality import run_market_data_quality_checks


def test_market_data_quality_passes_clean_sample():
    frame = pd.DataFrame(
        {
            "date": pd.bdate_range("2024-01-01", periods=45).repeat(3),
            "symbol": [symbol for _ in range(45) for symbol in ["AAA", "BBB", "CCC"]],
            "open": [10.0 + idx * 0.01 for idx in range(135)],
            "high": [10.2 + idx * 0.01 for idx in range(135)],
            "low": [9.9 + idx * 0.01 for idx in range(135)],
            "close": [10.1 + idx * 0.01 for idx in range(135)],
            "volume": [1000 + idx for idx in range(135)],
        }
    )

    report = run_market_data_quality_checks(frame)

    assert report.status == "PASS"
    assert report.summary["rows"] == 135
    assert report.summary["symbols"] == 3
    assert report.column_missing_rates["close"] == 0.0


def test_market_data_quality_flags_missing_required_columns_as_fail():
    report = run_market_data_quality_checks(pd.DataFrame({"date": ["2024-01-01"], "close": [10.0]}))

    assert report.status == "FAIL"
    assert any(issue.check == "schema" and issue.severity == "error" for issue in report.issues)


def test_market_data_quality_flags_duplicates_and_invalid_ohlc():
    frame = pd.DataFrame(
        {
            "date": ["2024-01-01", "2024-01-01", "2024-01-02"],
            "symbol": ["AAA", "AAA", "AAA"],
            "open": [10.0, 10.0, 12.0],
            "high": [9.0, 9.0, 11.0],
            "low": [10.0, 10.0, 10.5],
            "close": [10.0, 10.0, -1.0],
            "volume": [1000, 1000, -5],
        }
    )

    report = run_market_data_quality_checks(frame, min_dates=1, min_symbol_history=1)
    checks = {issue.check: issue.severity for issue in report.issues}

    assert report.status == "FAIL"
    assert checks["duplicate_date_symbol"] == "error"
    assert checks["high_low"] == "error"
    assert checks["close_positive"] == "error"
    assert checks["negative_volume"] == "error"
