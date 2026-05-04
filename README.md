# airflow-provider-unirate

[![PyPI](https://img.shields.io/pypi/v/airflow-provider-unirate.svg)](https://pypi.org/project/airflow-provider-unirate/)
[![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-2.10%20%7C%202.11%20%7C%203.x-017CEE?logo=apacheairflow)](https://airflow.apache.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Apache Airflow provider for **[UniRateAPI](https://unirateapi.com)** — real-time
and historical currency exchange rates. Hook, two operators, and one sensor for
plugging FX rates into your DAGs.

## Install

```bash
pip install airflow-provider-unirate
```

Requires `apache-airflow >= 2.10` (works on 2.10, 2.11, and 3.x).

## Connection setup

Create an **Airflow connection** of type **UniRate**:

| Field    | Value                                |
|----------|--------------------------------------|
| Conn Id  | `unirate_default` (or your own)      |
| Conn Type| `UniRate`                            |
| API Key  | your UniRate key (`password` field)  |

Or via env var:

```bash
export AIRFLOW_CONN_UNIRATE_DEFAULT='unirate://:YOUR_API_KEY@'
```

Get a free key at <https://unirateapi.com>.

## Components

### Hook — `UniRateHook`

```python
from unirate_provider.hooks.unirate import UniRateHook

hook = UniRateHook(unirate_conn_id="unirate_default")
rate = hook.get_rate("USD", "EUR")              # latest spot rate
amount = hook.convert("USD", "EUR", 100)        # convert 100 USD → EUR
hist = hook.get_historical_rate("2024-01-15", "USD", "EUR")  # Pro plan
codes = hook.list_currencies()                  # ['USD', 'EUR', ...]
```

### Operators

```python
from unirate_provider.operators.unirate import (
    UniRateGetRateOperator,
    UniRateConvertOperator,
)

latest = UniRateGetRateOperator(
    task_id="latest_eur",
    from_currency="USD",
    to_currency="EUR",
)

# Historical via the same operator (Pro plan; pass YYYY-MM-DD).
historical = UniRateGetRateOperator(
    task_id="hist_eur",
    from_currency="USD",
    to_currency="EUR",
    date="{{ ds }}",
)

convert = UniRateConvertOperator(
    task_id="convert_invoice",
    from_currency="USD",
    to_currency="EUR",
    amount="{{ ti.xcom_pull(task_ids='upstream', key='amount_usd') }}",
)
```

Both operators push their result (a `float`) to XCom. `from_currency`,
`to_currency`, `amount`, and `date` are all templated.

### Sensor — `UniRateRateChangeSensor`

Trigger downstream work when an FX rate moves beyond a threshold.

```python
from unirate_provider.sensors.unirate import UniRateRateChangeSensor

# Wake up downstream tasks when EUR moves >1% from a fixed reference.
big_move = UniRateRateChangeSensor(
    task_id="watch_eur",
    from_currency="USD",
    to_currency="EUR",
    threshold_pct=0.01,        # 1%
    baseline_rate=0.92,        # if omitted, the first poke sets the baseline
    direction="any",           # 'any' | 'up' | 'down'
    poke_interval=3600,        # check hourly
    mode="reschedule",         # default; releases the worker slot between pokes
    timeout=60 * 60 * 24,      # give up after 24h
)
```

The crossing rate is pushed to XCom on success.

## Example DAG

A complete example lives at `unirate_provider/example_dags/example_unirate.py`.

## Testing

```bash
pip install -e ".[test]"
pytest
```

## Status

`v0.1.0` — initial release. Hook + 2 operators + 1 sensor. 30 unit tests.

## License

MIT. UniRate client (`unirate-api`) is also MIT.

## Links

- UniRate API docs: <https://unirateapi.com/docs>
- Airflow custom-providers howto: <https://airflow.apache.org/docs/apache-airflow-providers/howto/create-custom-providers.html>
- Issues: <https://github.com/UniRate-API/airflow-provider-unirate/issues>
