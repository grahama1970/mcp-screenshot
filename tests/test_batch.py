#!/usr/bin/env python3
"""Tests for batch processing functionality."""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import shutil

from mcp_screenshot.core.batch import BatchProcessor, batch_capture, batch_describe


class TestBatchProcessing:
    """Test batch processing functionality"""
    
    @pytest.mark.asyncio
    async def test_batch_capture_single(self):
        """Test batch capture with single target"""
        with patch('mcp_screenshot.core.batch.capture_screenshot') as mock_capture:
            mock_capture.return_value = {
                "success": True,
                "file": "/tmp/test.jpg",
                "region": "full"
            }
            
            targets = [{"region": "full", "id": "test1"}]
            results = await batch_capture(targets)
            
            assert len(results) == 1
            assert results[0]["success"] is True
            assert results[0]["target_id"] == "test1"
            mock_capture.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_capture_multiple(self):
        """Test batch capture with multiple targets"""
        with patch('mcp_screenshot.core.batch.capture_screenshot') as mock_capture:
            mock_capture.side_effect = [
                {"success": True, "file": "/tmp/test1.jpg"},
                {"success": True, "file": "/tmp/test2.jpg"},
                {"success": False, "error": "Test error"}
            ]
            
            targets = [
                {"region": "full", "id": "test1"},
                {"region": "center", "id": "test2"},
                {"region": "left", "id": "test3"}
            ]
            
            results = await batch_capture(targets, max_concurrent=2)
            
            assert len(results) == 3
            assert results[0]["success"] is True
            assert results[1]["success"] is True
            assert results[2]["success"] is False
            assert results[2]["error"] == "Test error"
    
    @pytest.mark.asyncio
    async def test_batch_capture_with_urls(self):
        """Test batch capture with URL targets"""
        with patch('mcp_screenshot.core.batch.capture_browser_screenshot') as mock_browser:
            mock_browser.return_value = {
                "success": True,
                "file": "/tmp/website.jpg",
                "url": "https://example.com"
            }
            
            targets = [{"url": "https://example.com", "id": "web1"}]
            results = await batch_capture(targets)
            
            assert len(results) == 1
            assert results[0]["success"] is True
            assert results[0]["target_id"] == "web1"
            mock_browser.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_describe_single(self):
        """Test batch describe with single image"""
        with patch('mcp_screenshot.core.batch.litellm.acompletion') as mock_completion:
            mock_completion.return_value = AsyncMock()
            mock_completion.return_value.model_dump.return_value = {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "description": "Test image",
                            "filename": "test.jpg",
                            "confidence": 5
                        })
                    }
                }]
            }
            
            with patch('mcp_screenshot.core.batch.prepare_image_for_multimodal') as mock_prepare:
                mock_prepare.return_value = "base64_content"
                
                images = ["test.jpg"]
                results = await batch_describe(images)
                
                assert len(results) == 1
                assert results[0]["success"] is True
                assert results[0]["description"] == "Test image"
                assert results[0]["confidence"] == 5
    
    @pytest.mark.asyncio
    async def test_batch_describe_with_custom_prompts(self):
        """Test batch describe with custom prompts"""
        with patch('mcp_screenshot.core.batch.litellm.acompletion') as mock_completion:
            mock_completion.return_value = AsyncMock()
            mock_completion.return_value.model_dump.return_value = {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "description": "UI elements",
                            "filename": "ui.jpg",
                            "confidence": 4
                        })
                    }
                }]
            }
            
            with patch('mcp_screenshot.core.batch.prepare_image_for_multimodal') as mock_prepare:
                mock_prepare.return_value = "base64_content"
                
                images = [{
                    "path": "ui.jpg",
                    "prompt": "Describe the UI elements",
                    "id": "ui_test"
                }]
                
                results = await batch_describe(images)
                
                assert len(results) == 1
                assert results[0]["success"] is True
                assert results[0]["description"] == "UI elements"
                assert results[0]["image_id"] == "ui_test"
    
    @pytest.mark.asyncio
    async def test_batch_processor_concurrent_limit(self):
        """Test that batch processor respects concurrent limit"""
        processor = BatchProcessor(max_concurrent=2)
        
        # Track concurrent executions
        concurrent_count = 0
        max_concurrent_seen = 0
        
        async def slow_capture(target, pbar):
            nonlocal concurrent_count, max_concurrent_seen
            concurrent_count += 1
            max_concurrent_seen = max(max_concurrent_seen, concurrent_count)
            await asyncio.sleep(0.1)  # Simulate work
            concurrent_count -= 1
            pbar.update(1)
            return {"success": True, "target_id": target["id"]}
        
        # Patch the capture function
        processor._capture_one = slow_capture
        
        targets = [{"id": f"test{i}"} for i in range(5)]
        
        with patch('tqdm.asyncio.tqdm') as mock_tqdm:
            mock_pbar = Mock()
            mock_pbar.update = Mock()
            mock_tqdm.return_value.__enter__.return_value = mock_pbar
            
            # Create tasks manually to test concurrent limit
            tasks = []
            for target in targets:
                tasks.append(processor._capture_one(target, mock_pbar))
            
            await asyncio.gather(*tasks)
            
            # Check that we never exceeded the limit
            assert max_concurrent_seen <= 2
    
    @pytest.mark.asyncio
    async def test_batch_capture_and_describe(self):
        """Test combined capture and describe operation"""
        processor = BatchProcessor()
        
        with patch('mcp_screenshot.core.batch.capture_screenshot') as mock_capture:
            mock_capture.return_value = {
                "success": True,
                "file": "/tmp/test.jpg"
            }
            
            with patch('mcp_screenshot.core.batch.litellm.acompletion') as mock_completion:
                mock_completion.return_value = AsyncMock()
                mock_completion.return_value.model_dump.return_value = {
                    "choices": [{
                        "message": {
                            "content": json.dumps({
                                "description": "Screenshot content",
                                "filename": "test.jpg",
                                "confidence": 5
                            })
                        }
                    }]
                }
                
                with patch('mcp_screenshot.core.batch.prepare_image_for_multimodal') as mock_prepare:
                    mock_prepare.return_value = "base64_content"
                    
                    targets = [{"region": "full", "id": "test1"}]
                    results = await processor.process_capture_and_describe(targets)
                    
                    assert len(results) == 1
                    assert results[0]["success"] is True
                    assert "description" in results[0]
                    assert results[0]["description"]["description"] == "Screenshot content"
    
    @pytest.mark.asyncio
    async def test_batch_error_handling(self):
        """Test error handling in batch operations"""
        with patch('mcp_screenshot.core.batch.capture_screenshot') as mock_capture:
            mock_capture.side_effect = Exception("Capture failed")
            
            targets = [{"region": "full", "id": "test1"}]
            results = await batch_capture(targets)
            
            assert len(results) == 1
            assert results[0]["success"] is False
            assert "Capture failed" in results[0]["error"]
            assert results[0]["target_id"] == "test1"
    
    @pytest.mark.asyncio
    async def test_batch_progress_callback(self):
        """Test progress callback functionality"""
        callback_results = []
        
        async def progress_callback(result):
            callback_results.append(result)
        
        with patch('mcp_screenshot.core.batch.capture_screenshot') as mock_capture:
            mock_capture.return_value = {"success": True, "file": "/tmp/test.jpg"}
            
            targets = [{"region": "full", "id": "test1"}]
            processor = BatchProcessor()
            
            await processor.process_batch_captures(targets, progress_callback=progress_callback)
            
            assert len(callback_results) == 1
            assert callback_results[0]["success"] is True
    
    def test_batch_cli_command(self):
        """Test batch CLI command"""
        from mcp_screenshot.cli.main import app
        from typer.testing import CliRunner
        
        runner = CliRunner()
        
        # Create a temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {"region": "full", "id": "test1"},
                {"region": "center", "id": "test2"}
            ], f)
            config_file = f.name
        
        try:
            with patch('mcp_screenshot.core.batch.batch_capture') as mock_batch:
                mock_batch.return_value = [
                    {"success": True, "target_id": "test1", "file": "/tmp/test1.jpg"},
                    {"success": True, "target_id": "test2", "file": "/tmp/test2.jpg"}
                ]
                
                result = runner.invoke(app, ["batch", config_file, "--operation", "capture"])
                
                assert result.exit_code == 0
                assert "Batch capture completed" in result.stdout
                assert "Total: 2" in result.stdout
                assert "Successful: 2" in result.stdout
        finally:
            Path(config_file).unlink()
            # Clean up output directory
            if Path("./batch_output").exists():
                shutil.rmtree("./batch_output")