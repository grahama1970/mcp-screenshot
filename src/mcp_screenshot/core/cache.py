#!/usr/bin/env python3
"""
Simple caching for AI responses to reduce API costs and improve performance.

This module is part of the Core Layer.
"""

import hashlib
import json
import os
import time
from typing import Dict, Optional, Any
from loguru import logger


class ImageDescriptionCache:
    """Simple cache for AI image descriptions."""
    
    def __init__(self, ttl_seconds: int = 3600, cache_dir: str = ".cache"):
        """
        Initialize cache with TTL and storage directory.
        
        Args:
            ttl_seconds: Time to live for cache entries
            cache_dir: Directory to store cache files
        """
        self.ttl = ttl_seconds
        self.cache_dir = cache_dir
        self.memory_cache: Dict[str, Dict] = {}
        
        # Create cache directory if needed
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
            logger.info(f"Created cache directory: {cache_dir}")
    
    def get_cache_key(self, image_path: str, prompt: str, model: str) -> str:
        """
        Generate cache key from image content, prompt, and model.
        
        Args:
            image_path: Path to image file
            prompt: AI prompt used
            model: Model name
            
        Returns:
            str: Cache key hash
        """
        try:
            # Hash the image content
            with open(image_path, 'rb') as f:
                image_hash = hashlib.md5(f.read()).hexdigest()
            
            # Combine with prompt and model
            combined = f"{image_hash}_{prompt}_{model}"
            return hashlib.md5(combined.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error generating cache key: {e}")
            return None
    
    def get(self, key: str) -> Optional[Dict]:
        """
        Get cached result if not expired.
        
        Args:
            key: Cache key
            
        Returns:
            dict: Cached data or None if expired/missing
        """
        # Check memory cache first
        if key in self.memory_cache:
            item = self.memory_cache[key]
            if time.time() - item['timestamp'] < self.ttl:
                logger.debug(f"Cache hit (memory): {key}")
                return item['data']
        
        # Check file cache
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    item = json.load(f)
                
                if time.time() - item['timestamp'] < self.ttl:
                    # Load into memory cache
                    self.memory_cache[key] = item
                    logger.debug(f"Cache hit (file): {key}")
                    return item['data']
                else:
                    # Expired - remove file
                    os.remove(cache_file)
                    logger.debug(f"Cache expired: {key}")
            except Exception as e:
                logger.error(f"Error reading cache file: {e}")
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    def set(self, key: str, data: Dict[str, Any]):
        """
        Cache the result both in memory and on disk.
        
        Args:
            key: Cache key
            data: Data to cache
        """
        try:
            item = {
                'data': data,
                'timestamp': time.time()
            }
            
            # Memory cache
            self.memory_cache[key] = item
            
            # File cache
            cache_file = os.path.join(self.cache_dir, f"{key}.json")
            with open(cache_file, 'w') as f:
                json.dump(item, f)
            
            logger.debug(f"Cached result: {key}")
        except Exception as e:
            logger.error(f"Error caching result: {e}")
    
    def clear(self):
        """Clear all cache entries."""
        # Clear memory
        self.memory_cache.clear()
        
        # Clear files
        for file in os.listdir(self.cache_dir):
            if file.endswith('.json'):
                os.remove(os.path.join(self.cache_dir, file))
        
        logger.info("Cache cleared")


# Global cache instance
_cache = None

def get_cache() -> ImageDescriptionCache:
    """Get or create global cache instance."""
    global _cache
    if _cache is None:
        _cache = ImageDescriptionCache()
    return _cache