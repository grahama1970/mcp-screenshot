#!/usr/bin/env python3
"""Test combined search functionality."""

from mcp_screenshot.core.history import ScreenshotHistory

def main():
    """Run tests on combined search."""
    print("Creating test database in memory...")
    history = ScreenshotHistory(db_path=':memory:')
    
    print("\nTest 1: Text-only search")
    try:
        results = history.combined_search(text_query='test query')
        print(f"✓ Success! Results obtained: {len(results)}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    print("\nTest 2: Image-only search")
    try:
        # Using None as image_path since we're just testing parameter handling
        results = history.combined_search(image_path='dummy/path.jpg')
        print(f"✓ Success! Results obtained: {len(results)}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    print("\nTest 3: No parameters (should fail)")
    try:
        history.combined_search()
        print("✗ Failed: Should have raised an exception")
    except ValueError as e:
        print(f"✓ Success! Correctly failed with: {e}")
    
    print("\nTest 4: Zero weights for text search (should fail)")
    try:
        history.combined_search(text_query='test', text_weight=0)
        print("✗ Failed: Should have raised an exception")
    except ValueError as e:
        print(f"✓ Success! Correctly failed with: {e}")
        
    print("\nAll tests completed!")

if __name__ == "__main__":
    main()