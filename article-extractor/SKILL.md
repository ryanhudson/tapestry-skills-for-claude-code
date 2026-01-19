---
name: article-extractor
description: This skill should be used when the user wants to "download article", "extract article", "save blog post", "get article text", or provides a web URL and asks to extract the main content without ads, navigation, or clutter. Saves clean, readable text from web articles and blog posts.
allowed-tools: Bash,Read,Write
---

# Article Extractor

Extract main content from web articles and blog posts, removing navigation, ads, and clutter. Saves clean, readable text.

## Workflow

```
URL → Validate → Detect Tool → Extract Content → Sanitize Filename → Save
```

**Tools (in priority order)**:
1. `reader` (Mozilla Readability) - best for most articles
2. `trafilatura` - excellent for blogs/news
3. Fallback (curl + basic parsing) - works without dependencies

## Security Requirements

### URL Validation

```bash
# Validate protocol
if [[ ! "$URL" =~ ^https?:// ]]; then
    echo "Error: Only HTTP/HTTPS URLs are supported"
    exit 1
fi

# Block internal networks (SSRF protection)
if [[ "$URL" =~ ^https?://(localhost|127\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.) ]]; then
    echo "Error: Internal network URLs are not allowed"
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

## Step 1: Check Available Tools

```bash
if command -v reader &> /dev/null; then
    TOOL="reader"
elif command -v trafilatura &> /dev/null; then
    TOOL="trafilatura"
else
    TOOL="fallback"
fi

echo "Using: $TOOL"
```

### Installation Commands

**reader** (recommended):
```bash
npm install -g @aspect/readability-cli
# or
npm install -g reader-cli
```

**trafilatura**:
```bash
pip3 install --user trafilatura
```

## Step 2: Extract Content

### Using reader

```bash
TEMP_FILE=$(mktemp)
trap "rm -f '$TEMP_FILE'" EXIT

reader "$URL" > "$TEMP_FILE"

# Get title (first line in markdown format)
TITLE=$(head -n 1 "$TEMP_FILE" | sed 's/^# //')
```

### Using trafilatura

```bash
TEMP_FILE=$(mktemp)
trap "rm -f '$TEMP_FILE'" EXIT

# Get content
trafilatura --URL "$URL" --output-format txt --no-comments > "$TEMP_FILE"

# Get title from metadata
TITLE=$(trafilatura --URL "$URL" --json 2>/dev/null | \
    python3 -c "import json,sys; print(json.load(sys.stdin).get('title','Article'))" 2>/dev/null || echo "Article")
```

### Fallback Method

```bash
TEMP_FILE=$(mktemp)
trap "rm -f '$TEMP_FILE'" EXIT

# Get title from HTML
TITLE=$(curl -s --max-time 30 "$URL" | grep -oP '<title>\K[^<]+' | head -n 1)
TITLE=${TITLE%% - *}  # Remove site name suffix
TITLE=${TITLE%% | *}

# Extract content
curl -s --max-time 30 "$URL" | python3 -c "
from html.parser import HTMLParser
import sys

class Extractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.content = []
        self.skip = {'script', 'style', 'nav', 'header', 'footer', 'aside', 'form'}
        self.capture = False

    def handle_starttag(self, tag, attrs):
        if tag not in self.skip and tag in {'p', 'article', 'main'}:
            self.capture = True
        if tag in {'h1', 'h2', 'h3'}:
            self.content.append('')

    def handle_endtag(self, tag):
        if tag in {'p', 'article', 'main'}:
            self.capture = False

    def handle_data(self, data):
        if self.capture and data.strip():
            self.content.append(data.strip())

    def get_content(self):
        return '\n\n'.join(self.content)

p = Extractor()
p.feed(sys.stdin.read())
print(p.get_content())
" > "$TEMP_FILE"
```

## Step 3: Save with Clean Filename

```bash
SAFE_TITLE=$(sanitize_filename "$TITLE")
CONTENT_FILE="${SAFE_TITLE}.txt"

# Verify content was extracted
if [ ! -s "$TEMP_FILE" ]; then
    echo "Error: No content extracted"
    exit 1
fi

mv "$TEMP_FILE" "$CONTENT_FILE"
trap - EXIT

WORD_COUNT=$(wc -w < "$CONTENT_FILE" | tr -d ' ')

echo "Extracted: $TITLE"
echo "Saved to: $CONTENT_FILE"
echo "Words: $WORD_COUNT"
```

## Complete Workflow Script

```bash
#!/bin/bash
set -e

URL="$1"

# Validate URL
if [[ ! "$URL" =~ ^https?:// ]]; then
    echo "Error: Only HTTP/HTTPS URLs are supported"
    exit 1
fi

if [[ "$URL" =~ ^https?://(localhost|127\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.) ]]; then
    echo "Error: Internal network URLs not allowed"
    exit 1
fi

# Sanitization function
sanitize_filename() {
    echo "$1" | tr -d '\0' | tr '/' '_' | tr ':' '-' | tr '\\' '_' | \
        tr -d '?*"<>|`$'"'" | sed 's/\.\.//g' | cut -c 1-100
}

# Detect tool
if command -v reader &> /dev/null; then
    TOOL="reader"
elif command -v trafilatura &> /dev/null; then
    TOOL="trafilatura"
else
    TOOL="fallback"
fi

echo "Extracting with: $TOOL"

# Create temp file
TEMP_FILE=$(mktemp)
trap "rm -f '$TEMP_FILE'" EXIT

# Extract based on tool
case $TOOL in
    reader)
        reader "$URL" > "$TEMP_FILE"
        TITLE=$(head -n 1 "$TEMP_FILE" | sed 's/^# //')
        ;;
    trafilatura)
        trafilatura --URL "$URL" --output-format txt --no-comments > "$TEMP_FILE"
        TITLE=$(trafilatura --URL "$URL" --json 2>/dev/null | \
            python3 -c "import json,sys; print(json.load(sys.stdin).get('title','Article'))" 2>/dev/null || echo "Article")
        ;;
    fallback)
        TITLE=$(curl -s --max-time 30 "$URL" | grep -oP '<title>\K[^<]+' | head -n 1)
        TITLE=${TITLE%% - *}
        # See "Fallback Method" section above for full extraction code
        curl -s --max-time 30 "$URL" | python3 -c "
from html.parser import HTMLParser
import sys
class E(HTMLParser):
    def __init__(self):
        super().__init__()
        self.c=[]
        self.s={'script','style','nav','header','footer','aside','form'}
        self.cap=False
    def handle_starttag(self,t,a):
        if t not in self.s and t in {'p','article','main'}: self.cap=True
    def handle_data(self,d):
        if self.cap and d.strip(): self.c.append(d.strip())
    def get(self): return '\n\n'.join(self.c)
p=E(); p.feed(sys.stdin.read()); print(p.get())
" > "$TEMP_FILE"
        ;;
esac

# Verify extraction
if [ ! -s "$TEMP_FILE" ]; then
    echo "Error: No content extracted. Site may require authentication."
    exit 1
fi

# Save with clean filename
SAFE_TITLE=$(sanitize_filename "$TITLE")
CONTENT_FILE="${SAFE_TITLE}.txt"
mv "$TEMP_FILE" "$CONTENT_FILE"
trap - EXIT

# Show results
WORD_COUNT=$(wc -w < "$CONTENT_FILE" | tr -d ' ')
echo ""
echo "Extracted: $TITLE"
echo "Saved to: $CONTENT_FILE"
echo "Words: $WORD_COUNT"
echo ""
echo "Preview:"
head -n 10 "$CONTENT_FILE"
```

## Error Handling

| Issue | Solution |
|-------|----------|
| Invalid URL | Reject with clear message |
| Internal URL (SSRF) | Block localhost/private IPs |
| Paywall/login required | Inform user, cannot extract |
| No tool available | Use fallback method |
| Empty extraction | Try alternate tool, inform user |
| Timeout | Set `--max-time 30` on curl |

## What Gets Extracted

**Included**:
- Article title
- Author (if available)
- Main text content
- Section headings

**Removed**:
- Navigation menus
- Ads and promotions
- Newsletter signups
- Related articles
- Comment sections
- Social buttons
- Cookie notices

## Tool Comparison

| Tool | Strengths | Install |
|------|-----------|---------|
| reader | Best overall, Firefox algorithm | `npm install -g reader-cli` |
| trafilatura | News/blogs, multi-language | `pip3 install trafilatura` |
| fallback | No dependencies | Built-in |

## Dependencies

- **reader** OR **trafilatura**: Recommended (better extraction)
- **curl**: Required for fallback
- **Python 3**: Required for fallback parsing

## Security Reference

For complete security guidelines: `../shared/references/security-guidelines.md`
