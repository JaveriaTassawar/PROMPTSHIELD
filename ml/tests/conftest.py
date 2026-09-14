"""pytest configuration for the ML test suite.

Registers the `slow` marker and the `--slow` flag. Four adapters read very
large files (WildJailbreak 506 MB, llmail_phase1 427 MB, llmail_phase2 65 MB,
BIPIA 100 MB) and take minutes, so they are skipped unless asked for:

    pytest tests/ -v            fast structural tests only
    pytest tests/ -v --slow     everything
"""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--slow",
        action="store_true",
        default=False,
        help="also run tests against the large dataset files",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "slow: reads a large dataset file; only runs with --slow"
    )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if config.getoption("--slow"):
        return
    skip = pytest.mark.skip(reason="large-file test; pass --slow to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip)
