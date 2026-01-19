"""Shared pytest fixtures for tapestry tests."""

import pytest
from pathlib import Path

# Path to fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def sample_vtt(fixtures_dir) -> Path:
    """Return path to sample VTT file."""
    return fixtures_dir / "sample.vtt"


@pytest.fixture
def sample_vtt_content(sample_vtt) -> str:
    """Return contents of sample VTT file."""
    return sample_vtt.read_text()


@pytest.fixture
def expected_vtt_output(fixtures_dir) -> str:
    """Return expected clean text from VTT conversion."""
    return (fixtures_dir / "sample_clean.txt").read_text()


@pytest.fixture
def sample_html(fixtures_dir) -> Path:
    """Return path to sample HTML file."""
    return fixtures_dir / "sample.html"


@pytest.fixture
def sample_html_content(sample_html) -> str:
    """Return contents of sample HTML file."""
    return sample_html.read_text()


@pytest.fixture
def expected_html_output(fixtures_dir) -> str:
    """Return expected clean text from HTML extraction."""
    return (fixtures_dir / "sample_clean.html.txt").read_text()
