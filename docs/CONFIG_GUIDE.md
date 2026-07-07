# Configuration Guide

## Configuration Philosophy

AlphaLab Agent keeps configuration explicit and deterministic:

- Synthetic data is the default.
- Real-data adapters are disabled by default.
- Optional dependencies must lazy import and provide graceful fallback.
- Core research outputs must be reproducible from a fixed seed.
- Config files must not contain API keys, secrets, tokens, passwords, broker credentials, or live-trading settings.

The current `ResearchConfig` controls the deterministic research pipeline. CLI-only inputs such as `--csv-path` are documented separately and do not require changing the config loader.

## Minimal Synthetic Config

Use `examples/config_synthetic_minimal.json` as a small deterministic synthetic run:

```powershell
py -m alphalab_agent.cli --demo --config examples/config_synthetic_minimal.json
```

Important fields:

- `data_source`: `synthetic`
- `seed`: fixed integer seed
- `n_days`, `n_symbols`, `top_k`: small but valid research dimensions
- `output_dir`: an `artifacts/` subdirectory
- `generate_manifest`: `true`

## CSV Config

Use `examples/config_csv_sample.json` as a documented CSV sample workflow. The JSON keeps a valid `research_config` block and a separate `cli_args.csv_path` entry because the current CLI accepts CSV paths as command-line arguments:

```powershell
py -m alphalab_agent.cli --demo --data-source csv --csv-path examples/sample_ohlcv.csv
```

The sample CSV is synthetic-style data, not real stock data. Required CSV columns are:

- `date`
- `symbol`
- `open`
- `high`
- `low`
- `close`
- `volume`

## Supervised Model Config

The supervised factor model is research-only and disabled by default.

Relevant fields:

- `enable_supervised_model`: `false` by default
- `model_type`: `ridge` or `linear`
- `model_label_col`: usually `forward_return`
- `model_factor_cols`: `null` to use the default factor set

This model is for train-only research diagnostics and out-of-sample evaluation. It is not an investment recommendation and not a production prediction service.

## Output Config

Relevant output fields:

- `output_dir`
- `report_name`
- `html_report_name`
- `generate_html`
- `generate_charts`
- `generate_manifest`

Generated outputs should stay under `artifacts/` and should not be committed.

## Safety-Related Config

Safety boundaries:

- Do not store real API keys in config files.
- Do not add broker credentials.
- Do not enable live trading.
- Do not make yfinance or any real-data adapter the default.
- Do not add hidden network access to the default demo or test path.
