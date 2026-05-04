"""Example DAG demonstrating the UniRate provider.

Set up an Airflow connection of type **UniRate** with id ``unirate_default``
and paste your UniRateAPI key into the ``API Key`` (password) field. Then
unpause this DAG to fetch USD→EUR daily.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG

from unirate_provider.operators.unirate import (
    UniRateConvertOperator,
    UniRateGetRateOperator,
)
from unirate_provider.sensors.unirate import UniRateRateChangeSensor

with DAG(
    dag_id="unirate_example",
    description="Pull USD→EUR rates and watch for big moves.",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args={"retries": 1, "retry_delay": timedelta(minutes=5)},
    tags=["unirate", "currency", "example"],
) as dag:

    latest = UniRateGetRateOperator(
        task_id="latest_usd_eur",
        from_currency="USD",
        to_currency="EUR",
    )

    convert_100 = UniRateConvertOperator(
        task_id="convert_100_usd_to_eur",
        from_currency="USD",
        to_currency="EUR",
        amount=100,
    )

    # Trigger downstream work when EUR moves >1% from a fixed reference.
    big_move = UniRateRateChangeSensor(
        task_id="watch_big_eur_move",
        from_currency="USD",
        to_currency="EUR",
        threshold_pct=0.01,
        baseline_rate=0.92,
        poke_interval=3600,
        timeout=60 * 60 * 24,  # give up after a day
    )

    latest >> convert_100 >> big_move
