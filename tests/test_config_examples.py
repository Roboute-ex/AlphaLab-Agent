import json
from dataclasses import fields
from pathlib import Path

from alphalab_agent.config import ResearchConfig


SENSITIVE_TERMS = {"api_key", "secret", "token", "password", "broker", "live_trading"}


def _load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _assert_no_sensitive_terms(payload: dict):
    text = json.dumps(payload, sort_keys=True).lower()
    for term in SENSITIVE_TERMS:
        assert term not in text


def test_synthetic_config_example_is_valid_and_safe():
    payload = _load_json("examples/config_synthetic_minimal.json")
    _assert_no_sensitive_terms(payload)

    config = ResearchConfig(**payload)

    assert config.data_source == "synthetic"
    assert str(config.output_dir).startswith("artifacts")
    assert config.generate_manifest is True


def test_csv_config_example_references_sample_csv_and_is_safe():
    payload = _load_json("examples/config_csv_sample.json")
    _assert_no_sensitive_terms(payload)

    research_config = payload["research_config"]
    cli_args = payload["cli_args"]
    known_fields = {field.name for field in fields(ResearchConfig)}

    assert set(research_config).issubset(known_fields)
    config = ResearchConfig(**research_config)

    assert config.data_source == "csv"
    assert str(config.output_dir).startswith("artifacts")
    assert cli_args["csv_path"] == "examples/sample_ohlcv.csv"
    assert Path(cli_args["csv_path"]).exists()
