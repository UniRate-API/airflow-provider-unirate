"""Tests for the provider entry-point and metadata."""

from __future__ import annotations

import importlib.metadata


def test_get_provider_info_shape():
    from unirate_provider import __version__, get_provider_info

    info = get_provider_info()
    assert info["package-name"] == "airflow-provider-unirate"
    assert info["name"] == "UniRate"
    assert __version__ in info["versions"]
    assert info["connection-types"][0] == {
        "connection-type": "unirate",
        "hook-class-name": "unirate_provider.hooks.unirate.UniRateHook",
    }
    assert {"hooks", "operators", "sensors", "integrations"} <= info.keys()


def test_provider_info_required_keys_present():
    from unirate_provider import get_provider_info

    info = get_provider_info()
    # Per airflow's provider_info.schema.json the required top-level keys are
    # `name` and `description`.
    assert "name" in info and info["name"]
    assert "description" in info and info["description"]


def test_entry_point_resolves_to_get_provider_info():
    """Once the package is installed, the entry point must resolve."""
    eps = importlib.metadata.entry_points()
    # 3.10+ returns an EntryPoints object with .select(); 3.9 returns a dict.
    group = (
        list(eps.select(group="apache_airflow_provider"))
        if hasattr(eps, "select")
        else list(eps.get("apache_airflow_provider", []))
    )
    matches = [
        ep for ep in group
        if ep.name == "provider_info" and "unirate_provider" in ep.value
    ]
    assert matches, "apache_airflow_provider entry point not registered"
    func = matches[0].load()
    info = func()
    assert info["name"] == "UniRate"
