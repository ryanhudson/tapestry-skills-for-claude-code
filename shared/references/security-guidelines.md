# Security Guidelines for Tapestry Skills

This document outlines security best practices for all Tapestry skills that handle URLs, downloads, and file operations.

## URL Validation

### Required Checks

Before processing any user-provided URL:

1. **Protocol validation**: Only allow `http://` and `https://`
2. **SSRF protection**: Block localhost, internal IPs (10.x, 172.16-31.x, 192.168.x)
3. **Credential stripping**: Reject URLs with embedded username:password
4. **Path traversal detection**: Warn on `../` patterns

### Using the Validation Script

```bash
SCRIPT_DIR="/path/to/shared/scripts"

if ! "$SCRIPT_DIR/validate-url.sh" "$URL" > /dev/null 2>&1; then
    echo "Invalid URL provided"
    exit 1
fi
```

### Manual Validation Pattern

```bash
# Check protocol
if [[ ! "$URL" =~ ^https?:// ]]; then
    echo "Error: Only HTTP/HTTPS URLs supported"
    exit 1
fi

# Block internal networks
if [[ "$URL" =~ ^https?://(localhost|127\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.) ]]; then
    echo "Error: Internal URLs not allowed"
    exit 1
fi
```

## Filename Sanitization

### Dangerous Characters to Remove

| Character | Risk |
|-----------|------|
| `/` | Path traversal |
| `\` | Path traversal (Windows) |
| `..` | Directory escape |
| `:` | Drive letter (Windows), special meaning |
| `*` | Glob expansion |
| `?` | Glob expansion |
| `"` | Quote injection |
| `'` | Quote injection |
| `<` | Redirect operator |
| `>` | Redirect operator |
| `|` | Pipe operator |
| `` ` `` | Command substitution |
| `$` | Variable expansion |
| `\0` | Null byte injection |

### Using the Sanitization Script

```bash
SAFE_NAME=$("$SCRIPT_DIR/sanitize-filename.sh" "$UNTRUSTED_INPUT" 100)
```

### Manual Sanitization Pattern

```bash
SAFE_NAME=$(echo "$INPUT" | \
    tr -d '\0' | \
    tr '/' '_' | \
    tr ':' '-' | \
    tr '\\' '_' | \
    tr -d '?*"<>|`$' | \
    sed 's/\.\.//g' | \
    cut -c 1-100)
```

## Safe File Downloads

### Download Limits

Always set limits when downloading:

```bash
curl \
    --max-filesize 104857600 \  # 100MB limit
    --max-redirs 5 \             # Limit redirects
    --max-time 300 \             # 5 minute timeout
    --location \                 # Follow redirects
    -o "$SAFE_FILENAME" \
    "$VALIDATED_URL"
```

### Using the Safe Download Script

```bash
"$SCRIPT_DIR/safe-download.sh" "$URL" "$OUTPUT_NAME" 100  # 100MB limit
```

### Verify Downloads

After downloading, verify the file:

```bash
# Check file exists and has content
if [ ! -s "$DOWNLOADED_FILE" ]; then
    echo "Error: Download produced empty file"
    exit 1
fi

# For PDFs, verify magic bytes
if [[ "$DOWNLOADED_FILE" =~ \.pdf$ ]]; then
    if ! head -c 4 "$DOWNLOADED_FILE" | grep -q '%PDF'; then
        echo "Error: File is not a valid PDF"
        rm "$DOWNLOADED_FILE"
        exit 1
    fi
fi
```

## Temporary File Handling

### Use System Temp Directories

Never create temp files in the working directory with predictable names:

```bash
# BAD - predictable, race condition risk
echo "content" > temp_file.txt

# GOOD - random name in system temp
TEMP_FILE=$(mktemp)
echo "content" > "$TEMP_FILE"
```

### Cleanup on Exit

Always set up cleanup traps:

```bash
TEMP_DIR=$(mktemp -d)
trap "rm -rf '$TEMP_DIR'" EXIT

# Work in temp directory
cd "$TEMP_DIR"
# ... do work ...
# Cleanup happens automatically on exit
```

### Using the Safe Temp Script

```bash
TEMP_FILE=$("$SCRIPT_DIR/safe-temp.sh" file "youtube")
# ... use temp file ...
"$SCRIPT_DIR/safe-temp.sh" cleanup "$TEMP_FILE"
```

## External Tool Execution

### Validate Tool Availability

```bash
if ! command -v yt-dlp &> /dev/null; then
    echo "Error: yt-dlp is not installed"
    echo "Install with: brew install yt-dlp"
    exit 1
fi
```

### Quote All Variables

Always quote variables in commands:

```bash
# BAD - vulnerable to word splitting
yt-dlp --print "%(title)s" $URL

# GOOD - properly quoted
yt-dlp --print "%(title)s" "$URL"
```

### Avoid Sudo Unless Necessary

Prefer user-space installations:

```bash
# Prefer this
pip3 install --user yt-dlp

# Over this
sudo apt install yt-dlp
```

## Error Handling

### Check Exit Codes

```bash
if ! yt-dlp --write-sub "$URL" 2>/dev/null; then
    echo "Error: Failed to download subtitles"
    exit 1
fi
```

### Provide Helpful Messages

```bash
if [ $? -ne 0 ]; then
    echo "Error: Operation failed"
    echo "Possible causes:"
    echo "  - URL may be invalid or inaccessible"
    echo "  - Network connection issues"
    echo "  - Content may require authentication"
    exit 1
fi
```

## Content Type Verification

### Verify Expected Content

```bash
# Check Content-Type header
CONTENT_TYPE=$(curl -sI "$URL" | grep -i "Content-Type:" | head -1)

if [[ "$CONTENT_TYPE" =~ application/pdf ]]; then
    # Handle as PDF
elif [[ "$CONTENT_TYPE" =~ text/html ]]; then
    # Handle as article
else
    echo "Warning: Unexpected content type: $CONTENT_TYPE"
fi
```

## Summary Checklist

Before processing any URL:

- [ ] Validate URL protocol (http/https only)
- [ ] Block internal network access
- [ ] Sanitize any filenames derived from URL or content
- [ ] Set file size limits on downloads
- [ ] Use secure temporary files
- [ ] Quote all variables in shell commands
- [ ] Check exit codes and handle errors
- [ ] Clean up temporary files on exit
- [ ] Verify downloaded content matches expected type
