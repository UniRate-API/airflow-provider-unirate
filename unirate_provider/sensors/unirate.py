"""Sensors for UniRateAPI."""

from __future__ import annotations

from typing import Any, Sequence

from airflow.exceptions import AirflowException
from airflow.sensors.base import BaseSensorOperator, PokeReturnValue

from unirate_provider.hooks.unirate import UniRateHook


class UniRateRateChangeSensor(BaseSensorOperator):
    """Wait until an FX rate moves beyond a threshold.

    On the first poke the sensor records the current rate as the baseline (or
    uses ``baseline_rate`` if provided). On every subsequent poke it compares
    the latest rate to the baseline and succeeds when either:

    - ``threshold_pct`` is set and ``abs(latest - baseline) / baseline >= threshold_pct``, or
    - ``abs_threshold`` is set and ``abs(latest - baseline) >= abs_threshold``.

    The latest rate (the one that crossed the threshold) is pushed to XCom on
    success.

    :param from_currency: ISO 4217 source currency (e.g. ``"USD"``).
    :param to_currency: ISO 4217 target currency (e.g. ``"EUR"``).
    :param threshold_pct: Trigger when the rate moves by at least this fraction
        of the baseline (e.g. ``0.01`` = 1%). Mutually exclusive with
        ``abs_threshold``.
    :param abs_threshold: Trigger when the rate moves by at least this absolute
        amount. Mutually exclusive with ``threshold_pct``.
    :param baseline_rate: Optional fixed baseline. If omitted, the first poke's
        rate is used as the baseline.
    :param direction: ``"any"`` (default), ``"up"``, or ``"down"`` — restricts
        the trigger direction relative to the baseline.
    :param unirate_conn_id: Airflow connection id (default: ``unirate_default``).
    :param timeout_sec: Per-request HTTP timeout (default: 30). Distinct from
        the inherited Airflow ``timeout`` (the sensor's overall deadline).
    """

    template_fields: Sequence[str] = (
        "from_currency",
        "to_currency",
        "baseline_rate",
    )
    ui_color = "#fd7e14"

    def __init__(
        self,
        *,
        from_currency: str,
        to_currency: str,
        threshold_pct: float | None = None,
        abs_threshold: float | None = None,
        baseline_rate: float | None = None,
        direction: str = "any",
        unirate_conn_id: str = UniRateHook.default_conn_name,
        timeout_sec: int = 30,
        mode: str = "reschedule",
        poke_interval: float = 3600.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(mode=mode, poke_interval=poke_interval, **kwargs)
        if (threshold_pct is None) == (abs_threshold is None):
            raise AirflowException(
                "Exactly one of `threshold_pct` or `abs_threshold` must be set."
            )
        if threshold_pct is not None and threshold_pct <= 0:
            raise AirflowException("`threshold_pct` must be > 0.")
        if abs_threshold is not None and abs_threshold <= 0:
            raise AirflowException("`abs_threshold` must be > 0.")
        if direction not in {"any", "up", "down"}:
            raise AirflowException("`direction` must be one of: any, up, down.")
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.threshold_pct = threshold_pct
        self.abs_threshold = abs_threshold
        self.baseline_rate = baseline_rate
        self.direction = direction
        self.unirate_conn_id = unirate_conn_id
        self.timeout_sec = timeout_sec
        self._baseline: float | None = baseline_rate

    def poke(self, context: Any) -> bool | PokeReturnValue:
        hook = UniRateHook(
            unirate_conn_id=self.unirate_conn_id, timeout=self.timeout_sec
        )
        latest = hook.get_rate(
            from_currency=self.from_currency, to_currency=self.to_currency
        )
        if self._baseline is None:
            self._baseline = latest
            self.log.info(
                "UniRate sensor: baseline %s→%s = %s; will trigger on movement",
                self.from_currency, self.to_currency, latest,
            )
            return False

        delta = latest - self._baseline
        moved_enough = (
            self.abs_threshold is not None and abs(delta) >= self.abs_threshold
        ) or (
            self.threshold_pct is not None
            and self._baseline != 0
            and abs(delta) / abs(self._baseline) >= self.threshold_pct
        )
        direction_ok = (
            self.direction == "any"
            or (self.direction == "up" and delta > 0)
            or (self.direction == "down" and delta < 0)
        )
        self.log.info(
            "UniRate sensor poke %s→%s: baseline=%s latest=%s delta=%s moved=%s direction_ok=%s",
            self.from_currency, self.to_currency,
            self._baseline, latest, delta, moved_enough, direction_ok,
        )
        if moved_enough and direction_ok:
            return PokeReturnValue(is_done=True, xcom_value=latest)
        return False
