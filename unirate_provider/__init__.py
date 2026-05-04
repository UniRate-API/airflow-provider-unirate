"""Apache Airflow provider for UniRateAPI.

Exposes:
- ``UniRateHook`` (conn_type: ``unirate``)
- ``UniRateGetRateOperator`` / ``UniRateConvertOperator``
- ``UniRateRateChangeSensor``
"""

from __future__ import annotations

__version__ = "0.1.0"


def get_provider_info() -> dict:
    return {
        "package-name": "airflow-provider-unirate",
        "name": "UniRate",
        "description": "UniRateAPI provider for Apache Airflow: real-time and historical currency exchange rates.",
        "versions": [__version__],
        "connection-types": [
            {
                "connection-type": "unirate",
                "hook-class-name": "unirate_provider.hooks.unirate.UniRateHook",
            }
        ],
        "hooks": [
            {
                "integration-name": "UniRate",
                "python-modules": ["unirate_provider.hooks.unirate"],
            }
        ],
        "operators": [
            {
                "integration-name": "UniRate",
                "python-modules": ["unirate_provider.operators.unirate"],
            }
        ],
        "sensors": [
            {
                "integration-name": "UniRate",
                "python-modules": ["unirate_provider.sensors.unirate"],
            }
        ],
        "integrations": [
            {
                "integration-name": "UniRate",
                "external-doc-url": "https://unirateapi.com/docs",
                "logo": "/integration-logos/unirate.png",
                "tags": ["service"],
            }
        ],
    }
