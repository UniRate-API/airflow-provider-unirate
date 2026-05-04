# Changelog

All notable changes to `airflow-provider-unirate` will be documented in this file.

## [0.1.0] — 2026-05-04

Initial release.

- `UniRateHook` (`conn_type="unirate"`) wrapping the official `unirate-api` Python client. Custom UI behaviour relabels the connection's password field as **API Key** and hides unused fields.
- `UniRateGetRateOperator` — fetches latest or historical exchange rate; XCom-pushes the float.
- `UniRateConvertOperator` — converts an amount; XCom-pushes the float.
- `UniRateRateChangeSensor` — pokes until an FX pair moves beyond a `threshold_pct` or `abs_threshold` (with optional direction filter); defaults to `mode="reschedule"`.
- 30 unit tests, mock-only.
- CI matrix on Apache Airflow 2.10, 2.11, and 3.0 across Python 3.9–3.12.
