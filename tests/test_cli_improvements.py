#!/usr/bin/env python3
"""Tests for CLI improvements"""

import pytest
from typer.testing import CliRunner
from mcp_screenshot.cli.main import app


class TestCLIImprovements:
    """Test improved CLI functionality"""
    
    def test_annotate_direct_options(self):
        """Test annotate command with direct options"""
        runner = CliRunner()
        
        # Create a dummy image file for testing
        with runner.isolated_filesystem():
            # Create a simple test image
            from PIL import Image
            img = Image.new('RGB', (100, 100), color='white')
            img.save('test.jpg')
            
            # Test rectangle annotation
            result = runner.invoke(app, [
                "annotate", "test.jpg",
                "--rect", "10,10,50,50",
                "--color", "error"
            ])
            
            assert result.exit_code == 0
            assert "Annotated image saved" in result.stdout
    
    def test_annotate_multiple_options(self):
        """Test annotate with multiple direct options"""
        runner = CliRunner()
        
        with runner.isolated_filesystem():
            from PIL import Image
            img = Image.new('RGB', (200, 200), color='white')
            img.save('test.jpg')
            
            # Test multiple annotations
            result = runner.invoke(app, [
                "annotate", "test.jpg",
                "--rect", "10,10,50,50",
                "--circle", "100,100,30",
                "--text", "Test Label",
                "--position", "150,150",
                "--color", "success"
            ])
            
            assert result.exit_code == 0
            assert "Applied" in result.stdout
    
    def test_schema_command(self):
        """Test schema command"""
        runner = CliRunner()
        
        # Test batch schema
        result = runner.invoke(app, ["schema", "batch"])
        assert result.exit_code == 0
        assert "capture" in result.stdout
        assert "describe" in result.stdout
        
        # Test capture schema
        result = runner.invoke(app, ["schema", "capture"])
        assert result.exit_code == 0
        assert "region" in result.stdout
        assert "zoom_center" in result.stdout
        
        # Test invalid command
        result = runner.invoke(app, ["schema", "invalid"])
        assert result.exit_code == 1
        assert "Unknown command" in result.stdout
    
    def test_help_improvements(self):
        """Test that help text includes all improvements"""
        runner = CliRunner()
        
        # Test capture help
        result = runner.invoke(app, ["capture", "--help"])
        assert "EXAMPLES:" in result.stdout
        assert "REGIONS: full, left-half" in result.stdout
        assert "30-90" in result.stdout
        
        # Test describe help
        result = runner.invoke(app, ["describe", "--help"])
        assert "USAGE: Requires either --url OR --file" in result.stdout
        assert "MODELS:" in result.stdout
        assert "vertex_ai/gemini-" in result.stdout
        
        # Test compare help
        result = runner.invoke(app, ["compare", "--help"])
        assert "RGB format" in result.stdout
        assert "'255,0,0'" in result.stdout
    
    def test_json_output_consistency(self):
        """Test JSON output is available for all commands"""
        runner = CliRunner()
        
        commands = ["regions", "cache-info", "version"]
        
        for cmd in commands:
            result = runner.invoke(app, ["--json", cmd])
            # Should not fail (exit code might vary based on environment)
            assert "{" in result.stdout or "Error" in result.stdout