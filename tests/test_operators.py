"""Tests for the UniRate operators."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from unirate_provider.operators.unirate import (
    UniRateConvertOperator,
    UniRateGetRateOperator,
)


@patch("unirate_provider.operators.unirate.UniRateHook")
def test_get_rate_operator_latest(mock_hook_cls):
    mock_hook_cls.return_value.get_rate.return_value = 0.92
    op = UniRateGetRateOperator(
        task_id="latest", from_currency="USD", to_currency="EUR"
    )
    assert op.execute({}) == 0.92
    mock_hook_cls.return_value.get_rate.assert_called_once_with(
        from_currency="USD", to_currency="EUR"
    )
    mock_hook_cls.return_value.get_historical_rate.assert_not_called()


@patch("unirate_provider.operators.unirate.UniRateHook")
def test_get_rate_operator_historical(mock_hook_cls):
    mock_hook_cls.return_value.get_historical_rate.return_value = 0.85
    op = UniRateGetRateOperator(
        task_id="hist",
        from_currency="USD",
        to_currency="EUR",
        date="2024-01-15",
    )
    assert op.execute({}) == 0.85
    mock_hook_cls.return_value.get_historical_rate.assert_called_once_with(
        date="2024-01-15", from_currency="USD", to_currency="EUR"
    )
    mock_hook_cls.return_value.get_rate.assert_not_called()


@patch("unirate_provider.operators.unirate.UniRateHook")
def test_convert_operator_latest(mock_hook_cls):
    mock_hook_cls.return_value.convert.return_value = 92.0
    op = UniRateConvertOperator(
        task_id="conv",
        from_currency="USD",
        to_currency="EUR",
        amount=100,
    )
    assert op.execute({}) == 92.0
    mock_hook_cls.return_value.convert.assert_called_once_with(
        from_currency="USD", to_currency="EUR", amount=100.0
    )


@patch("unirate_provider.operators.unirate.UniRateHook")
def test_convert_operator_historical(mock_hook_cls):
    mock_hook_cls.return_value.get_historical_rate.return_value = 85.0
    op = UniRateConvertOperator(
        task_id="conv-hist",
        from_currency="USD",
        to_currency="EUR",
        amount="100",  # string is allowed (templating)
        date="2024-01-15",
    )
    assert op.execute({}) == 85.0
    mock_hook_cls.return_value.get_historical_rate.assert_called_once_with(
        date="2024-01-15",
        from_currency="USD",
        to_currency="EUR",
        amount=100.0,
    )


def test_template_fields_declared():
    assert "from_currency" in UniRateGetRateOperator.template_fields
    assert "to_currency" in UniRateGetRateOperator.template_fields
    assert "date" in UniRateGetRateOperator.template_fields
    assert "amount" in UniRateConvertOperator.template_fields
