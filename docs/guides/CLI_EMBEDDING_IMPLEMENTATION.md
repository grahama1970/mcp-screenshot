# Embedding Support Implementation for MCP Screenshot

## Summary

This guide documents how to implement embedding generation support for the MCP Screenshot tool, enabling semantic analysis of captured screenshots using LiteLLM with Vertex AI models.

## Implementation Overview

The implementation follows these key principles:

1. **Integration with LiteLLM**: Use the existing LiteLLM integration for Vertex AI/Gemini models
2. **D3.js-specific prompts**: Create specialized prompts for analyzing D3.js visualizations
3. **Non-invasive enhancement**: Build on top of the existing screenshot functionality
4. **Compatibility with MCP protocol**: Ensure all functions work seamlessly with Claude Code

## Key Components

1. **Core Embedding Module** (`core/embeddings.py`):
   - Functions for generating embeddings from image data
   - Integration with LiteLLM for vision models
   - Support for both screenshots and existing images

2. **Enhanced Capture Module** (`core/capture_enhanced.py`):
   - Extends the standard capture operations to include AI analysis
   - Wraps existing functions with embedding generation
   - Maintains the same function signatures for compatibility

3. **D3.js Verification Module** (`core/d3_verification.py`):
   - Specialized prompts for D3.js visualizations
   - Verification functions for different chart types
   - Analysis of data relationships in graphs

## Implementation Details

### Embedding Generation Logic

The core embedding generation should be implemented as:

```python
def generate_image_embedding(
    image_path: str,
    model: str = "vertex_ai/gemini-2.0-flash-exp",
    prompt: str = "Describe this image in detail"
) -> Dict[str, Any]:
    """Generate embeddings/analysis for an image using vision models."""
    
    # Prepare image for multimodal analysis
    image_b64 = prepare_image_for_multimodal(image_path)
    
    # Create messages for LiteLLM
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                }
            ]
        }
    ]
    
    # Call LiteLLM with Vertex AI
    response = completion(
        model=model,
        messages=messages,
        vertex_ai=get_vertex_credentials()
    )
    
    return {
        "description": response.choices[0].message.content,
        "model": model,
        "prompt": prompt
    }
```

### D3.js Specific Prompts

Create specialized prompts for different D3.js visualization types:

```python
D3_PROMPTS = {
    "bar-chart": """
    Analyze this D3.js bar chart visualization. Focus on:
    1. Number of bars and their relative heights
    2. Axis labels and values
    3. Color coding if present
    4. Data patterns or trends
    """,
    
    "network-graph": """
    Analyze this D3.js network graph visualization. Identify:
    1. Number of nodes and edges
    2. Node labels and relationships
    3. Graph layout and clustering
    4. Any notable patterns in connections
    """,
    
    "scatter-plot": """
    Analyze this D3.js scatter plot. Look for:
    1. Distribution of points
    2. Axis ranges and labels
    3. Correlations or clusters
    4. Outliers or patterns
    """
}
```

### CLI Integration

The enhanced CLI commands should provide detailed feedback:

```python
@app.command("verify-d3")
def verify_d3(
    url: str = typer.Argument(..., help="URL of D3.js visualization"),
    chart_type: str = typer.Option("auto", help="Type of chart to verify"),
    expected_features: List[str] = typer.Option([], help="Expected features")
):
    """Verify a D3.js visualization meets expectations."""
    
    # Capture screenshot
    screenshot_result = capture_browser_screenshot(url)
    
    if "error" in screenshot_result:
        print_error(f"Screenshot failed: {screenshot_result['error']}")
        return
    
    # Get appropriate prompt
    prompt = D3_PROMPTS.get(chart_type, DEFAULT_D3_PROMPT)
    
    # Analyze with AI
    analysis = generate_image_embedding(
        screenshot_result["file"],
        prompt=prompt
    )
    
    # Verify expected features
    description = analysis["description"]
    missing_features = []
    
    for feature in expected_features:
        if feature.lower() not in description.lower():
            missing_features.append(feature)
    
    # Report results
    print_info(f"Screenshot: {screenshot_result['file']}")
    print_info(f"Analysis: {description}")
    
    if missing_features:
        print_warning(f"Missing features: {', '.join(missing_features)}")
    else:
        print_success("All expected features found!")
```

## Configuration

### Environment Variables

```bash
export VERTEX_PROJECT="your-project-id"
export VERTEX_LOCATION="us-central1"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

### MCP Configuration

In `.mcp.json`:

```json
{
  "mcp-screenshot": {
    "command": "python",
    "args": ["-m", "mcp_screenshot.mcp.server"],
    "env": {
      "VERTEX_PROJECT": "${VERTEX_PROJECT}",
      "VERTEX_LOCATION": "${VERTEX_LOCATION}"
    }
  }
}
```

## Testing

### Basic Functionality Test

```python
def test_d3_verification():
    """Test D3.js visualization verification."""
    
    # Test URL with known D3.js visualization
    test_url = "http://localhost:3000/bar-chart"
    
    # Capture and analyze
    result = verify_d3_visualization(
        url=test_url,
        chart_type="bar-chart",
        expected_features=["bars", "axes", "labels"]
    )
    
    # Verify results
    assert result["success"]
    assert "bars" in result["analysis"]["description"]
    assert result["analysis"]["confidence"] > 3
```

### Integration Test

```python
def test_mcp_integration():
    """Test MCP server integration."""
    
    # Start MCP server
    server = create_mcp_server()
    
    # Test screenshot function
    result = server.execute("capture_and_describe", {
        "url": "http://localhost:3000/graph",
        "prompt": "Describe this D3.js visualization"
    })
    
    assert result["success"]
    assert "description" in result
```

## Error Handling

Implement robust error handling for common issues:

```python
def safe_capture_and_analyze(url: str, **kwargs) -> Dict[str, Any]:
    """Safely capture and analyze with error handling."""
    
    try:
        # Attempt capture
        screenshot = capture_browser_screenshot(url)
        
        if "error" in screenshot:
            return {
                "success": False,
                "error": f"Screenshot failed: {screenshot['error']}"
            }
        
        # Attempt analysis
        analysis = generate_image_embedding(
            screenshot["file"],
            **kwargs
        )
        
        return {
            "success": True,
            "screenshot": screenshot,
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"Capture and analyze failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
```

## Performance Considerations

1. **Image Compression**: Use appropriate JPEG quality to balance file size and clarity
2. **Model Selection**: Use fast models like Gemini Flash for quick analysis
3. **Caching**: Consider caching analysis results for repeated screenshots
4. **Batch Processing**: Support analyzing multiple screenshots in one call

## Next Steps

1. Implement browser automation for dynamic D3.js content
2. Add support for comparing before/after states
3. Create a library of D3.js-specific validation patterns
4. Add support for accessibility verification
5. Implement visual regression testing capabilities