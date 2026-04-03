"""Pytest configuration for turtlebot3_acmpc tests."""

from __future__ import annotations

import logging
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def configure_test_logging():
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def src_path() -> Path:
    """Return the src directory."""
    return Path(__file__).parent.parent / "src"
