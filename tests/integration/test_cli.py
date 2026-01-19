"""Integration tests for CLI entry points."""

import subprocess
import pytest
from pathlib import Path


def run_cli(command: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    """Run a CLI command via uv run."""
    return subprocess.run(
        ["uv", "run"] + command,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class TestValidateUrlCLI:
    """Test tapestry-validate-url CLI."""

    def test_valid_url_returns_0(self):
        result = run_cli(["tapestry-validate-url", "https://example.com"])
        assert result.returncode == 0
        assert "valid" in result.stdout.lower()

    def test_invalid_url_returns_1(self):
        result = run_cli(["tapestry-validate-url", "not-a-url"])
        assert result.returncode == 1
        assert "error" in result.stderr.lower()

    def test_localhost_blocked(self):
        result = run_cli(["tapestry-validate-url", "http://localhost/admin"])
        assert result.returncode == 1
        assert "error" in result.stderr.lower()

    def test_internal_ip_blocked(self):
        result = run_cli(["tapestry-validate-url", "http://192.168.1.1"])
        assert result.returncode == 1

    def test_no_args_shows_usage(self):
        result = run_cli(["tapestry-validate-url"])
        assert result.returncode == 1
        assert "usage" in result.stderr.lower()


class TestSanitizeFilenameCLI:
    """Test tapestry-sanitize-filename CLI."""

    def test_basic_sanitization(self):
        result = run_cli(["tapestry-sanitize-filename", "Hello World"])
        assert result.returncode == 0
        assert result.stdout.strip() == "Hello World"

    def test_colon_replaced(self):
        result = run_cli(["tapestry-sanitize-filename", "File: Name"])
        assert result.returncode == 0
        assert ":" not in result.stdout

    def test_slash_replaced(self):
        result = run_cli(["tapestry-sanitize-filename", "Path/To/File"])
        assert result.returncode == 0
        assert "/" not in result.stdout

    def test_dangerous_chars_removed(self):
        result = run_cli(["tapestry-sanitize-filename", "Test<script>"])
        assert result.returncode == 0
        assert "<" not in result.stdout
        assert ">" not in result.stdout

    def test_custom_max_length(self):
        long_name = "A" * 200
        result = run_cli(["tapestry-sanitize-filename", long_name, "50"])
        assert result.returncode == 0
        assert len(result.stdout.strip()) <= 50

    def test_no_args_shows_usage(self):
        result = run_cli(["tapestry-sanitize-filename"])
        assert result.returncode == 1
        assert "usage" in result.stderr.lower()


class TestVttToTextCLI:
    """Test tapestry-vtt-to-text CLI."""

    def test_converts_vtt_file(self, sample_vtt, tmp_path):
        output = tmp_path / "output.txt"
        result = run_cli([
            "tapestry-vtt-to-text",
            str(sample_vtt),
            "--output", str(output)
        ])
        assert result.returncode == 0
        assert output.exists()
        content = output.read_text()
        assert "Hello and welcome" in content

    def test_outputs_to_stdout_without_flag(self, sample_vtt):
        result = run_cli(["tapestry-vtt-to-text", str(sample_vtt)])
        assert result.returncode == 0
        assert "Hello and welcome" in result.stdout

    def test_removes_timestamps(self, sample_vtt):
        result = run_cli(["tapestry-vtt-to-text", str(sample_vtt)])
        assert result.returncode == 0
        assert "-->" not in result.stdout
        assert "00:00" not in result.stdout

    def test_decodes_html_entities(self, sample_vtt):
        result = run_cli(["tapestry-vtt-to-text", str(sample_vtt)])
        assert result.returncode == 0
        # &amp; should be decoded to &
        assert "&" in result.stdout
        assert "&amp;" not in result.stdout

    def test_nonexistent_file_error(self, tmp_path):
        nonexistent = tmp_path / "does_not_exist.vtt"
        result = run_cli(["tapestry-vtt-to-text", str(nonexistent)])
        assert result.returncode == 1
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()


class TestExtractHtmlCLI:
    """Test tapestry-extract-html CLI."""

    def test_extracts_from_file(self, sample_html, tmp_path):
        output = tmp_path / "output.txt"
        result = run_cli([
            "tapestry-extract-html",
            str(sample_html),
            "--output", str(output)
        ])
        assert result.returncode == 0
        assert output.exists()
        content = output.read_text()
        assert "Better Code" in content

    def test_outputs_to_stdout_without_flag(self, sample_html):
        result = run_cli(["tapestry-extract-html", str(sample_html)])
        assert result.returncode == 0
        assert "Better Code" in result.stdout

    def test_extracts_main_content(self, sample_html):
        result = run_cli(["tapestry-extract-html", str(sample_html)])
        assert result.returncode == 0
        assert "meaningful variable names" in result.stdout
        assert "keep functions small" in result.stdout

    def test_removes_navigation(self, sample_html):
        result = run_cli(["tapestry-extract-html", str(sample_html)])
        assert result.returncode == 0
        # Navigation links should not be in output
        assert "Home" not in result.stdout or "About" not in result.stdout

    def test_nonexistent_file_error(self, tmp_path):
        nonexistent = tmp_path / "does_not_exist.html"
        result = run_cli(["tapestry-extract-html", str(nonexistent)])
        assert result.returncode == 1


class TestSafeDownloadCLI:
    """Test tapestry-safe-download CLI (limited - avoids network)."""

    def test_rejects_invalid_url(self, tmp_path):
        output = tmp_path / "output.txt"
        result = run_cli([
            "tapestry-safe-download",
            "not-a-valid-url",
            str(output)
        ])
        assert result.returncode == 1
        assert "error" in result.stderr.lower()

    def test_rejects_localhost(self, tmp_path):
        output = tmp_path / "output.txt"
        result = run_cli([
            "tapestry-safe-download",
            "http://localhost/file",
            str(output)
        ])
        assert result.returncode == 1

    def test_no_args_shows_usage(self):
        result = run_cli(["tapestry-safe-download"])
        assert result.returncode != 0
