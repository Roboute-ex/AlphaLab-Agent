import pandas as pd

from alphalab_agent.analysis.ml_model import (
    evaluate_supervised_factor_model,
    predict_supervised_factor_model,
    train_supervised_factor_model,
)


def _ml_frame() -> pd.DataFrame:
    rows = []
    for idx, date in enumerate(pd.bdate_range("2024-01-01", periods=30)):
        for symbol_idx, symbol in enumerate(["AAA", "BBB", "CCC", "DDD"]):
            factor_a = idx * 0.01 + symbol_idx * 0.1
            factor_b = symbol_idx * 0.05
            label = 0.02 * factor_a - 0.01 * factor_b
            rows.append(
                {
                    "date": date,
                    "symbol": symbol,
                    "factor_a": factor_a,
                    "factor_b": factor_b,
                    "forward_return_5d": label,
                }
            )
    return pd.DataFrame(rows)


def test_supervised_factor_model_train_predict_evaluate():
    frame = _ml_frame()
    train = frame.loc[frame["date"] < frame["date"].drop_duplicates().iloc[20]]
    test = frame.loc[frame["date"] >= frame["date"].drop_duplicates().iloc[20]].copy()

    model = train_supervised_factor_model(train, ["factor_a", "factor_b"], "forward_return_5d")
    test["prediction_score"] = predict_supervised_factor_model(model, test)
    metrics = evaluate_supervised_factor_model(test, "prediction_score", "forward_return_5d", quantiles=3)

    assert model.status == "PASS"
    assert model.n_train == len(train)
    assert set(model.coefficients) == {"factor_a", "factor_b"}
    assert len(test["prediction_score"]) == len(test)
    assert metrics["n_test"] == len(test)
    assert metrics["mse"] >= 0.0
    assert metrics["prediction_ic"] > 0.9


def test_supervised_factor_model_predictions_do_not_use_test_labels():
    frame = _ml_frame()
    train = frame.iloc[:80]
    test = frame.iloc[80:].copy()
    model = train_supervised_factor_model(train, ["factor_a", "factor_b"], "forward_return_5d")

    baseline = predict_supervised_factor_model(model, test)
    mutated = test.copy()
    mutated["forward_return_5d"] = mutated["forward_return_5d"] * -100.0
    changed_labels_prediction = predict_supervised_factor_model(model, mutated)

    assert baseline.equals(changed_labels_prediction)


def test_supervised_factor_model_small_sample_returns_warning():
    frame = _ml_frame().head(2)

    model = train_supervised_factor_model(frame, ["factor_a", "factor_b"], "forward_return_5d")

    assert model.status == "WARN"
    assert all(value == 0.0 for value in model.coefficients.values())
