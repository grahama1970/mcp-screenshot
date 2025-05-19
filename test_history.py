#!/usr/bin/env python3
"""Test script for screenshot history functionality."""

import subprocess
import time
import json

def run_command(cmd):
    """Run a command and return the output."""
    print(f"\n$ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"ERROR: {result.stderr}")
    return result

def main():
    print("Testing screenshot history functionality...")
    
    # 1. Use an existing image for testing
    print("\n1. Using existing image for test...")
    existing_image = "./tmp/screenshot_1747667625057.jpeg"
    run_command(f"cp {existing_image} ./test_history.jpg")
    
    # 2. Describe it with custom prompt
    print("\n2. Describing the screenshot...")
    run_command('mcp-screenshot describe --file test_history.jpg --prompt "Extract all visible text and UI elements"')
    
    # 3. Show history
    print("\n3. Showing screenshot history...")
    run_command("mcp-screenshot history")
    
    # 4. Search for text
    print("\n4. Searching for 'text' in history...")
    run_command('mcp-screenshot search "text"')
    
    # 5. Show stats
    print("\n5. Showing statistics...")
    run_command("mcp-screenshot stats")
    
    # 6. Test JSON output
    print("\n6. Testing JSON output...")
    result = run_command("mcp-screenshot --json history --limit 5")
    if result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            print(f"Found {len(data.get('screenshots', []))} screenshots in history")
        except json.JSONDecodeError:
            print("Failed to parse JSON output")
    
    print("\nHistory test complete!")

if __name__ == "__main__":
    main()