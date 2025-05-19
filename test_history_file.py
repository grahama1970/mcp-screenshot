#!/usr/bin/env python3
"""Test screenshot history functionality with local files."""

import os
import shutil
from datetime import datetime
import tempfile
from pathlib import Path

from mcp_screenshot.core.history import ScreenshotHistory

def main():
    print("Testing screenshot history with test database...")
    
    # Create temp directory for database and storage
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up paths
        db_path = os.path.join(temp_dir, "test_history.db")
        storage_dir = os.path.join(temp_dir, "screenshots")
        os.makedirs(storage_dir, exist_ok=True)
        
        print(f"Test database path: {db_path}")
        print(f"Test storage directory: {storage_dir}")
        
        # Create history instance with test paths
        history = ScreenshotHistory(db_path=db_path, storage_dir=storage_dir)
        
        # Copy test image
        test_image = "test_history.jpg"
        if not os.path.exists(test_image):
            source_image = None
            for path in ["./tmp/screenshot_1747667625057.jpeg", "./browser_1747666462510.jpeg"]:
                if os.path.exists(path):
                    source_image = path
                    break
            
            if source_image:
                print(f"Copying {source_image} to {test_image}...")
                shutil.copy2(source_image, test_image)
            else:
                print("No source image found, creating blank image...")
                from PIL import Image
                img = Image.new('RGB', (800, 600), color = (0, 0, 0))
                img.save(test_image)
        
        # Add to history
        print("\nAdding screenshot to history...")
        screenshot_id = history.add_screenshot(
            file_path=test_image,
            description="This is a test image",
            extracted_text="Test text content",
            url=None,
            region="center",
            metadata={"source": "test", "test_run": True}
        )
        print(f"Added with ID: {screenshot_id}")
        
        # Get recent screenshots
        print("\nGetting recent screenshots...")
        screenshots = history.get_recent(limit=10)
        print(f"Found {len(screenshots)} screenshots")
        
        for screenshot in screenshots:
            print(f"ID: {screenshot['id']}")
            print(f"Filename: {screenshot['filename']}")
            print(f"Path: {screenshot['storage_path']}")
            print(f"Region: {screenshot['region']}")
            print(f"Description: {screenshot.get('description')}")
        
        # Search
        print("\nSearching for 'test'...")
        results = history.search("test", limit=10)
        print(f"Found {len(results)} results")
        
        for result in results:
            print(f"ID: {result['id']}")
            print(f"Filename: {result['filename']}")
            print(f"Score: {result['rank']}")
            print(f"Description: {result.get('description')}")
        
        # Stats
        print("\nGetting statistics...")
        stats = history.get_stats()
        print(f"Total screenshots: {stats['total_screenshots']}")
        print(f"Total size: {stats['total_size_mb']} MB")
        
        # Close
        history.close()
        print("\nDone!")

if __name__ == "__main__":
    main()