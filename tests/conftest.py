"""Pytest configuration for turtlebot3_acmpc tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def src_path() -> Path:
    """Return the src directory."""
    return Path(__file__).parent.parent / "src"
