#!/bin/bash
# safe-download.sh - Download files with security checks
# Usage: ./safe-download.sh "URL" "output_filename" [max_size_mb]
# Returns: 0 on success, 1 on failure

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

URL="$1"
OUTPUT="$2"
MAX_SIZE_MB="${3:-100}"  # Default 100MB limit

if [ -z "$URL" ] || [ -z "$OUTPUT" ]; then
    echo "Error: Usage: safe-download.sh URL OUTPUT [MAX_SIZE_MB]" >&2
    exit 1
fi

# Validate URL first
if ! "$SCRIPT_DIR/validate-url.sh" "$URL" > /dev/null 2>&1; then
    "$SCRIPT_DIR/validate-url.sh" "$URL" 2>&1
    exit 1
fi

# Sanitize output filename
SAFE_OUTPUT=$("$SCRIPT_DIR/sanitize-filename.sh" "$OUTPUT")

# Ensure output doesn't escape current directory
if [[ "$SAFE_OUTPUT" =~ ^/ ]] || [[ "$SAFE_OUTPUT" =~ \.\. ]]; then
    echo "Error: Output path must be relative and not contain .." >&2
    exit 1
fi

# Calculate max size in bytes
MAX_SIZE_BYTES=$((MAX_SIZE_MB * 1024 * 1024))

# Create a temporary file in current directory
TEMP_FILE=$(mktemp -p . "download.XXXXXX")
trap "rm -f '$TEMP_FILE'" EXIT

# Download with security options
curl \
    --silent \
    --show-error \
    --location \
    --max-redirs 5 \
    --max-filesize "$MAX_SIZE_BYTES" \
    --max-time 300 \
    --output "$TEMP_FILE" \
    "$URL"

CURL_EXIT=$?

if [ $CURL_EXIT -ne 0 ]; then
    echo "Error: Download failed (curl exit code: $CURL_EXIT)" >&2
    if [ $CURL_EXIT -eq 63 ]; then
        echo "Error: File exceeds maximum size of ${MAX_SIZE_MB}MB" >&2
    fi
    exit 1
fi

# Move to final location
mv "$TEMP_FILE" "$SAFE_OUTPUT"
trap - EXIT  # Clear the trap since we moved the file

echo "Downloaded: $SAFE_OUTPUT"
exit 0
