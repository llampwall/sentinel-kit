"""Smoke test that imports every sentinelkit module."""

import pkgutil

import sentinelkit


def test_import_all_modules() -> None:
    modules = [pkg.name for pkg in pkgutil.walk_packages(sentinelkit.__path__, sentinelkit.__name__ + '.')]
    for mod in modules:
        __import__(mod)
