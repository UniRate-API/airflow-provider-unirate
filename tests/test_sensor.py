"""Tests for ``UniRateRateChangeSensor``."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from airflow.exceptions import AirflowException
from airflow.sensors.base import PokeReturnValue

from unirate_provider.sensors.unirate import UniRateRateChangeSensor


def _make_sensor(**overrides):
    defaults = dict(
        task_id="t",
        from_currency="USD",
        to_currency="EUR",
        threshold_pct=0.01,
    )
    defaults.update(overrides)
    return UniRateRateChangeSensor(**defaults)


def test_rejects_no_threshold():
    with pytest.raises(AirflowException, match="Exactly one"):
        UniRateRateChangeSensor(task_id="t", from_currency="USD", to_currency="EUR")


def test_rejects_both_thresholds():
    with pytest.raises(AirflowException, match="Exactly one"):
        UniRateRateChangeSensor(
            task_id="t",
            from_currency="USD",
            to_currency="EUR",
            threshold_pct=0.01,
            abs_threshold=0.01,
        )


def test_rejects_bad_direction():
    with pytest.raises(AirflowException, match="direction"):
        UniRateRateChangeSensor(
            task_id="t",
            from_currency="USD",
            to_currency="EUR",
            threshold_pct=0.01,
            direction="sideways",
        )


def test_rejects_non_positive_threshold():
    with pytest.raises(AirflowException):
        UniRateRateChangeSensor(
            task_id="t", from_currency="USD", to_currency="EUR", threshold_pct=0
        )


@patch("unirate_provider.sensors.unirate.UniRateHook")
def test_first_poke_records_baseline_returns_false(mock_hook_cls):
    mock_hook_cls.return_value.get_rate.return_value = 0.92
    sensor = _make_sensor()
    assert sensor.poke({}) is False
    assert sensor._baseline == 0.92


@patch("unirate_provider.sensors.unirate.UniRateHook")
def test_pct_threshold_triggers(mock_hook_cls):
    sensor = _make_sensor(threshold_pct=0.01, baseline_rate=1.0)
    mock_hook_cls.return_value.get_rate.return_value = 1.02  # +2%
    result = sensor.poke({})
    assert isinstance(result, PokeReturnValue)
    assert result.is_done is True
    assert result.xcom_value == 1.02


@patch("unirate_provider.sensors.unirate.UniRateHook")
def test_pct_threshold_not_triggered(mock_hook_cls):
    sensor = _make_sensor(threshold_pct=0.05, baseline_rate=1.0)
    mock_hook_cls.return_value.get_rate.return_value = 1.02  # +2% < 5%
    assert sensor.poke({}) is False


@patch("unirate_provider.sensors.unirate.UniRateHook")
def test_abs_threshold_triggers(mock_hook_cls):
    sensor = _make_sensor(threshold_pct=None, abs_threshold=0.01, baseline_rate=1.0)
    mock_hook_cls.return_value.get_rate.return_value = 1.02
    result = sensor.poke({})
    assert isinstance(result, PokeReturnValue)
    assert result.xcom_value == 1.02


@patch("unirate_provider.sensors.unirate.UniRateHook")
def test_direction_filter_blocks_wrong_way(mock_hook_cls):
    sensor = _make_sensor(threshold_pct=0.01, baseline_rate=1.0, direction="up")
    mock_hook_cls.return_value.get_rate.return_value = 0.95  # -5%
    assert sensor.poke({}) is False


@patch("unirate_provider.sensors.unirate.UniRateHook")
def test_direction_filter_allows_right_way(mock_hook_cls):
    sensor = _make_sensor(threshold_pct=0.01, baseline_rate=1.0, direction="down")
    mock_hook_cls.return_value.get_rate.return_value = 0.95
    result = sensor.poke({})
    assert isinstance(result, PokeReturnValue)
    assert result.xcom_value == 0.95


def test_sensor_defaults_to_reschedule_mode():
    sensor = _make_sensor()
    assert sensor.mode == "reschedule"
    assert sensor.poke_interval == 3600.0
