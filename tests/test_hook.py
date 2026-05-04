"""Tests for ``UniRateHook``."""

from __future__ import annotations

import pytest

from airflow.exceptions import AirflowException

from unirate_provider.hooks.unirate import UniRateHook
from unirate.exceptions import AuthenticationError


def test_hook_class_attrs():
    assert UniRateHook.conn_type == "unirate"
    assert UniRateHook.conn_name_attr == "unirate_conn_id"
    assert UniRateHook.default_conn_name == "unirate_default"
    assert UniRateHook.hook_name == "UniRate"


def test_get_ui_field_behaviour_has_required_keys():
    behaviour = UniRateHook.get_ui_field_behaviour()
    assert "hidden_fields" in behaviour
    assert "relabeling" in behaviour
    assert "placeholders" in behaviour
    # The standard `password` slot is repurposed for the API key, so it must
    # NOT be hidden, and it must be relabeled.
    assert "password" not in behaviour["hidden_fields"]
    assert behaviour["relabeling"]["password"] == "API Key"


def test_get_conn_memoizes(fake_connection, mock_unirate_client):
    hook = UniRateHook()
    a = hook.get_conn()
    b = hook.get_conn()
    assert a is b is mock_unirate_client


def test_missing_api_key_raises(monkeypatch):
    from airflow.models import Connection
    from airflow.hooks import base as base_hook

    conn = Connection(conn_id="unirate_default", conn_type="unirate", password=None)
    monkeypatch.setattr(base_hook.BaseHook, "get_connection", lambda *a, **k: conn)
    hook = UniRateHook()
    with pytest.raises(AirflowException, match="missing an API key"):
        hook.get_conn()


def test_get_rate_delegates(fake_connection, mock_unirate_client):
    mock_unirate_client.get_rate.return_value = 0.92
    hook = UniRateHook()
    assert hook.get_rate("USD", "EUR") == 0.92
    mock_unirate_client.get_rate.assert_called_once_with(
        from_currency="USD", to_currency="EUR"
    )


def test_convert_delegates(fake_connection, mock_unirate_client):
    mock_unirate_client.convert.return_value = 92.0
    hook = UniRateHook()
    assert hook.convert("USD", "EUR", 100) == 92.0
    mock_unirate_client.convert.assert_called_once_with(
        from_currency="USD", to_currency="EUR", amount=100
    )


def test_historical_delegates(fake_connection, mock_unirate_client):
    mock_unirate_client.get_historical_rate.return_value = 0.85
    hook = UniRateHook()
    assert hook.get_historical_rate("2024-01-15", "USD", "EUR") == 0.85


def test_list_currencies_delegates(fake_connection, mock_unirate_client):
    mock_unirate_client.get_supported_currencies.return_value = ["USD", "EUR", "GBP"]
    hook = UniRateHook()
    assert hook.list_currencies() == ["USD", "EUR", "GBP"]


def test_unirate_error_remapped_to_airflow(fake_connection, mock_unirate_client):
    mock_unirate_client.get_rate.side_effect = AuthenticationError("bad key")
    hook = UniRateHook()
    with pytest.raises(AirflowException, match="UniRate get_rate failed"):
        hook.get_rate("USD", "EUR")


def test_test_connection_success(fake_connection, mock_unirate_client):
    mock_unirate_client.get_supported_currencies.return_value = ["USD"]
    ok, msg = UniRateHook().test_connection()
    assert ok is True
    assert "Connected" in msg


def test_test_connection_failure(fake_connection, mock_unirate_client):
    mock_unirate_client.get_supported_currencies.side_effect = AuthenticationError("nope")
    ok, msg = UniRateHook().test_connection()
    assert ok is False
    assert "nope" in msg
