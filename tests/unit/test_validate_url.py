"""Tests for URL validation with SSRF protection."""

import pytest
from tapestry.validate_url import validate_url


class TestValidUrls:
    """Test cases for valid URLs."""

    def test_https_url(self):
        is_valid, msg = validate_url("https://example.com")
        assert is_valid is True
        assert msg == "valid"

    def test_http_url(self):
        is_valid, msg = validate_url("http://example.com")
        assert is_valid is True
        assert msg == "valid"

    def test_url_with_path(self):
        is_valid, msg = validate_url("https://example.com/path/to/page")
        assert is_valid is True

    def test_url_with_query(self):
        is_valid, msg = validate_url("https://example.com/search?q=test&page=1")
        assert is_valid is True

    def test_url_with_port(self):
        is_valid, msg = validate_url("https://example.com:8080/api")
        assert is_valid is True

    def test_url_with_fragment(self):
        is_valid, msg = validate_url("https://example.com/page#section")
        assert is_valid is True


class TestInvalidProtocols:
    """Test cases for invalid protocols."""

    def test_ftp_protocol(self):
        is_valid, msg = validate_url("ftp://example.com/file.txt")
        assert is_valid is False
        assert "HTTP/HTTPS" in msg

    def test_file_protocol(self):
        is_valid, msg = validate_url("file:///etc/passwd")
        assert is_valid is False

    def test_javascript_protocol(self):
        is_valid, msg = validate_url("javascript:alert(1)")
        assert is_valid is False

    def test_data_protocol(self):
        is_valid, msg = validate_url("data:text/html,<script>alert(1)</script>")
        assert is_valid is False

    def test_no_protocol(self):
        is_valid, msg = validate_url("example.com")
        assert is_valid is False


class TestSSRFProtection:
    """Test cases for SSRF protection (internal network blocking)."""

    def test_localhost(self):
        is_valid, msg = validate_url("http://localhost/admin")
        assert is_valid is False
        assert "Internal" in msg or "localhost" in msg

    def test_localhost_with_port(self):
        is_valid, msg = validate_url("http://localhost:8080/api")
        assert is_valid is False

    def test_127_0_0_1(self):
        is_valid, msg = validate_url("http://127.0.0.1/secret")
        assert is_valid is False

    def test_127_x_x_x(self):
        is_valid, msg = validate_url("http://127.1.2.3/api")
        assert is_valid is False

    def test_10_network(self):
        is_valid, msg = validate_url("http://10.0.0.1/internal")
        assert is_valid is False

    def test_10_network_any(self):
        is_valid, msg = validate_url("http://10.255.255.255/api")
        assert is_valid is False

    def test_172_16_network(self):
        is_valid, msg = validate_url("http://172.16.0.1/private")
        assert is_valid is False

    def test_172_31_network(self):
        is_valid, msg = validate_url("http://172.31.255.255/api")
        assert is_valid is False

    def test_172_15_network_allowed(self):
        # 172.15.x.x is NOT private, should be allowed
        is_valid, msg = validate_url("http://172.15.0.1/public")
        assert is_valid is True

    def test_192_168_network(self):
        is_valid, msg = validate_url("http://192.168.1.1/router")
        assert is_valid is False

    def test_192_168_any(self):
        is_valid, msg = validate_url("http://192.168.255.255/api")
        assert is_valid is False

    def test_0_0_0_0(self):
        is_valid, msg = validate_url("http://0.0.0.0/api")
        assert is_valid is False

    def test_ipv6_localhost(self):
        is_valid, msg = validate_url("http://[::1]/api")
        assert is_valid is False

    def test_ipv6_link_local(self):
        is_valid, msg = validate_url("http://[fe80::1]/api")
        assert is_valid is False


class TestEmbeddedCredentials:
    """Test cases for URLs with embedded credentials."""

    def test_username_password(self):
        is_valid, msg = validate_url("http://user:pass@example.com")
        assert is_valid is False
        assert "credentials" in msg.lower()

    def test_username_only(self):
        is_valid, msg = validate_url("http://user@example.com")
        assert is_valid is False


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_string(self):
        is_valid, msg = validate_url("")
        assert is_valid is False
        assert "No URL" in msg

    def test_none(self):
        is_valid, msg = validate_url(None)
        assert is_valid is False

    def test_whitespace_only(self):
        is_valid, msg = validate_url("   ")
        assert is_valid is False

    def test_malformed_url(self):
        is_valid, msg = validate_url("http://")
        assert is_valid is False

    def test_path_traversal_warning(self, capsys):
        """Path traversal should warn but not fail."""
        is_valid, msg = validate_url("https://example.com/../etc/passwd")
        # Should still be valid (warning only)
        assert is_valid is True
        # Check that warning was printed
        captured = capsys.readouterr()
        assert "traversal" in captured.err.lower()
