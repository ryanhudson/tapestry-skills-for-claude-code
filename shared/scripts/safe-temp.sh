#!/bin/bash
# safe-temp.sh - Create and manage secure temporary files/directories
# Usage:
#   ./safe-temp.sh file [prefix]  - Create temp file, print path
#   ./safe-temp.sh dir [prefix]   - Create temp directory, print path
#   ./safe-temp.sh cleanup PATH   - Remove temp file/directory

set -e

MODE="$1"
ARG="$2"

case "$MODE" in
    file)
        PREFIX="${ARG:-tapestry}"
        TEMP_FILE=$(mktemp -t "${PREFIX}.XXXXXX")
        echo "$TEMP_FILE"
        ;;

    dir)
        PREFIX="${ARG:-tapestry}"
        TEMP_DIR=$(mktemp -d -t "${PREFIX}.XXXXXX")
        echo "$TEMP_DIR"
        ;;

    cleanup)
        if [ -z "$ARG" ]; then
            echo "Error: No path provided for cleanup" >&2
            exit 1
        fi

        # Verify it's actually a temp file (contains expected pattern)
        if [[ ! "$ARG" =~ ^(/tmp/|/var/folders/|$TMPDIR) ]]; then
            echo "Error: Path doesn't appear to be a temp file: $ARG" >&2
            exit 1
        fi

        if [ -d "$ARG" ]; then
            rm -rf "$ARG"
        elif [ -f "$ARG" ]; then
            rm -f "$ARG"
        fi
        echo "Cleaned up: $ARG"
        ;;

    *)
        echo "Usage:" >&2
        echo "  $0 file [prefix]  - Create temp file" >&2
        echo "  $0 dir [prefix]   - Create temp directory" >&2
        echo "  $0 cleanup PATH   - Remove temp file/directory" >&2
        exit 1
        ;;
esac
