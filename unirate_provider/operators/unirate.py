"""Operators for UniRateAPI."""

from __future__ import annotations

from typing import Any, Sequence

from airflow.models import BaseOperator

from unirate_provider.hooks.unirate import UniRateHook


class UniRateGetRateOperator(BaseOperator):
    """Fetch a single exchange rate and push it to XCom.

    If ``date`` is set (``YYYY-MM-DD``), the historical endpoint is called
    (requires a UniRate Pro plan); otherwise the latest rate is returned.

    :param from_currency: ISO 4217 source currency (e.g. ``"USD"``).
    :param to_currency: ISO 4217 target currency (e.g. ``"EUR"``).
    :param date: Optional historical date in ``YYYY-MM-DD`` format.
    :param unirate_conn_id: Airflow connection id (default: ``unirate_default``).
    :param timeout: Per-request timeout in seconds (default: 30).
    """

    template_fields: Sequence[str] = ("from_currency", "to_currency", "date")
    ui_color = "#0d6efd"

    def __init__(
        self,
        *,
        from_currency: str,
        to_currency: str,
        date: str | None = None,
        unirate_conn_id: str = UniRateHook.default_conn_name,
        timeout: int = 30,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.date = date
        self.unirate_conn_id = unirate_conn_id
        self.timeout = timeout

    def execute(self, context: Any) -> float:
        hook = UniRateHook(unirate_conn_id=self.unirate_conn_id, timeout=self.timeout)
        if self.date:
            rate = hook.get_historical_rate(
                date=self.date,
                from_currency=self.from_currency,
                to_currency=self.to_currency,
            )
            self.log.info(
                "UniRate historical rate %s→%s on %s = %s",
                self.from_currency, self.to_currency, self.date, rate,
            )
        else:
            rate = hook.get_rate(
                from_currency=self.from_currency, to_currency=self.to_currency
            )
            self.log.info(
                "UniRate latest rate %s→%s = %s",
                self.from_currency, self.to_currency, rate,
            )
        return rate


class UniRateConvertOperator(BaseOperator):
    """Convert ``amount`` from one currency to another and push to XCom.

    :param from_currency: ISO 4217 source currency.
    :param to_currency: ISO 4217 target currency.
    :param amount: Amount to convert. May be a string for templating.
    :param date: Optional historical date in ``YYYY-MM-DD`` format (Pro plan).
    :param unirate_conn_id: Airflow connection id (default: ``unirate_default``).
    :param timeout: Per-request timeout in seconds (default: 30).
    """

    template_fields: Sequence[str] = ("from_currency", "to_currency", "amount", "date")
    ui_color = "#198754"

    def __init__(
        self,
        *,
        from_currency: str,
        to_currency: str,
        amount: float | str = 1.0,
        date: str | None = None,
        unirate_conn_id: str = UniRateHook.default_conn_name,
        timeout: int = 30,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.amount = amount
        self.date = date
        self.unirate_conn_id = unirate_conn_id
        self.timeout = timeout

    def execute(self, context: Any) -> float:
        amount = float(self.amount)
        hook = UniRateHook(unirate_conn_id=self.unirate_conn_id, timeout=self.timeout)
        if self.date:
            result = hook.get_historical_rate(
                date=self.date,
                from_currency=self.from_currency,
                to_currency=self.to_currency,
                amount=amount,
            )
            self.log.info(
                "UniRate historical convert %s %s→%s on %s = %s",
                amount, self.from_currency, self.to_currency, self.date, result,
            )
        else:
            result = hook.convert(
                from_currency=self.from_currency,
                to_currency=self.to_currency,
                amount=amount,
            )
            self.log.info(
                "UniRate convert %s %s→%s = %s",
                amount, self.from_currency, self.to_currency, result,
            )
        return result
