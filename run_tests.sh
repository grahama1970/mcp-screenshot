#!/bin/bash
# Test runner for MCP Screenshot Tool

echo "Running MCP Screenshot Tool Tests..."
echo "===================================="

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run all tests
python -m pytest tests/ -v

# If pytest not installed, run tests directly
if [ $? -ne 0 ]; then
    echo "pytest not found, running tests directly..."
    python tests/test_mcp_screenshot.py
    python tests/test_zoom.py
fi