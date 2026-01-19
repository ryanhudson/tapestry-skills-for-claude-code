#!/usr/bin/env python3
"""URL validation with SSRF protection.

Usage:
    tapestry-validate-url <url>

Returns exit code 0 if valid, 1 if invalid.
Prints "valid" to stdout on success, error message to stderr on failure.
"""

import re
import sys
from urllib.parse import urlparse

# Private/internal IP patterns (SSRF protection)
BLOCKED_HOST_PATTERNS = [
    r"^localhost$",
    r"^127\.",
    r"^10\.",
    r"^172\.(1[6-9]|2[0-9]|3[01])\.",
    r"^192\.168\.",
    r"^0\.0\.0\.0$",
    r"^\[::1\]$",
    r"^\[fe80:",
    r"^169\.254\.",  # Link-local
    r"^fc00:",  # IPv6 unique local
    r"^fd00:",  # IPv6 unique local
]


def validate_url(url: str) -> tuple[bool, str]:
    """Validate URL for security.

    Checks:
    - Protocol is http or https
    - Host is not internal/localhost (SSRF protection)
    - No embedded credentials
    - Warns on path traversal patterns

    Args:
        url: The URL to validate

    Returns:
        Tuple of (is_valid, message).
        If valid, message is "valid".
        If invalid, message describes the error.
    """
    if not url:
        return False, "No URL provided"

    # Check protocol
    if not re.match(r"^https?://", url, re.IGNORECASE):
        return False, f"Only HTTP/HTTPS URLs supported. Got: {url[:30]}..."

    # Block file:// protocol attempts (even if disguised)
    if re.match(r"^file://", url, re.IGNORECASE):
        return False, "file:// URLs are not allowed"

    # Parse URL
    try:
        parsed = urlparse(url)
        host = parsed.hostname or ""
    except Exception as e:
        return False, f"Invalid URL format: {e}"

    if not host:
        return False, "URL has no hostname"

    # Block internal networks (SSRF protection)
    for pattern in BLOCKED_HOST_PATTERNS:
        if re.match(pattern, host, re.IGNORECASE):
            return False, "Internal/localhost URLs not allowed"

    # Block embedded credentials
    if parsed.username or parsed.password:
        return False, "URLs with embedded credentials not allowed"

    # Warn on path traversal (don't fail - filename sanitizer handles it)
    if re.search(r"\.\./|\.\.\\|%2e%2e", url, re.IGNORECASE):
        print("Warning: URL contains path traversal patterns", file=sys.stderr)

    return True, "valid"


def main() -> int:
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: tapestry-validate-url <url>", file=sys.stderr)
        print("Returns 0 if valid, 1 if invalid", file=sys.stderr)
        return 1

    url = sys.argv[1]
    is_valid, message = validate_url(url)

    if is_valid:
        print("valid")
        return 0
    else:
        print(f"Error: {message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
