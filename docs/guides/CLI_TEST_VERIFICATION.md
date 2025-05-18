# CLI Test Verification Guide

This document outlines the process for ensuring that CLI functionality remains aligned with automated tests, providing a verification pathway to confirm that passing tests translate to working CLI commands.

## Why CLI Verification is Necessary

While automated tests cover individual components, they may not fully exercise the CLI entry points as a user would experience them. Tests passing does not always guarantee that the CLI works correctly due to:

1. Interface misalignment between CLI arguments and underlying functions
2. Environment differences between test and CLI execution contexts
3. Integration failures that don't appear in isolated component tests
4. Edge cases with real-world inputs

## CLI Verification Checklist

After tests pass, follow this verification checklist to ensure the CLI functionality works correctly:

### 1. Basic CLI Health Check

Run the CLI with help flag to verify it starts correctly:

```bash
mcp-screenshot --help
```

Expected: Help text displays showing all available commands

### 2. Core Functionality Check

Verify basic capture without options:

```bash
mcp-screenshot capture
```

Expected: Screenshot saved to default location

### 3. URL-Based Capture

Capture a webpage screenshot:

```bash
mcp-screenshot capture --url http://localhost:3000
```

Expected: Browser opens, captures page, saves screenshot

### 4. D3.js Verification

Test D3.js-specific functionality:

```bash
# Basic D3.js verification
mcp-screenshot verify-d3 --url http://localhost:3000/chart --type bar-chart

# With expected features
mcp-screenshot verify-d3 --url http://localhost:3000/network \
  --type network-graph \
  --expected-features nodes,edges,labels
```

Expected: Screenshot captured, analyzed, and verification results displayed

### 5. Image Description

Test AI-powered description:

```bash
# Describe a file
mcp-screenshot describe --file screenshot.jpg

# Capture and describe
mcp-screenshot describe --url http://localhost:3000 \
  --prompt "Analyze this D3.js visualization"
```

Expected: Detailed description of image content

### 6. Region Capture

Test region-based capture:

```bash
# Named region
mcp-screenshot capture --region right_half

# Coordinate region
mcp-screenshot capture --region "100,100,800,600"
```

Expected: Captures specified region only

### 7. Quality Settings

Test quality parameter:

```bash
mcp-screenshot capture --quality 90 --url http://localhost:3000
```

Expected: Higher quality image saved

### 8. JSON Output

Test JSON output format:

```bash
mcp-screenshot capture --url http://localhost:3000 --json
```

Expected: JSON-formatted response with success status

### 9. Error Handling Verification

Test error handling with invalid inputs:

```bash
# Invalid URL
mcp-screenshot capture --url invalid-url

# Non-existent file
mcp-screenshot describe --file nonexistent.jpg

# Invalid chart type
mcp-screenshot verify-d3 --url http://localhost:3000 --type invalid-type
```

Expected: Clear error messages that explain the issue

## Automated CLI Verification Script

Create a verification script that runs after tests pass:

```bash
#!/bin/bash
# cli_verification.sh
echo "Running CLI verification tests..."

# Define colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Array to track failed tests
failed_tests=()

# Function to run test and check result
run_test() {
  local test_name="$1"
  local command="$2"
  local expected_pattern="$3"
  
  echo -n "Testing $test_name... "
  
  # Run command and capture output
  output=$(eval "$command" 2>&1)
  exit_code=$?
  
  # Check if output matches expected pattern or exit code is 0
  if [ $exit_code -eq 0 ] || echo "$output" | grep -q "$expected_pattern"; then
    echo -e "${GREEN}PASS${NC}"
  else
    echo -e "${RED}FAIL${NC}"
    echo "  Exit code: $exit_code"
    echo "  Expected pattern: $expected_pattern"
    echo "  Actual output: $output"
    failed_tests+=("$test_name")
  fi
}

# Create test directory
mkdir -p test_output

# Run verification tests
run_test "help display" "mcp-screenshot --help" "Usage:"
run_test "basic capture" "mcp-screenshot capture --output test_output/basic.jpg" ""
run_test "url capture" "mcp-screenshot capture --url https://example.com --output test_output/url.jpg" ""
run_test "describe file" "mcp-screenshot describe --file test_output/basic.jpg" "description"
run_test "json output" "mcp-screenshot capture --json" "\"success\""
run_test "region capture" "mcp-screenshot capture --region right_half --output test_output/region.jpg" ""
run_test "d3 verification" "mcp-screenshot verify-d3 --url https://example.com --type bar-chart" ""

# Test error handling
run_test "invalid url error" "mcp-screenshot capture --url invalid-url" "Error"
run_test "file not found error" "mcp-screenshot describe --file nonexistent.jpg" "Error"

# Clean up
rm -rf test_output

# Report results
if [ ${#failed_tests[@]} -eq 0 ]; then
  echo -e "\n${GREEN}All CLI verification tests passed!${NC}"
  exit 0
else
  echo -e "\n${RED}Some CLI verification tests failed:${NC}"
  for test in "${failed_tests[@]}"; do
    echo "  - $test"
  done
  exit 1
fi
```

## Integration with CI/CD

Add CLI verification to your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
test_and_verify:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install uv
        uv pip install -e .
    
    - name: Run tests
      run: |
        python -m pytest tests/
    
    - name: Verify CLI
      run: |
        bash scripts/cli_verification.sh
```

## Troubleshooting Common CLI Issues

When CLI verification fails but tests pass, check for:

1. **Environment Variables**: 
   - Ensure `VERTEX_PROJECT` and `VERTEX_LOCATION` are set
   - Check `GOOGLE_APPLICATION_CREDENTIALS` path is valid

2. **Browser Dependencies**:
   - Verify Chrome/Chromium is installed for browser captures
   - Check Selenium drivers are properly configured

3. **Model Access**:
   - Confirm Vertex AI API is enabled in project
   - Verify service account has necessary permissions

4. **Python Path Issues**:
   - Ensure package is properly installed with `uv pip install -e .`
   - Check that all modules are importable

## Ensuring Test and CLI Alignment

To maintain alignment between tests and CLI:

1. **Use Same Core Functions**: CLI commands should call the same core functions as tests
2. **Test CLI Directly**: Include subprocess tests that invoke CLI commands
3. **Document Parameters**: Keep CLI help text synchronized with function docstrings
4. **Version Commands**: Track CLI interface changes in changelog
5. **Integration Tests**: Test complete workflows through CLI

## Example CLI Integration Test

```python
import subprocess
import json
import os

def test_cli_capture_and_describe():
    """Test CLI capture and describe workflow."""
    
    # Capture screenshot
    result = subprocess.run([
        "mcp-screenshot", "capture",
        "--url", "http://localhost:3000",
        "--output", "test_screenshot.jpg",
        "--json"
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["success"] is True
    assert os.path.exists("test_screenshot.jpg")
    
    # Describe the captured image
    result = subprocess.run([
        "mcp-screenshot", "describe",
        "--file", "test_screenshot.jpg",
        "--json"
    ], capture_output=True, text=True)
    
    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["success"] is True
    assert "description" in output["result"]
    
    # Clean up
    os.remove("test_screenshot.jpg")
```

## CLI Verification Report Template

Document CLI verification results:

```markdown
# CLI Verification Report - [Date]

## Environment
- OS: [Operating System]
- Python: [Version]
- mcp-screenshot: [Version]
- Vertex AI Project: [Project ID]

## Test Results

| Command | Status | Notes |
|---------|--------|-------|
| `mcp-screenshot --help` | ✅ PASS | Help displayed correctly |
| `mcp-screenshot capture` | ✅ PASS | Basic capture works |
| `mcp-screenshot capture --url` | ✅ PASS | Browser capture works |
| `mcp-screenshot verify-d3` | ✅ PASS | D3.js verification works |
| `mcp-screenshot describe` | ✅ PASS | AI description works |
| Error handling | ✅ PASS | Errors reported clearly |

## Issues Found
- None / [List any issues]

## Recommendations
- [Any improvements suggested]
```

This verification process ensures that the CLI works correctly in real-world usage, complementing the automated test suite.