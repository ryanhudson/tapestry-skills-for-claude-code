#!/bin/bash
# sanitize-filename.sh - Sanitize strings for safe filesystem use
# Usage: ./sanitize-filename.sh "string" [max_length]
# Returns: Sanitized filename (safe for all filesystems)

set -e

INPUT="$1"
MAX_LENGTH="${2:-100}"

if [ -z "$INPUT" ]; then
    echo "Error: No input provided" >&2
    exit 1
fi

# Sanitize the filename:
# 1. Replace dangerous/problematic characters with safe alternatives
# 2. Remove null bytes and control characters
# 3. Collapse multiple dashes/underscores
# 4. Trim leading/trailing whitespace and dots
# 5. Limit length

SANITIZED=$(echo "$INPUT" | \
    tr -d '\0' | \
    tr '/' '_' | \
    tr ':' '-' | \
    tr '\\' '_' | \
    tr '?' '' | \
    tr '"' '' | \
    tr "'" '' | \
    tr '<' '' | \
    tr '>' '' | \
    tr '|' '-' | \
    tr '*' '' | \
    tr '$' '' | \
    tr '`' '' | \
    tr '\n' ' ' | \
    tr '\r' '' | \
    tr '\t' ' ' | \
    sed 's/[[:cntrl:]]//g' | \
    sed 's/--*/-/g' | \
    sed 's/__*/_/g' | \
    sed 's/^[. ]*//' | \
    sed 's/[. ]*$//' | \
    cut -c "1-${MAX_LENGTH}")

# Ensure we have something left
if [ -z "$SANITIZED" ]; then
    SANITIZED="unnamed"
fi

echo "$SANITIZED"
