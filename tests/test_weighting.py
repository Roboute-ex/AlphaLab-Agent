import pandas as pd

from alphalab_agent.analysis.weighting import learn_factor_weights


def test_train_only_weighting_modes_are_normalized_and_stable():
    train = pd.DataFrame(
        {
            "date": [pd.Timestamp("2020-01-01")] * 5 + [pd.Timestamp("2020-01-02")] * 5,
            "factor_a": [1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
            "factor_b": [5, 4, 3, 2, 1, 5, 4, 3, 2, 1],
            "forward_return_1d": [1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
        }
    )

    equal = learn_factor_weights(train, "forward_return_1d", ["factor_a", "factor_b"], mode="equal_weight")
    config = learn_factor_weights(
        train,
        "forward_return_1d",
        ["factor_a", "factor_b"],
        mode="config_weight",
        config_weights={"factor_a": 2.0, "factor_b": 1.0},
    )
    ic = learn_factor_weights(train, "forward_return_1d", ["factor_a", "factor_b"], mode="ic_weight_train_only")

    assert equal == {"factor_a": 0.5, "factor_b": 0.5}
    assert round(sum(abs(value) for value in config.values()), 6) == 1.0
    assert round(sum(abs(value) for value in ic.values()), 6) == 1.0
    assert ic["factor_a"] > 0
    assert ic["factor_b"] < 0


def test_train_only_weighting_falls_back_for_small_samples():
    train = pd.DataFrame(
        {
            "date": [pd.Timestamp("2020-01-01")],
            "factor_a": [1.0],
            "factor_b": [1.0],
            "forward_return_1d": [0.01],
        }
    )
    weights = learn_factor_weights(train, "forward_return_1d", ["factor_a", "factor_b"], mode="ic_weight_train_only")
    assert weights == {"factor_a": 0.5, "factor_b": 0.5}
