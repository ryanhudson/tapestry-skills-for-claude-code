#!/usr/bin/env python3
"""Secure file downloads with size limits and validation.

Usage:
    tapestry-safe-download <url> <output_path> [--max-size=104857600] [--timeout=300]

Downloads a file with security checks:
- URL validation
- Size limits (default 100MB)
- Timeout protection
- Atomic write (temp file then move)
"""

import argparse
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from tapestry.validate_url import validate_url

# Default limits
DEFAULT_MAX_SIZE = 100 * 1024 * 1024  # 100MB
DEFAULT_TIMEOUT = 300  # 5 minutes
MAX_REDIRECTS = 5
CHUNK_SIZE = 8192

# User agent to avoid blocks
USER_AGENT = "Mozilla/5.0 (compatible; Tapestry/1.0)"


def safe_download(
    url: str,
    output_path: str,
    max_size: int = DEFAULT_MAX_SIZE,
    timeout: int = DEFAULT_TIMEOUT,
) -> tuple[bool, str]:
    """Download a file with security checks.

    Args:
        url: URL to download
        output_path: Where to save the file
        max_size: Maximum file size in bytes
        timeout: Request timeout in seconds

    Returns:
        Tuple of (success, message)
    """
    # Validate URL first
    is_valid, error = validate_url(url)
    if not is_valid:
        return False, f"Invalid URL: {error}"

    output = Path(output_path)

    # Create parent directory if needed
    output.parent.mkdir(parents=True, exist_ok=True)

    # Download to temp file first (atomic write)
    temp_fd = None
    temp_path = None

    try:
        # Create temp file in same directory (for atomic move)
        temp_fd, temp_path = tempfile.mkstemp(
            dir=output.parent,
            prefix=".download_",
            suffix=".tmp"
        )

        # Build request with headers
        request = Request(url, headers={"User-Agent": USER_AGENT})

        # Open connection
        with urlopen(request, timeout=timeout) as response:
            # Check content length if provided
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > max_size:
                return False, f"File too large: {int(content_length)} bytes (max {max_size})"

            # Download in chunks with size tracking
            downloaded = 0
            with open(temp_fd, "wb") as f:
                while True:
                    chunk = response.read(CHUNK_SIZE)
                    if not chunk:
                        break

                    downloaded += len(chunk)
                    if downloaded > max_size:
                        return False, f"Download exceeded max size ({max_size} bytes)"

                    f.write(chunk)

            # Close temp_fd so we can move the file
            temp_fd = None

        # Atomic move to final location
        shutil.move(temp_path, output)
        temp_path = None  # Don't delete in finally

        return True, f"Downloaded {downloaded} bytes to {output}"

    except HTTPError as e:
        return False, f"HTTP error {e.code}: {e.reason}"
    except URLError as e:
        return False, f"URL error: {e.reason}"
    except TimeoutError:
        return False, f"Download timed out after {timeout} seconds"
    except Exception as e:
        return False, f"Download failed: {e}"
    finally:
        # Clean up temp file on failure
        if temp_fd is not None:
            try:
                import os
                os.close(temp_fd)
            except Exception:
                pass
        if temp_path is not None:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except Exception:
                pass


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Securely download a file with size limits"
    )
    parser.add_argument("url", help="URL to download")
    parser.add_argument("output", help="Output file path")
    parser.add_argument(
        "--max-size",
        type=int,
        default=DEFAULT_MAX_SIZE,
        help=f"Maximum file size in bytes (default: {DEFAULT_MAX_SIZE})"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT})"
    )

    args = parser.parse_args()

    success, message = safe_download(
        args.url,
        args.output,
        max_size=args.max_size,
        timeout=args.timeout
    )

    if success:
        print(message)
        return 0
    else:
        print(f"Error: {message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
