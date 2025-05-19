# MCP Screenshot Tool

A powerful AI-powered screenshot capture and image analysis tool that integrates with the Model Context Protocol (MCP) ecosystem. Designed with a flexible three-layer architecture for maximum extensibility and maintainability.

## Features

- **Screenshot Capture**: Capture full screen, specific regions, or web pages
- **AI-Powered Analysis**: Describe images using Vertex AI/Gemini models
- **Expert Verification**: Analyze visualizations with customizable AI expertise
- **Screenshot History**: Store and organize screenshots automatically
- **BM25 Text Search**: Find screenshots by content using SQLite FTS5
- **Image Similarity**: Find visually similar screenshots using perceptual hashing
- **Combined Search**: Flexible search by text content and/or visual similarity with normalized weights
- **MCP Integration**: Use as an MCP server for AI agents
- **CLI & JSON Support**: Unix-like command interface with JSON output

## Installation

```bash
# Clone the repository
git clone https://github.com/grahama1970/mcp-screenshot.git
cd mcp-screenshot

# Install with uv (recommended)
uv venv --python=3.10.11 .venv
source .venv/bin/activate
uv pip install -e .

# Or install with pip
pip install -e .
```

## Configuration

1. Create a `.env` file in the project root:
```env
VERTEX_AI_PROJECT=your-project-id
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_SERVICE_ACCOUNT_FILE=./vertex_ai_service_account.json
VERTEX_AI_MODEL=vertex_ai/gemini-2.5-flash-preview-04-17
```

2. Add your Vertex AI service account JSON file to the project root

## Quick Start

```bash
# Take a screenshot and describe it
mcp-screenshot capture
mcp-screenshot describe --file screenshot.jpg

# Verify a visualization with expert mode
mcp-screenshot verify chart.png --expert chart

# Get JSON output for scripting
mcp-screenshot --json describe --file image.jpg
```

## Command Reference

### Global Options

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--json` | | Output as JSON | `mcp-screenshot --json capture` |
| `--debug` | | Enable debug logging | `mcp-screenshot --debug capture` |
| `--help` | | Show help message | `mcp-screenshot --help` |

### capture - Screenshot Capture

Capture screenshots of screen regions or web pages.

| Option | Short | Description | Default | Example |
|--------|-------|-------------|---------|---------|
| `--url` | `-u` | URL to capture | None | `--url https://example.com` |
| `--quality` | `-q` | Image quality (30-90) | 70 | `--quality 80` |
| `--region` | `-r` | Screen region | full | `--region left-half` |
| `--output` | `-o` | Output filename | timestamped | `--output screen.jpg` |
| `--output-dir` | `-d` | Output directory | ./ | `--output-dir ./screenshots` |
| `--wait` | `-w` | Wait seconds (for URLs) | 3 | `--wait 5` |
| `--zoom-center` | `-z` | Center point for zoom (x,y) | None | `--zoom-center 640,480` |
| `--zoom-factor` | `-zf` | Zoom factor (1.0-10.0) | 1.0 | `--zoom-factor 2.0` |

**Available regions**: full, left-half, right-half, top-half, bottom-half, center

```bash
# Examples
mcp-screenshot capture                           # Full screen
mcp-screenshot capture --region left-half        # Left half of screen
mcp-screenshot capture --url https://d3js.org    # Web page
mcp-screenshot capture --output shot.jpg --quality 85

# Zoom examples
mcp-screenshot capture --zoom-center 800,600 --zoom-factor 2.0
mcp-screenshot capture --zoom-center 400,300 --zoom-factor 4.0 --output zoomed.jpg
mcp-screenshot capture --region center --zoom-center 640,360 --zoom-factor 1.5
```

### describe - AI Image Description

Get AI-powered descriptions of images.

| Option | Short | Description | Default | Example |
|--------|-------|-------------|---------|---------|
| `--url` | `-u` | URL to capture & describe | None | `--url https://example.com` |
| `--file` | `-f` | Image file to describe | None | `--file chart.png` |
| `--prompt` | `-p` | Custom prompt | "Describe this image" | `--prompt "What colors are used?"` |
| `--model` | `-m` | AI model | gemini-2.5-flash | `--model vertex_ai/gemini-2.0` |
| `--quality` | `-q` | Quality (for URLs) | 70 | `--quality 80` |

```bash
# Examples
mcp-screenshot describe --file graph.png
mcp-screenshot describe --url https://d3js.org --prompt "What type of visualization is this?"
mcp-screenshot --json describe --file chart.jpg
```

### verify - Visualization Verification

Analyze visualizations with expert modes and feature detection.

| Option | Short | Description | Default | Example |
|--------|-------|-------------|---------|---------|
| `target` | | URL or file path | Required | `chart.png` |
| `--expert` | `-e` | Expert mode | None | `--expert chart` |
| `--features` | `-f` | Expected features | None | `--features "axes,legend"` |
| `--prompt` | `-p` | Custom prompt | None | `--prompt "Analyze the color scheme"` |
| `--model` | `-m` | AI model | gemini-2.5-flash | `--model vertex_ai/gemini-2.0` |
| `--quality` | `-q` | Screenshot quality | 70 | `--quality 80` |
| `--wait` | `-w` | Wait seconds (URLs) | 3 | `--wait 5` |

**Expert modes**: d3, chart, graph, data-viz, or custom string

```bash
# Examples
mcp-screenshot verify chart.png --expert chart
mcp-screenshot verify https://d3js.org/example --expert d3 --wait 5
mcp-screenshot verify graph.jpg --features "nodes,edges,labels"
mcp-screenshot verify ui.png --prompt "As a UX expert, evaluate this interface"
```

### regions - List Screen Regions

Show available screen regions for capture.

```bash
mcp-screenshot regions
mcp-screenshot --json regions
```

### history - Screenshot History

View and manage screenshot history.

| Option | Short | Description | Default | Example |
|--------|-------|-------------|---------|---------|
| `--limit` | `-l` | Number of screenshots | 10 | `--limit 20` |
| `--region` | `-r` | Filter by region | None | `--region center` |

```bash
# Show recent screenshots
mcp-screenshot history

# Show more results
mcp-screenshot history --limit 20

# Filter by region
mcp-screenshot history --region left-half
```

### search - Search by Content

Search screenshots by text content using BM25 ranking.

| Option | Short | Description | Default | Example |
|--------|-------|-------------|---------|---------|
| `query` | | Search query | Required | `"error message"` |
| `--limit` | `-l` | Maximum results | 10 | `--limit 5` |
| `--region` | `-r` | Filter by region | None | `--region center` |
| `--from` | | Start date | None | `--from 2024-01-01` |
| `--to` | | End date | None | `--to 2024-06-30` |

```bash
# Search by content
mcp-screenshot search "login form"

# Limit results
mcp-screenshot search "dashboard" --limit 5

# Filter by date
mcp-screenshot search "chart" --from 2024-01-01 --to 2024-06-30
```

### similar - Find Similar Images

Find visually similar screenshots using perceptual hashing.

| Option | Short | Description | Default | Example |
|--------|-------|-------------|---------|---------|
| `image` | | Reference image | Required | `image.jpg` |
| `--threshold` | `-t` | Similarity threshold | 0.8 | `--threshold 0.9` |
| `--limit` | `-l` | Maximum results | 10 | `--limit 5` |
| `--region` | `-r` | Filter by region | None | `--region center` |

```bash
# Find similar images
mcp-screenshot similar reference.jpg

# Adjust similarity threshold
mcp-screenshot similar logo.png --threshold 0.9

# Limit results
mcp-screenshot similar ui.jpg --limit 5
```

### combined - Flexible Search by Text and/or Image

Search by text content and/or visual similarity with intelligent weight normalization.

| Option | Short | Description | Default | Example |
|--------|-------|-------------|---------|---------|
| `--text` | `-t` | Text to search for | None | `--text "login form"` |
| `--image` | `-i` | Reference image | None | `--image login.jpg` |
| `--text-weight` | `-tw` | Text search weight | 1.0 | `--text-weight 7` |
| `--image-weight` | `-iw` | Image search weight | 1.0 | `--image-weight 3` |
| `--limit` | `-l` | Maximum results | 10 | `--limit 5` |
| `--region` | `-r` | Filter by region | None | `--region center` |

```bash
# Combined search (text + image, equal weights)
mcp-screenshot combined --text "error message" --image error.jpg

# Text-only search
mcp-screenshot combined --text "login form"

# Image-only search 
mcp-screenshot combined --image reference.jpg

# Adjust weights (70% text, 30% image)
mcp-screenshot combined --text "dashboard" --image ui.png --text-weight 7 --image-weight 3

# For agents (get JSON output)
mcp-screenshot --json combined --text "button" --image button.png
```

### stats - History Statistics

Show screenshot history statistics.

```bash
mcp-screenshot stats
mcp-screenshot --json stats
```

### cleanup - Delete Old Screenshots

Clean up old screenshots from history.

| Option | Short | Description | Default | Example |
|--------|-------|-------------|---------|---------|
| `--days` | `-d` | Days to keep | 30 | `--days 7` |
| `--force` | `-f` | Skip confirmation | False | `--force` |

```bash
# Clean up screenshots older than 30 days
mcp-screenshot cleanup

# Clean up screenshots older than 7 days (forced)
mcp-screenshot cleanup --days 7 --force
```

### version - Show Version

Display version information.

```bash
mcp-screenshot version
```

## MCP Server Usage

Run as an MCP server for AI agent integration:

```bash
python -m mcp_screenshot.mcp.server
```

Configure in your MCP client (e.g., Claude Code):
```json
{
  "mcpServers": {
    "screenshot": {
      "command": "python",
      "args": ["-m", "mcp_screenshot.mcp.server"],
      "env": {
        "VERTEX_AI_PROJECT": "your-project-id",
        "VERTEX_AI_LOCATION": "us-central1"
      }
    }
  }
}
```

### MCP Tools Available

| Tool | Description | Parameters |
|------|-------------|------------|
| `capture_screenshot` | Capture a screenshot | quality, region, output_dir, zoom_center, zoom_factor |
| `describe_image` | Describe an image with AI | file_path, prompt, model |
| `verify_visualization` | Verify with expert mode | file_path, expert_mode, features |
| `search_screenshots` | Search screenshot history | query, limit, region, date_from, date_to |
| `find_similar_images` | Find visually similar screenshots | image_path, threshold, limit, region |
| `combined_search` | Search by text and image | text_query, image_path, text_weight, image_weight |

## History and Search

The tool automatically saves all screenshots and descriptions in a SQLite database.

```bash
# View recent history
mcp-screenshot history

# Search by content
mcp-screenshot search "error message"

# Find similar images
mcp-screenshot similar reference.jpg

# Combined search (text + image)
mcp-screenshot combined --text "login form" --image login.jpg

# Get statistics
mcp-screenshot stats

# Clean up old screenshots
mcp-screenshot cleanup --days 30
```

### Technical Details

- **Database**: SQLite with FTS5 virtual table for full-text search
- **Text Ranking**: BM25 for relevance scoring (like Elasticsearch)
- **Image Similarity**: Perceptual hashing using the ImageHash library
- **Combined Search**: Weighted combination of text and image scores with automatic normalization
- **Storage**: Files are organized in `~/.mcp_screenshot/`
  - Database: `~/.mcp_screenshot/history.db`
  - Screenshots: `~/.mcp_screenshot/screenshots/`

## Advanced Usage

### Zoom Feature

The capture command supports zooming in on specific coordinates:

- **`--zoom-center x,y`**: Specify the center point for zoom (e.g., 640,480)
- **`--zoom-factor`**: Set the zoom multiplication factor (1.0 to 10.0)

Zoom works by:
1. Capturing the full screenshot
2. Cropping around the specified center point
3. Enlarging the cropped area by the zoom factor

```bash
# Zoom 2x into the center of the screen
mcp-screenshot capture --zoom-center 640,360 --zoom-factor 2.0

# Zoom 3x into a specific UI element
mcp-screenshot capture --zoom-center 1200,400 --zoom-factor 3.0 --output ui_detail.jpg

# Combine with regions for more control
mcp-screenshot capture --region center --zoom-center 640,360 --zoom-factor 1.5
```

**Note**: Zoom is only available for screen captures, not URL captures.

### JSON Output for Scripting

```bash
# Capture and get JSON output
OUTPUT=$(mcp-screenshot --json capture)
FILE=$(echo $OUTPUT | jq -r '.file')

# Describe the captured image
mcp-screenshot --json describe --file "$FILE" | jq '.description'

# Find similar images
REFERENCE=$(mcp-screenshot --json capture | jq -r '.file')
SIMILAR=$(mcp-screenshot --json similar "$REFERENCE" | jq -r '.results[0].storage_path')

# Compare them
mcp-screenshot compare "$REFERENCE" "$SIMILAR"

# Search history
mcp-screenshot --json search "dashboard" > search_results.json
```

### Expert Mode Examples

```bash
# D3.js visualization analysis
mcp-screenshot verify d3_chart.html --expert d3 --features "axes,data-points,tooltip"

# Chart analysis
mcp-screenshot verify sales_chart.png --expert chart --features "trend-line,labels,legend"

# Custom expertise
mcp-screenshot verify ui_mockup.png --prompt "As a UI/UX expert, evaluate the visual hierarchy"
```

### Batch Processing

```bash
# Process multiple images
for img in screenshots/*.png; do
  mcp-screenshot --json describe --file "$img" > "${img%.png}_description.json"
done
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VERTEX_AI_PROJECT` | Google Cloud project ID | Required |
| `VERTEX_AI_LOCATION` | Vertex AI location | us-central1 |
| `VERTEX_AI_SERVICE_ACCOUNT_FILE` | Path to service account JSON | Required |
| `VERTEX_AI_MODEL` | AI model to use | vertex_ai/gemini-2.5-flash-preview-04-17 |
| `MAX_WIDTH` | Max image width for AI | 1280 |
| `MAX_HEIGHT` | Max image height for AI | 1024 |
| `DEFAULT_QUALITY` | Default JPEG quality | 70 |

## Three-Layer Architecture

This project follows a strict three-layer architecture:

### 1. Core Layer (`src/mcp_screenshot/core/`)
- Pure business logic
- No UI or integration dependencies
- Screenshot capture, image processing, AI analysis
- History storage and search (SQLite, BM25, perceptual hashing)

### 2. CLI Layer (`src/mcp_screenshot/cli/`)
- Command-line interface
- Rich formatting and user interaction
- Depends only on Core layer

### 3. MCP Layer (`src/mcp_screenshot/mcp/`)
- MCP server implementation
- Protocol-specific wrappers
- Depends on Core layer

## Requirements

- Python 3.10+
- Google Cloud account with Vertex AI enabled
- Service account with Vertex AI permissions
- Display environment for screen capture (optional for file operations)

## Troubleshooting

### Common Issues

1. **"$DISPLAY not set" error**
   - This occurs in headless environments
   - Use file-based operations or web capture instead
   - Consider using Xvfb for headless screen capture

2. **"No module named 'google'" error**
   - Install Google Cloud dependencies: `pip install google-cloud-aiplatform`

3. **Authentication errors**
   - Ensure service account JSON has Vertex AI permissions
   - Check VERTEX_AI_PROJECT environment variable

4. **Image too large errors**
   - Images are automatically resized to MAX_WIDTH/MAX_HEIGHT
   - Adjust quality settings with `--quality` flag

## License

MIT License - see LICENSE file for details

## Contributing

1. Follow the three-layer architecture
2. Add tests for all new features
3. Update documentation for CLI changes
4. Ensure all commands have JSON output support

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/grahama1970/mcp-screenshot).