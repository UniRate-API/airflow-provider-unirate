"""Shared pytest fixtures."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock

import pytest

# Quiet Airflow's "you must initialise the db" warnings during unit tests.
os.environ.setdefault("AIRFLOW__CORE__UNIT_TEST_MODE", "True")
os.environ.setdefault("AIRFLOW__CORE__LOAD_EXAMPLES", "False")
os.environ.setdefault("AIRFLOW__CORE__LOAD_DEFAULT_CONNECTIONS", "False")


@pytest.fixture
def fake_connection(monkeypatch):
    """Patch ``BaseHook.get_connection`` to return a connection with a fixed API key."""
    from airflow.models import Connection
    from airflow.hooks import base as base_hook

    conn = Connection(
        conn_id="unirate_default",
        conn_type="unirate",
        password="test-api-key",
    )
    monkeypatch.setattr(base_hook.BaseHook, "get_connection", lambda *_args, **_kw: conn)
    return conn


@pytest.fixture
def mock_unirate_client(monkeypatch):
    """Replace ``UnirateClient`` with a MagicMock; yield the mock instance."""
    from unirate_provider.hooks import unirate as hook_module

    mock_instance = MagicMock(name="UnirateClient")
    monkeypatch.setattr(hook_module, "UnirateClient", lambda *a, **kw: mock_instance)
    return mock_instance
