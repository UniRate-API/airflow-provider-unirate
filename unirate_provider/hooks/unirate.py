"""Hook for the UniRateAPI currency-exchange service."""

from __future__ import annotations

from typing import Any

from airflow.exceptions import AirflowException
from airflow.hooks.base import BaseHook
from unirate import UnirateClient
from unirate.exceptions import UnirateError


class UniRateHook(BaseHook):
    """Interact with UniRateAPI.

    The connection's ``password`` field stores the API key. All other standard
    connection fields are unused.

    :param unirate_conn_id: Airflow connection id (default: ``unirate_default``).
    :param timeout: Per-request timeout in seconds (default: 30).
    """

    conn_name_attr = "unirate_conn_id"
    default_conn_name = "unirate_default"
    conn_type = "unirate"
    hook_name = "UniRate"

    def __init__(
        self,
        unirate_conn_id: str = default_conn_name,
        timeout: int = 30,
    ) -> None:
        super().__init__()
        self.unirate_conn_id = unirate_conn_id
        self.timeout = timeout
        self._client: UnirateClient | None = None

    @staticmethod
    def get_ui_field_behaviour() -> dict[str, Any]:
        return {
            "hidden_fields": ["host", "port", "login", "schema", "extra"],
            "relabeling": {"password": "API Key"},
            "placeholders": {"password": "your UniRateAPI key"},
        }

    def get_conn(self) -> UnirateClient:
        """Return a memoized ``UnirateClient`` configured from the Airflow connection."""
        if self._client is not None:
            return self._client
        conn = self.get_connection(self.unirate_conn_id)
        api_key = conn.password
        if not api_key:
            raise AirflowException(
                f"UniRate connection '{self.unirate_conn_id}' is missing an API key "
                "(set it in the connection's password field)."
            )
        self._client = UnirateClient(api_key=api_key, timeout=self.timeout)
        return self._client

    def get_rate(self, from_currency: str, to_currency: str) -> float:
        """Return the latest exchange rate for ``from_currency``→``to_currency``."""
        try:
            return self.get_conn().get_rate(
                from_currency=from_currency, to_currency=to_currency
            )
        except UnirateError as exc:
            raise AirflowException(f"UniRate get_rate failed: {exc}") from exc

    def convert(
        self,
        from_currency: str,
        to_currency: str,
        amount: float = 1.0,
    ) -> float:
        try:
            return self.get_conn().convert(
                from_currency=from_currency,
                to_currency=to_currency,
                amount=amount,
            )
        except UnirateError as exc:
            raise AirflowException(f"UniRate convert failed: {exc}") from exc

    def get_historical_rate(
        self,
        date: str,
        from_currency: str,
        to_currency: str,
        amount: float = 1.0,
    ) -> float:
        try:
            return self.get_conn().get_historical_rate(
                date=date,
                from_currency=from_currency,
                to_currency=to_currency,
                amount=amount,
            )
        except UnirateError as exc:
            raise AirflowException(f"UniRate get_historical_rate failed: {exc}") from exc

    def list_currencies(self) -> list[str]:
        try:
            return self.get_conn().get_supported_currencies()
        except UnirateError as exc:
            raise AirflowException(f"UniRate list_currencies failed: {exc}") from exc

    def test_connection(self) -> tuple[bool, str]:
        """Airflow UI 'Test' button hook."""
        try:
            self.get_conn().get_supported_currencies()
            return True, "Connected to UniRateAPI."
        except Exception as exc:  # noqa: BLE001 — surfaced verbatim to UI
            return False, str(exc)
