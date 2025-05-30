# Text Extraction Examples with mcp-screenshot

The tool already supports advanced text extraction using AI vision models. Here are practical examples:

## Basic Text Extraction

```bash
# Extract all visible text
mcp-screenshot describe --file screenshot.jpg --prompt "Extract all text from this image"

# Extract text from a specific region
mcp-screenshot describe --region right_half --prompt "Extract all text visible in this region"
```

## Structured Text Extraction

```bash
# Extract form data
mcp-screenshot describe --file form.jpg --prompt "List all form fields and their labels in JSON format"

# Extract table data
mcp-screenshot describe --file table.jpg --prompt "Extract the table data and format it as CSV"

# Extract menu items
mcp-screenshot describe --file menu.jpg --prompt "List all menu items and their keyboard shortcuts"
```

## Contextual Text Extraction

```bash
# Extract error messages
mcp-screenshot describe --file error_dialog.jpg --prompt "What error messages are displayed? Include any error codes"

# Extract button text
mcp-screenshot describe --file ui.jpg --prompt "List all clickable button text in order of visual prominence"

# Extract status information
mcp-screenshot describe --file dashboard.jpg --prompt "Extract all status indicators and their current values"
```

## Advanced Text Analysis

```bash
# Extract and translate
mcp-screenshot describe --file japanese_ui.jpg --prompt "Extract all Japanese text and provide English translations"

# Extract with positional info
mcp-screenshot describe --file layout.jpg --prompt "Extract all text with their approximate positions (top/bottom, left/right)"

# Extract and categorize
mcp-screenshot describe --file app.jpg --prompt "Extract all text and categorize it as: headers, body text, buttons, labels, or status messages"
```

## Code and Technical Text

```bash
# Extract code snippets
mcp-screenshot describe --file ide.jpg --prompt "Extract any visible code and identify the programming language"

# Extract terminal output
mcp-screenshot describe --file terminal.jpg --prompt "Extract the command line output, preserving formatting"

# Extract configuration
mcp-screenshot describe --file settings.jpg --prompt "Extract all configuration options and their current values"
```

## Comparison with Traditional OCR

### LLM-based Extraction (Current)
✅ Understands context
✅ Handles multiple languages automatically
✅ Can extract specific types of text
✅ Provides natural language responses
✅ Works with handwritten text
✅ Can infer missing/partial text

### Traditional OCR (Would add)
✅ Faster for bulk processing
✅ Lower cost for simple tasks
✅ Offline capability
✅ Character-level bounding boxes
✅ Better for legal/compliance needs

## Best Practices

1. **Be Specific**: The more specific your prompt, the better the extraction
2. **Request Format**: Ask for specific output formats (JSON, CSV, list)
3. **Context Matters**: Include context about what you're looking for
4. **Combine Commands**: Use with region selection for targeted extraction

```bash
# Example: Extract error text from specific region
mcp-screenshot capture --region top_half
mcp-screenshot describe --file screenshot_*.jpg --prompt "Extract any error or warning messages"
```

The AI-based approach is superior for most use cases because it understands meaning, not just characters!