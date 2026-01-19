---
name: tapestry
description: This skill should be used when the user says "tapestry <URL>", "weave <URL>", "help me plan <URL>", "extract and plan <URL>", "make this actionable <URL>", or wants to extract content from a URL and create an action plan. Automatically detects content type (YouTube video, article, PDF) and orchestrates the full extract-to-plan workflow.
allowed-tools: Bash,Read,Write
---

# Tapestry: Unified Content Extraction + Action Planning

Master skill that orchestrates the entire Tapestry workflow:
1. Detect content type from URL
2. Extract content using appropriate method
3. Create a Ship-Learn-Next action plan automatically

## Workflow Overview

```
URL → Validate → Detect Type → Extract Content → Create Plan → Save Files
```

**Output**: Two files saved:
- Content file: `[Title].txt`
- Plan file: `Ship-Learn-Next Plan - [Quest].md`

## Security Requirements

**CRITICAL**: Before processing ANY URL, validate it first using the shared security scripts.

Use the shared security scripts located in `../shared/scripts/`:

### URL Validation (Required)

```bash
URL="$1"

# Run security validation (checks protocol, blocks SSRF, etc.)
../shared/scripts/validate-url.sh "$URL" || exit 1
```

### Filename Sanitization (Required)

```bash
# Use shared sanitization script for all titles
SAFE_TITLE=$(../shared/scripts/sanitize-filename.sh "$TITLE")
```

## Step 1: Detect Content Type

```bash
detect_content_type() {
    local URL="$1"

    # YouTube patterns
    if [[ "$URL" =~ youtube\.com/watch || "$URL" =~ youtu\.be/ || "$URL" =~ youtube\.com/shorts ]]; then
        echo "youtube"
        return
    fi

    # PDF by extension
    if [[ "$URL" =~ \.pdf($|\?) ]]; then
        echo "pdf"
        return
    fi

    # PDF by Content-Type header
    if curl -sI --max-time 10 "$URL" | grep -iq "Content-Type:.*application/pdf"; then
        echo "pdf"
        return
    fi

    # Default to article
    echo "article"
}

CONTENT_TYPE=$(detect_content_type "$URL")
echo "Detected: $CONTENT_TYPE"
```

## Step 2: Extract Content

### YouTube Extraction

Use the youtube-transcript skill workflow:

```bash
# Check yt-dlp
if ! command -v yt-dlp &> /dev/null; then
    echo "Installing yt-dlp..."
    brew install yt-dlp || pip3 install yt-dlp
fi

# Get and sanitize title
VIDEO_TITLE=$(yt-dlp --print "%(title)s" "$URL" 2>/dev/null)
SAFE_TITLE=$(../shared/scripts/sanitize-filename.sh "$VIDEO_TITLE")

# Create temp file
TEMP_VTT=$(mktemp)
trap "rm -f '$TEMP_VTT'" EXIT

# Download transcript (try manual first, then auto-generated)
if ! yt-dlp --write-sub --skip-download --sub-langs en -o "$TEMP_VTT" "$URL" 2>/dev/null; then
    yt-dlp --write-auto-sub --skip-download --sub-langs en -o "$TEMP_VTT" "$URL"
fi

# Convert VTT to clean text (deduplicate)
python3 -c "
import sys, re
seen = set()
for line in sys.stdin:
    line = line.strip()
    if line and not line.startswith('WEBVTT') and '-->' not in line:
        clean = re.sub('<[^>]*>', '', line)
        clean = clean.replace('&amp;', '&').replace('&gt;', '>').replace('&lt;', '<')
        if clean and clean not in seen:
            print(clean)
            seen.add(clean)
" < "${TEMP_VTT}.en.vtt" > "${SAFE_TITLE}.txt"

CONTENT_FILE="${SAFE_TITLE}.txt"
```

### Article Extraction

Use the article-extractor skill workflow:

```bash
# Check for extraction tools
if command -v reader &> /dev/null; then
    TOOL="reader"
elif command -v trafilatura &> /dev/null; then
    TOOL="trafilatura"
else
    TOOL="fallback"
fi

TEMP_FILE=$(mktemp)
trap "rm -f '$TEMP_FILE'" EXIT

case $TOOL in
    reader)
        reader "$URL" > "$TEMP_FILE"
        TITLE=$(head -n 1 "$TEMP_FILE" | sed 's/^# //')
        ;;
    trafilatura)
        trafilatura --URL "$URL" --output-format txt --no-comments > "$TEMP_FILE"
        TITLE=$(trafilatura --URL "$URL" --json 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin).get('title','Article'))" 2>/dev/null || echo "Article")
        ;;
    fallback)
        TITLE=$(curl -s --max-time 30 "$URL" | grep -oP '<title>\K[^<]+' | head -n 1)
        curl -s --max-time 30 "$URL" | python3 -c "
from html.parser import HTMLParser
import sys

class Extractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.content = []
        self.skip = {'script','style','nav','header','footer','aside'}
        self.capture = False
    def handle_starttag(self, tag, attrs):
        self.capture = tag in {'p','article','main'} and tag not in self.skip
    def handle_data(self, data):
        if self.capture and data.strip():
            self.content.append(data.strip())
    def get(self):
        return '\n\n'.join(self.content)

p = Extractor()
p.feed(sys.stdin.read())
print(p.get())
" > "$TEMP_FILE"
        ;;
esac

SAFE_TITLE=$(../shared/scripts/sanitize-filename.sh "$TITLE")
CONTENT_FILE="${SAFE_TITLE}.txt"
mv "$TEMP_FILE" "$CONTENT_FILE"
trap - EXIT
```

### PDF Extraction

```bash
# Sanitize filename from URL
URL_BASENAME=$(basename "$URL" | cut -d'?' -f1)
SAFE_PDF=$(../shared/scripts/sanitize-filename.sh "$URL_BASENAME")

# Ensure .pdf extension
[[ "$SAFE_PDF" != *.pdf ]] && SAFE_PDF="${SAFE_PDF}.pdf"

# Download with size limit (100MB)
curl \
    --silent \
    --show-error \
    --location \
    --max-redirs 5 \
    --max-filesize 104857600 \
    --max-time 300 \
    --output "$SAFE_PDF" \
    "$URL"

# Verify it's actually a PDF
if ! head -c 4 "$SAFE_PDF" | grep -q '%PDF'; then
    echo "Error: Downloaded file is not a valid PDF"
    rm -f "$SAFE_PDF"
    exit 1
fi

# Extract text if pdftotext available
if command -v pdftotext &> /dev/null; then
    CONTENT_FILE="${SAFE_PDF%.pdf}.txt"
    pdftotext "$SAFE_PDF" "$CONTENT_FILE"
    echo "Extracted text to: $CONTENT_FILE"
else
    echo "Note: pdftotext not found. Install with: brew install poppler"
    CONTENT_FILE="$SAFE_PDF"
fi
```

## Step 3: Create Action Plan

After extracting content, invoke the ship-learn-next skill logic:

1. Read the extracted content file
2. Extract 3-5 core actionable lessons
3. Define a specific 4-8 week quest
4. Design Rep 1 (shippable this week)
5. Outline Reps 2-5 (progressive iterations)
6. Save as: `Ship-Learn-Next Plan - [Quest Title].md`

**Key points**:
- Focus on actionable lessons, not summaries
- Rep 1 must be completable in 1-7 days
- Each rep produces real artifacts
- Emphasize doing over studying

## Step 4: Present Results

```
Tapestry Workflow Complete!

Content Extracted:
  Type: [youtube/article/pdf]
  Title: [Title]
  Saved to: [filename.txt]
  Words: [X]

Action Plan Created:
  Quest: [Quest title]
  Saved to: Ship-Learn-Next Plan - [Title].md

Rep 1 (This Week): [Rep 1 goal]

When will you ship Rep 1?
```

## Error Handling

| Issue | Action |
|-------|--------|
| Invalid URL | Reject with clear message |
| No subtitles (YouTube) | Offer Whisper transcription (with consent) |
| Paywall/login required | Inform user, cannot extract |
| Tools not installed | Auto-install or provide instructions |
| Download failed | Check URL, retry, inform user |
| Empty extraction | Verify before planning, don't create empty plan |

## Dependencies

**YouTube**: yt-dlp, Python 3
**Articles**: reader (npm) OR trafilatura (pip) OR curl (fallback)
**PDFs**: curl, pdftotext (optional, from poppler)
**Planning**: No additional requirements

## Security Reference

For detailed security guidelines, see: `../shared/references/security-guidelines.md`

Key requirements:
- Validate all URLs before processing
- Sanitize all filenames
- Use temp files with cleanup traps
- Set download size limits
- Quote all variables in shell commands
