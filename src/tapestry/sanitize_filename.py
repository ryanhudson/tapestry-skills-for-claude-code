#!/usr/bin/env python3
"""Filename sanitization for safe filesystem use.

Usage:
    tapestry-sanitize-filename <string> [max_length]

Prints sanitized filename to stdout.
"""

import re
import sys
import unicodedata

# Characters that are problematic across filesystems
DANGEROUS_CHARS = {
    "/": "_",      # Unix path separator
    "\\": "_",     # Windows path separator
    ":": "-",      # Windows drive separator, macOS
    "*": "",       # Wildcard
    "?": "",       # Wildcard
    '"': "",       # Quote
    "'": "",       # Quote
    "<": "",       # Redirect
    ">": "",       # Redirect
    "|": "-",      # Pipe
    "`": "",       # Backtick (shell)
    "$": "",       # Variable expansion
    "\0": "",      # Null byte
    "\n": " ",     # Newline
    "\r": "",      # Carriage return
    "\t": " ",     # Tab
}

# Reserved Windows filenames
WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}


def sanitize_filename(name: str, max_length: int = 100) -> str:
    """Sanitize a string for safe use as a filename.

    Operations:
    1. Normalize unicode (NFC)
    2. Replace/remove dangerous characters
    3. Remove control characters
    4. Remove path traversal sequences (..)
    5. Collapse repeated separators
    6. Trim leading/trailing whitespace and dots
    7. Handle Windows reserved names
    8. Limit length

    Args:
        name: The string to sanitize
        max_length: Maximum length (default 100)

    Returns:
        Sanitized filename, or "unnamed" if result would be empty
    """
    if not name:
        return "unnamed"

    # Normalize unicode
    result = unicodedata.normalize("NFC", name)

    # Replace/remove dangerous characters
    for char, replacement in DANGEROUS_CHARS.items():
        result = result.replace(char, replacement)

    # Remove control characters
    result = "".join(c for c in result if not unicodedata.category(c).startswith("C"))

    # Remove path traversal sequences
    result = re.sub(r"\.\.+", "", result)

    # Collapse repeated dashes and underscores
    result = re.sub(r"-{2,}", "-", result)
    result = re.sub(r"_{2,}", "_", result)
    result = re.sub(r" {2,}", " ", result)

    # Trim leading/trailing whitespace and dots
    result = result.strip(" .")

    # Handle Windows reserved names
    name_upper = result.upper().split(".")[0]
    if name_upper in WINDOWS_RESERVED:
        result = f"_{result}"

    # Limit length (preserve extension if present)
    if len(result) > max_length:
        if "." in result[-10:]:
            # Has extension in last 10 chars
            name_part, ext = result.rsplit(".", 1)
            max_name = max_length - len(ext) - 1
            result = f"{name_part[:max_name]}.{ext}"
        else:
            result = result[:max_length]

    # Final check
    if not result:
        return "unnamed"

    return result


def main() -> int:
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: tapestry-sanitize-filename <string> [max_length]", file=sys.stderr)
        return 1

    name = sys.argv[1]
    max_length = int(sys.argv[2]) if len(sys.argv) > 2 else 100

    result = sanitize_filename(name, max_length)
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
