# Tapestry Skills for Claude Code

A collection of productivity skills for [Claude Code](https://claude.com/claude-code) that help you work faster and learn better.

**Tapestry weaves learning content into action.** Extract any content (YouTube, articles, PDFs) and automatically create implementation plans.

## Requirements

- **[UV](https://docs.astral.sh/uv/)** - Fast Python package manager (required)
- **Python 3.10+** - UV will manage this for you

Install UV:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# or
brew install uv
```

## Skills Included

### 0. Tapestry (Master Skill)
The unified workflow that orchestrates everything. Just say `tapestry <URL>` and it:
1. Detects content type (YouTube, article, PDF)
2. Extracts clean content
3. Automatically creates a Ship-Learn-Next action plan

**One command. Complete workflow. From learning to shipping.**

### 1. YouTube Transcript Downloader
Download and clean YouTube video transcripts with automatic deduplication and readable formatting.

**Features:**
- Downloads transcripts using yt-dlp (pinned version via UV)
- Removes duplicate lines (YouTube VTT format issue)
- Uses video title for filename
- Fallback to Whisper transcription if no subtitles available
- Automatic cleanup of temporary files

### 2. Article Extractor
Extract clean, readable content from web articles and blog posts, removing ads, navigation, and clutter.

**Features:**
- Uses Mozilla Readability or trafilatura for extraction
- Removes ads, navigation, and newsletter signups
- Saves as clean plain text
- Uses article title for filename
- Built-in fallback extractor when external tools unavailable

### 3. Ship-Learn-Next Action Planner
Transform passive learning content (transcripts, articles, tutorials) into actionable implementation plans using the Ship-Learn-Next framework.

**Features:**
- Converts advice into concrete, shippable iterations (reps)
- Creates 5-rep action plans with timelines
- Focuses on DOING over studying
- Includes reflection questions after each rep

## Installation

### Plugin Install (Recommended)

```bash
# Install directly as a Claude Code plugin
claude /install-plugin https://github.com/ryanhudson/tapestry-skills-for-claude-code
```

### Script Install (Alternative)

```bash
# Clone the repository
git clone https://github.com/ryanhudson/tapestry-skills-for-claude-code.git

# Run the installation script
cd tapestry-skills-for-claude-code
chmod +x install.sh
./install.sh
```

The installer will:
1. Check for UV (offer to install if missing)
2. Verify Python 3.10+
3. Install all dependencies via `uv sync`
4. Verify the utilities work
5. Symlink skills to `~/.claude/skills/`

### Manual Installation

```bash
# 1. Clone and enter directory
git clone https://github.com/yourusername/tapestry-skills-for-claude-code.git
cd tapestry-skills-for-claude-code

# 2. Install dependencies
uv sync

# 3. Verify installation
uv run tapestry-validate-url https://example.com
uv run tapestry-sanitize-filename "Test: File/Name"

# 4. Symlink skills to Claude (or use plugin install)
mkdir -p ~/.claude/skills
ln -sfn "$(pwd)/skills/tapestry" ~/.claude/skills/tapestry
ln -sfn "$(pwd)/skills/youtube-transcript" ~/.claude/skills/youtube-transcript
ln -sfn "$(pwd)/skills/article-extractor" ~/.claude/skills/article-extractor
ln -sfn "$(pwd)/skills/ship-learn-next" ~/.claude/skills/ship-learn-next

# OR install as a plugin:
# claude /install-plugin https://github.com/ryanhudson/tapestry-skills-for-claude-code
```

## Usage

### Tapestry (Recommended - Use This!)

The simplest way to use Tapestry skills. One command extracts content and creates your action plan:

```
"tapestry https://www.youtube.com/watch?v=VIDEO_ID"
"weave https://example.com/article"
"help me plan https://example.com/paper.pdf"
"make this actionable https://blog.com/post"
```

**All these phrases work**: tapestry, weave, help me plan, extract and plan, make this actionable

The skill will:
1. Detect content type (YouTube/article/PDF)
2. Extract clean content
3. Create a Ship-Learn-Next action plan automatically
4. Save both files
5. Ask: "When will you ship Rep 1?"

### YouTube Transcript Downloader

```
"Download the transcript for https://www.youtube.com/watch?v=VIDEO_ID"
```

### Article Extractor

```
"Extract the article from https://example.com/blog-post"
"Download this article without the ads"
```

### Ship-Learn-Next Action Planner

```
"Turn this transcript into an implementation plan"
"Make this actionable using the Ship-Learn-Next framework"
```

## Built-in Utilities

All utilities are available via `uv run` from the project root:

| Utility | Description |
|---------|-------------|
| `tapestry-validate-url` | URL validation with SSRF protection |
| `tapestry-sanitize-filename` | Safe filename generation |
| `tapestry-safe-download` | Secure file downloads with size limits |
| `tapestry-vtt-to-text` | VTT subtitle to plain text conversion |
| `tapestry-extract-html` | Fallback HTML content extractor |

Example:
```bash
uv run tapestry-validate-url "https://example.com"
uv run tapestry-sanitize-filename "My: Unsafe/Filename"
uv run tapestry-vtt-to-text captions.vtt --output transcript.txt
```

## Dependencies

All Python dependencies are managed via UV and pinned in `pyproject.toml`:

| Package | Purpose |
|---------|---------|
| `yt-dlp` | YouTube video/transcript downloads |
| `trafilatura` | Article extraction |
| `openai-whisper` (optional) | Transcription for videos without subtitles |

**Optional system tools** (install separately for best results):
- `reader` - Mozilla Readability CLI (`npm install -g reader-cli`)
- `pdftotext` - PDF text extraction (`brew install poppler`)

## Examples

### Example 1: Tapestry Unified Workflow

```
User: "tapestry https://www.youtube.com/watch?v=dQw4w9WgXcQ"

Claude:
Tapestry Workflow Starting...
Detected: youtube
Extracting YouTube transcript...
Saved transcript: Never Gonna Give You Up.txt

Creating action plan...
Quest: Master Video Production Techniques
Saved plan: Ship-Learn-Next Plan - Master Video Production.md

Tapestry Complete!
Content: Never Gonna Give You Up.txt
Plan: Ship-Learn-Next Plan - Master Video Production.md

Rep 1 (This Week): Film and edit a 60-second video
When will you ship Rep 1?
```

### Example 2: Download YouTube Transcript

```
User: "Download transcript for https://www.youtube.com/watch?v=VIDEO_ID"

Claude:
Checked available subtitles
Downloaded auto-generated transcript
Converted to readable format
Removed duplicate lines
Saved to: Video Title.txt
```

### Example 3: Extract Article

```
User: "Extract https://example.com/how-to-build-saas"

Claude:
Using trafilatura for extraction
Extracted article: How to Build a SaaS in 30 Days
Saved to: How to Build a SaaS in 30 Days.txt

Preview (first 10 lines):
[Clean article text without ads or navigation...]
```

## Philosophy

These skills are built on the principle that **learning = doing better, not knowing more**.

### Ship-Learn-Next Framework
- **Ship**: Create something real (code, content, product)
- **Learn**: Honest reflection on what happened
- **Next**: Plan the next iteration based on learnings

100 reps beats 100 hours of study.

## Project Structure

```
tapestry-skills-for-claude-code/
├── plugin.json             # Claude Code plugin manifest
├── pyproject.toml          # Dependencies (UV/pip)
├── src/tapestry/           # Python utilities
│   ├── validate_url.py
│   ├── sanitize_filename.py
│   ├── safe_download.py
│   ├── vtt_to_text.py
│   └── html_extractor.py
├── skills/                 # Claude Code skills
│   ├── tapestry/           # Master skill
│   ├── youtube-transcript/ # YouTube extraction skill
│   ├── article-extractor/  # Article extraction skill
│   └── ship-learn-next/    # Action planning skill
├── tests/                  # Test suite
├── shared/references/      # Security documentation
└── install.sh              # Installation script
```

## Contributing

Found a bug or want to add a feature? Contributions are welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-skill`)
3. Commit your changes (`git commit -m 'Add amazing skill'`)
4. Push to the branch (`git push origin feature/amazing-skill`)
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details

## Acknowledgments

- **UV**: Fast Python package management from Astral
- **Ship-Learn-Next framework**: Inspired by the ShipLearnNext GPT methodology
- **yt-dlp**: Excellent tool for downloading YouTube content
- **OpenAI Whisper**: State-of-the-art speech recognition
- **Mozilla Readability**: Clean article extraction algorithm
- **trafilatura**: Python web scraping and content extraction

## Support

Having issues? Please [open an issue](https://github.com/yourusername/tapestry-skills-for-claude-code/issues) on GitHub.

---

**Made with Claude Code**

Learn more about Claude Code at [claude.com/claude-code](https://claude.com/claude-code)
