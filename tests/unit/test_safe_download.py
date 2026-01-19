"""Tests for safe download functionality."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from tapestry.safe_download import safe_download, DEFAULT_MAX_SIZE


class TestURLValidation:
    """Test that URL validation happens before download."""

    def test_rejects_invalid_url(self, tmp_path):
        output = tmp_path / "output.txt"
        success, msg = safe_download("not-a-url", str(output))
        assert success is False
        assert "Invalid URL" in msg

    def test_rejects_localhost(self, tmp_path):
        output = tmp_path / "output.txt"
        success, msg = safe_download("http://localhost/file", str(output))
        assert success is False
        assert "Invalid URL" in msg

    def test_rejects_internal_ip(self, tmp_path):
        output = tmp_path / "output.txt"
        success, msg = safe_download("http://192.168.1.1/file", str(output))
        assert success is False
        assert "Invalid URL" in msg


class TestSizeLimits:
    """Test download size limits."""

    @patch("tapestry.safe_download.urlopen")
    def test_rejects_oversized_content_length(self, mock_urlopen, tmp_path):
        """Reject if Content-Length header exceeds limit."""
        mock_response = MagicMock()
        mock_response.headers = {"Content-Length": str(DEFAULT_MAX_SIZE + 1)}
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        output = tmp_path / "output.txt"
        success, msg = safe_download(
            "https://example.com/large-file",
            str(output),
            max_size=1000
        )
        assert success is False
        assert "too large" in msg.lower()

    @patch("tapestry.safe_download.urlopen")
    def test_stops_download_when_size_exceeded(self, mock_urlopen, tmp_path):
        """Stop download if content exceeds limit during streaming."""
        mock_response = MagicMock()
        mock_response.headers = MagicMock()
        mock_response.headers.get = MagicMock(return_value=None)  # No Content-Length
        # Return chunks that exceed limit
        mock_response.read = MagicMock(side_effect=[b"x" * 600, b"x" * 600])
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        output = tmp_path / "output.txt"
        success, msg = safe_download(
            "https://example.com/streaming-file",
            str(output),
            max_size=1000
        )
        assert success is False
        assert "exceeded" in msg.lower()


class TestSuccessfulDownload:
    """Test successful download scenarios."""

    @patch("tapestry.safe_download.urlopen")
    def test_successful_download(self, mock_urlopen, tmp_path):
        """Test successful file download."""
        test_content = b"Hello, World!"

        mock_response = MagicMock()
        mock_response.headers = MagicMock()
        mock_response.headers.get = MagicMock(return_value=str(len(test_content)))
        mock_response.read = MagicMock(side_effect=[test_content, b""])
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        output = tmp_path / "output.txt"
        success, msg = safe_download("https://example.com/file.txt", str(output))

        assert success is True
        assert output.exists()
        assert output.read_bytes() == test_content

    @patch("tapestry.safe_download.urlopen")
    def test_creates_parent_directories(self, mock_urlopen, tmp_path):
        """Test that parent directories are created."""
        test_content = b"Content"

        mock_response = MagicMock()
        mock_response.headers = MagicMock()
        mock_response.headers.get = MagicMock(return_value=str(len(test_content)))
        mock_response.read = MagicMock(side_effect=[test_content, b""])
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        output = tmp_path / "nested" / "dirs" / "output.txt"
        success, msg = safe_download("https://example.com/file.txt", str(output))

        assert success is True
        assert output.exists()


class TestErrorHandling:
    """Test error handling."""

    @patch("tapestry.safe_download.urlopen")
    def test_handles_http_error(self, mock_urlopen, tmp_path):
        """Test handling of HTTP errors."""
        from urllib.error import HTTPError
        mock_urlopen.side_effect = HTTPError(
            "https://example.com/file",
            404,
            "Not Found",
            {},
            None
        )

        output = tmp_path / "output.txt"
        success, msg = safe_download("https://example.com/file.txt", str(output))

        assert success is False
        assert "404" in msg

    @patch("tapestry.safe_download.urlopen")
    def test_handles_url_error(self, mock_urlopen, tmp_path):
        """Test handling of URL errors."""
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("Connection refused")

        output = tmp_path / "output.txt"
        success, msg = safe_download("https://example.com/file.txt", str(output))

        assert success is False
        assert "error" in msg.lower()

    @patch("tapestry.safe_download.urlopen")
    def test_handles_timeout(self, mock_urlopen, tmp_path):
        """Test handling of timeout errors."""
        mock_urlopen.side_effect = TimeoutError()

        output = tmp_path / "output.txt"
        success, msg = safe_download(
            "https://example.com/file.txt",
            str(output),
            timeout=1
        )

        assert success is False
        assert "timed out" in msg.lower()

    @patch("tapestry.safe_download.urlopen")
    def test_cleans_up_temp_file_on_failure(self, mock_urlopen, tmp_path):
        """Test that temp file is cleaned up on failure."""
        mock_response = MagicMock()
        mock_response.headers = MagicMock()
        mock_response.headers.get = MagicMock(return_value=None)
        # Fail during read
        mock_response.read = MagicMock(side_effect=Exception("Read error"))
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        output = tmp_path / "output.txt"
        success, msg = safe_download("https://example.com/file.txt", str(output))

        assert success is False
        # Output file should not exist
        assert not output.exists()
        # No temp files should remain
        temp_files = list(tmp_path.glob(".download_*"))
        assert len(temp_files) == 0
