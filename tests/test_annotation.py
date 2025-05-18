"""Tests for screenshot annotation functionality"""

import pytest
import os
from pathlib import Path
from PIL import Image
import tempfile

from mcp_screenshot.core.annotate import annotate_screenshot, get_font, DEFAULT_COLORS


class TestAnnotation:
    """Test annotation functionality"""
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample test image"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img = Image.new('RGB', (800, 600), color='white')
            img.save(f.name)
            yield f.name
            os.unlink(f.name)
    
    def test_annotate_empty_list(self, sample_image):
        """Test annotating with empty annotations list"""
        result = annotate_screenshot(sample_image, [])
        assert result['success']
        assert result['annotation_count'] == 0
        assert os.path.exists(result['annotated_path'])
        os.unlink(result['annotated_path'])
    
    def test_annotate_rectangle(self, sample_image):
        """Test adding rectangle annotation"""
        annotations = [{
            'type': 'rectangle',
            'coordinates': [100, 100, 300, 200],
            'text': 'Test Rectangle',
            'color': 'highlight'
        }]
        
        result = annotate_screenshot(sample_image, annotations)
        assert result['success']
        assert result['annotation_count'] == 1
        assert os.path.exists(result['annotated_path'])
        
        # Verify the image was modified
        original = Image.open(sample_image)
        annotated = Image.open(result['annotated_path'])
        assert original.size == annotated.size
        
        os.unlink(result['annotated_path'])
    
    def test_annotate_circle(self, sample_image):
        """Test adding circle annotation"""
        annotations = [{
            'type': 'circle',
            'coordinates': [400, 300, 50],  # x, y, radius
            'text': 'Test Circle',
            'color': 'error'
        }]
        
        result = annotate_screenshot(sample_image, annotations)
        assert result['success']
        assert result['annotation_count'] == 1
        assert os.path.exists(result['annotated_path'])
        os.unlink(result['annotated_path'])
    
    def test_annotate_arrow(self, sample_image):
        """Test adding arrow annotation"""
        annotations = [{
            'type': 'arrow',
            'coordinates': [100, 100, 200, 200],
            'text': 'Arrow',
            'color': 'info'
        }]
        
        result = annotate_screenshot(sample_image, annotations)
        assert result['success']
        assert result['annotation_count'] == 1
        assert os.path.exists(result['annotated_path'])
        os.unlink(result['annotated_path'])
    
    def test_annotate_text(self, sample_image):
        """Test adding text annotation"""
        annotations = [{
            'type': 'text',
            'coordinates': [50, 50],
            'text': 'Test Text',
            'color': 'success'
        }]
        
        result = annotate_screenshot(sample_image, annotations)
        assert result['success']
        assert result['annotation_count'] == 1
        assert os.path.exists(result['annotated_path'])
        os.unlink(result['annotated_path'])
    
    def test_multiple_annotations(self, sample_image):
        """Test adding multiple annotations"""
        annotations = [
            {
                'type': 'rectangle',
                'coordinates': [10, 10, 100, 100],
                'text': 'Box 1',
                'color': 'highlight'
            },
            {
                'type': 'circle',
                'coordinates': [200, 200, 30],
                'text': 'Circle',
                'color': 'error'
            },
            {
                'type': 'arrow',
                'coordinates': [300, 100, 400, 200],
                'text': 'Arrow',
                'color': 'info'
            },
            {
                'type': 'text',
                'coordinates': [500, 50],
                'text': 'Label',
                'color': 'success'
            }
        ]
        
        result = annotate_screenshot(sample_image, annotations)
        assert result['success']
        assert result['annotation_count'] == 4
        assert os.path.exists(result['annotated_path'])
        os.unlink(result['annotated_path'])
    
    def test_custom_output_path(self, sample_image):
        """Test saving to custom output path"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            output_path = f.name
        
        annotations = [{
            'type': 'rectangle',
            'coordinates': [100, 100, 200, 200],
            'color': 'highlight'
        }]
        
        result = annotate_screenshot(sample_image, annotations, output_path=output_path)
        assert result['success']
        assert result['annotated_path'] == output_path
        assert os.path.exists(output_path)
        os.unlink(output_path)
    
    def test_custom_font_size(self, sample_image):
        """Test with custom font size"""
        annotations = [{
            'type': 'text',
            'coordinates': [100, 100],
            'text': 'Large Text',
            'color': 'highlight'
        }]
        
        result = annotate_screenshot(sample_image, annotations, font_size=24)
        assert result['success']
        assert os.path.exists(result['annotated_path'])
        os.unlink(result['annotated_path'])
    
    def test_invalid_image_path(self):
        """Test with invalid image path"""
        result = annotate_screenshot('/nonexistent/image.png', [])
        assert not result['success']
        assert 'error' in result
    
    def test_custom_color_tuple(self, sample_image):
        """Test with custom color tuple"""
        annotations = [{
            'type': 'rectangle',
            'coordinates': [100, 100, 200, 200],
            'color': (128, 0, 128, 200)  # Purple with transparency
        }]
        
        result = annotate_screenshot(sample_image, annotations)
        assert result['success']
        assert os.path.exists(result['annotated_path'])
        os.unlink(result['annotated_path'])
    
    def test_default_colors(self):
        """Test default color values"""
        assert DEFAULT_COLORS['highlight'] == (255, 255, 0, 128)
        assert DEFAULT_COLORS['error'] == (255, 0, 0, 128)
        assert DEFAULT_COLORS['success'] == (0, 255, 0, 128)
        assert DEFAULT_COLORS['info'] == (0, 0, 255, 128)
    
    def test_font_loading(self):
        """Test font loading function"""
        font = get_font(16)
        assert font is not None
        
        # Test font caching
        font2 = get_font(16)
        assert font is font2  # Should be the same object from cache
        
        # Test different size
        font3 = get_font(24)
        assert font3 is not None
        assert font3 is not font