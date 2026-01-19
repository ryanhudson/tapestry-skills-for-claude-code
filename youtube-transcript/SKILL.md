---
name: youtube-transcript
description: This skill should be used when the user provides a YouTube URL and wants to "download transcript", "get captions", "get subtitles", "transcribe video", or extract text content from a YouTube video. Handles manual subtitles, auto-generated captions, and Whisper transcription as fallback.
allowed-tools: Bash,Read,Write
---

# YouTube Transcript Downloader

Extract transcripts from YouTube videos using yt-dlp. Supports manual subtitles, auto-generated captions, and Whisper transcription as a last resort.

## Workflow

```
URL → Validate → Check yt-dlp → List Subtitles → Download → Convert to Text → Save
```

**Priority order**:
1. Manual subtitles (highest quality)
2. Auto-generated captions (usually available)
3. Whisper transcription (requires user consent)

## Security Requirements

### URL Validation

```bash
# Only accept YouTube URLs
if [[ ! "$URL" =~ ^https?://(www\.)?(youtube\.com|youtu\.be)/ ]]; then
    echo "Error: Not a valid YouTube URL"
    exit 1
fi
```

### Filename Sanitization

```bash
sanitize_filename() {
    echo "$1" | \
        tr -d '\0' | \
        tr '/' '_' | \
        tr ':' '-' | \
        tr '\\' '_' | \
        tr -d '?*"<>|`$'"'" | \
        sed 's/\.\.//g' | \
        sed 's/^[. ]*//' | \
        sed 's/[. ]*$//' | \
        cut -c 1-100
}
```

## Step 1: Check yt-dlp Installation

```bash
if ! command -v yt-dlp &> /dev/null; then
    echo "yt-dlp not found. Installing..."
    if command -v brew &> /dev/null; then
        brew install yt-dlp
    else
        pip3 install --user yt-dlp
    fi
fi
```

**Avoid sudo** - prefer user-space installation with `pip3 install --user`.

## Step 2: Check Available Subtitles

Always check what's available first:

```bash
yt-dlp --list-subs "$URL"
```

Look for:
- `Available subtitles` (manual, higher quality)
- `Available automatic captions` (auto-generated)

## Step 3: Download Subtitles

### Try Manual First

```bash
TEMP_DIR=$(mktemp -d)
trap "rm -rf '$TEMP_DIR'" EXIT

if yt-dlp --write-sub --skip-download --sub-langs en -o "$TEMP_DIR/transcript" "$URL" 2>/dev/null; then
    echo "Downloaded manual subtitles"
else
    # Fall back to auto-generated
    yt-dlp --write-auto-sub --skip-download --sub-langs en -o "$TEMP_DIR/transcript" "$URL"
    echo "Downloaded auto-generated captions"
fi
```

## Step 4: Convert VTT to Clean Text

YouTube auto-generated VTT files contain duplicates due to progressive caption display. Always deduplicate:

```bash
VIDEO_TITLE=$(yt-dlp --print "%(title)s" "$URL" 2>/dev/null)
SAFE_TITLE=$(sanitize_filename "$VIDEO_TITLE")

VTT_FILE=$(find "$TEMP_DIR" -name "*.vtt" | head -n 1)

python3 -c "
import sys, re
seen = set()
with open('$VTT_FILE', 'r') as f:
    for line in f:
        line = line.strip()
        # Skip VTT metadata and timestamps
        if not line or line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:') or '-->' in line:
            continue
        # Remove HTML tags
        clean = re.sub('<[^>]*>', '', line)
        # Decode entities
        clean = clean.replace('&amp;', '&').replace('&gt;', '>').replace('&lt;', '<')
        # Deduplicate
        if clean and clean not in seen:
            print(clean)
            seen.add(clean)
" > "${SAFE_TITLE}.txt"

echo "Saved: ${SAFE_TITLE}.txt"
```

## Whisper Transcription (Last Resort)

**Only offer when no subtitles are available. Requires explicit user consent.**

### Check File Size First

```bash
DURATION=$(yt-dlp --print "%(duration)s" "$URL" 2>/dev/null)
TITLE=$(yt-dlp --print "%(title)s" "$URL" 2>/dev/null)

echo "No subtitles available for: $TITLE"
echo "Duration: $((DURATION / 60)) minutes"
echo ""
echo "Download audio and transcribe with Whisper? (requires ~1-3GB for model)"
echo "Type 'yes' to proceed:"
```

**Wait for explicit "yes" before proceeding.**

### Install Whisper (with consent)

```bash
if ! command -v whisper &> /dev/null; then
    echo "Whisper not installed. Install now? (y/n)"
    read -r RESPONSE
    if [[ "$RESPONSE" =~ ^[Yy]$ ]]; then
        pip3 install --user openai-whisper
    else
        echo "Cannot proceed without Whisper"
        exit 1
    fi
fi
```

### Download and Transcribe

```bash
TEMP_DIR=$(mktemp -d)
trap "rm -rf '$TEMP_DIR'" EXIT

# Download audio only
yt-dlp -x --audio-format mp3 -o "$TEMP_DIR/audio.%(ext)s" "$URL"

# Transcribe with base model (good balance of speed/accuracy)
whisper "$TEMP_DIR/audio.mp3" --model base --output_format vtt --output_dir "$TEMP_DIR"

# Convert to text (same process as above)
# ...
```

## Complete Workflow Script

```bash
#!/bin/bash
set -e

URL="$1"

# Validate URL
if [[ ! "$URL" =~ ^https?://(www\.)?(youtube\.com|youtu\.be)/ ]]; then
    echo "Error: Not a valid YouTube URL"
    exit 1
fi

# Sanitization function
sanitize_filename() {
    echo "$1" | tr -d '\0' | tr '/' '_' | tr ':' '-' | tr '\\' '_' | \
        tr -d '?*"<>|`$'"'" | sed 's/\.\.//g' | cut -c 1-100
}

# Check yt-dlp
if ! command -v yt-dlp &> /dev/null; then
    echo "Installing yt-dlp..."
    pip3 install --user yt-dlp || { echo "Failed to install yt-dlp"; exit 1; }
fi

# Get video info
VIDEO_TITLE=$(yt-dlp --print "%(title)s" "$URL" 2>/dev/null)
SAFE_TITLE=$(sanitize_filename "$VIDEO_TITLE")

echo "Video: $VIDEO_TITLE"
echo ""

# Create temp directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf '$TEMP_DIR'" EXIT

# Try to download subtitles
echo "Checking for subtitles..."
if yt-dlp --write-sub --skip-download --sub-langs en -o "$TEMP_DIR/transcript" "$URL" 2>/dev/null; then
    echo "Found manual subtitles"
elif yt-dlp --write-auto-sub --skip-download --sub-langs en -o "$TEMP_DIR/transcript" "$URL" 2>/dev/null; then
    echo "Found auto-generated captions"
else
    echo "No subtitles available"
    # Offer Whisper option here (with user consent)
    exit 1
fi

# Find VTT file
VTT_FILE=$(find "$TEMP_DIR" -name "*.vtt" | head -n 1)

if [ -z "$VTT_FILE" ]; then
    echo "Error: No VTT file found"
    exit 1
fi

# Convert to clean text
python3 -c "
import sys, re
seen = set()
with open('$VTT_FILE', 'r') as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:') or '-->' in line:
            continue
        clean = re.sub('<[^>]*>', '', line)
        clean = clean.replace('&amp;', '&').replace('&gt;', '>').replace('&lt;', '<')
        if clean and clean not in seen:
            print(clean)
            seen.add(clean)
" > "${SAFE_TITLE}.txt"

WORD_COUNT=$(wc -w < "${SAFE_TITLE}.txt" | tr -d ' ')

echo ""
echo "Transcript saved: ${SAFE_TITLE}.txt"
echo "Words: $WORD_COUNT"
```

## Error Handling

| Issue | Solution |
|-------|----------|
| yt-dlp not installed | Auto-install via pip3 (user-space) |
| Invalid URL | Reject non-YouTube URLs |
| No subtitles | Offer Whisper with user consent |
| Private/restricted video | Inform user, cannot access |
| SSL errors | Try `--no-check-certificate` (with warning) |
| Download timeout | Retry or inform user |

## Output Options

- **VTT format** (`.vtt`): With timestamps, for video players
- **Plain text** (`.txt`): Clean text, recommended for reading/analysis

## Dependencies

- **yt-dlp**: Primary tool (auto-installed)
- **Python 3**: For VTT conversion
- **Whisper** (optional): For videos without subtitles
- **ffmpeg** (optional): Required by Whisper for audio processing

## Security Reference

For complete security guidelines: `../shared/references/security-guidelines.md`
