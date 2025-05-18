# CLI Migration Guide

## Overview

This guide helps you transition from the old mcp_tools/screenshot functionality to the new mcp-screenshot tool with improved consistency and D3.js-specific features.

## Key Changes

### 1. Screenshot Commands - Enhanced Functionality

**Old Style** (mcp_tools):
```bash
python -m mcp_tools.screenshot.cli screenshot --quality 70 --region right_half
python -m mcp_tools.screenshot.cli describe --prompt "Describe this image"
```

**New Style** (mcp-screenshot):
```bash
mcp-screenshot capture --quality 70 --region right_half
mcp-screenshot describe --url http://localhost:3000 --prompt "Analyze this D3.js visualization"
mcp-screenshot verify-d3 --url http://localhost:3000 --type bar-chart
```

**Benefits**:
- Direct browser screenshot support
- D3.js-specific verification commands
- Integration with Vertex AI models
- Better error handling and reporting

### 2. MCP Integration - Simplified

**Old Style**:
```json
{
  "screenshot": {
    "command": "python",
    "args": ["-m", "mcp_tools.screenshot.mcp.mcp_server"]
  }
}
```

**New Style**:
```json
{
  "mcp-screenshot": {
    "command": "python",
    "args": ["-m", "mcp_screenshot.mcp.server"],
    "env": {
      "VERTEX_PROJECT": "your-project-id",
      "VERTEX_LOCATION": "us-central1"
    }
  }
}
```

### 3. D3.js Specific Features - New!

The new tool adds specialized D3.js verification:

```bash
# Verify a bar chart
mcp-screenshot verify-d3 --url http://localhost:3000/bar-chart \
  --type bar-chart \
  --expected-features bars,axes,labels

# Verify a network graph
mcp-screenshot verify-d3 --url http://localhost:3000/network \
  --type network-graph \
  --expected-features nodes,edges,labels

# Auto-detect visualization type
mcp-screenshot verify-d3 --url http://localhost:3000/viz --type auto
```

## Migration Steps

### Phase 1: Install New Tool
```bash
# Clone and install
git clone https://github.com/yourusername/mcp-screenshot
cd mcp-screenshot
uv pip install -e .
```

### Phase 2: Update Configuration
1. Update `.mcp.json` with new configuration
2. Set environment variables for Vertex AI
3. Test basic functionality

### Phase 3: Update Scripts
Replace old commands with new ones in your scripts and documentation.

## Command Mapping

| Old Command | New Command |
|------------|-------------|
| `screenshot --quality 70` | `capture --quality 70` |
| `describe --prompt "..."` | `describe --url URL --prompt "..."` |
| `capture full` | `capture --region full` |
| `tools regions` | `regions` |

## Best Practices

1. **Use URL-based capture** for web visualizations
2. **Specify chart types** for better D3.js analysis
3. **Set expected features** for verification
4. **Use environment variables** for configuration
5. **Enable JSON output** for scripting

## Example Workflow (New Style)

```bash
# Capture and analyze a D3.js bar chart
mcp-screenshot verify-d3 \
  --url http://localhost:3000/sales-chart \
  --type bar-chart \
  --expected-features "bars,x-axis,y-axis,title" \
  --output json

# Capture a specific region
mcp-screenshot capture \
  --region "100,100,800,600" \
  --quality 90 \
  --output screenshot.jpg

# Describe an existing image
mcp-screenshot describe \
  --file screenshot.jpg \
  --prompt "Identify the chart type and data patterns"

# Use with MCP in Claude Code
# The tool will be available as mcp_screenshot
# with functions like verify_d3, capture_and_describe
```

## Troubleshooting

### Common Issues

1. **Vertex AI Auth**: Ensure `GOOGLE_APPLICATION_CREDENTIALS` is set
2. **Browser Not Found**: Install Chrome/Chromium for browser captures
3. **Model Access**: Verify Vertex AI API is enabled in your project

### Debug Mode

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
mcp-screenshot --debug capture --url http://localhost:3000
```

## Benefits of Migration

1. **Better D3.js Support**: Specialized prompts and verification
2. **Cleaner Architecture**: Follows 3-layer design pattern
3. **Improved Performance**: Optimized image processing
4. **Enhanced CLI**: More consistent command structure
5. **MCP Ready**: Direct integration with Claude Code