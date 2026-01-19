#!/bin/bash
# validate-url.sh - Validate URLs for security
# Usage: ./validate-url.sh "URL"
# Returns: 0 if valid, 1 if invalid (with error message to stderr)

set -e

URL="$1"

if [ -z "$URL" ]; then
    echo "Error: No URL provided" >&2
    exit 1
fi

# Check for valid protocol (only http/https allowed)
if [[ ! "$URL" =~ ^https?:// ]]; then
    echo "Error: Only HTTP/HTTPS URLs are supported. Got: ${URL:0:20}..." >&2
    exit 1
fi

# Block file:// protocol attempts
if [[ "$URL" =~ ^file:// ]]; then
    echo "Error: file:// URLs are not allowed" >&2
    exit 1
fi

# Block localhost/internal network access (SSRF protection)
if [[ "$URL" =~ ^https?://(localhost|127\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|0\.0\.0\.0|\[::1\]|\[fe80:) ]]; then
    echo "Error: Internal/localhost URLs are not allowed" >&2
    exit 1
fi

# Block URLs with credentials embedded
if [[ "$URL" =~ ^https?://[^/]*:[^/]*@ ]]; then
    echo "Error: URLs with embedded credentials are not allowed" >&2
    exit 1
fi

# Check for suspicious path traversal in URL
if [[ "$URL" =~ \.\./|\.\.\\|%2e%2e ]]; then
    echo "Warning: URL contains path traversal patterns" >&2
    # Don't fail, but warn - the filename sanitizer will handle it
fi

# URL is valid
echo "valid"
exit 0
