"""
Module: litellm_cache.py
Description: Functions for litellm cache operations

External Dependencies:
- redis: https://redis-py.readthedocs.io/
- litellm: [Documentation URL]
- loguru: [Documentation URL]

Sample Input:
>>> # Add specific examples based on module functionality

Expected Output:
>>> # Add expected output examples

Example Usage:
>>> # Add usage examples
"""

#!/usr/bin/env python3
"""
LiteLLM Cache initialization for MCP Screenshot Tool

This module sets up LiteLLM's built-in caching mechanism using Redis or '
falling back to in-memory caching if Redis is unavailable.

This module is part of the Core Layer.
"""

import os
import redis
import litellm
from loguru import logger
from litellm.caching.caching import (
    Cache as LiteLLMCache,
    LiteLLMCacheType,
)
from typing import Optional, Dict, Any


def initialize_litellm_cache(
    redis_host: str = None,
    redis_port: int = None,
    redis_password: str = None,
    ttl: int = 3600  # 1 hour default
) -> bool:
    """
    Initialize LiteLLM cache with Redis or fallback to in-memory.
    
    Args:
        redis_host: Redis host (defaults to env var or localhost)
        redis_port: Redis port (defaults to env var or 6379)
        redis_password: Redis password (defaults to env var)
        ttl: Time to live in seconds (default 1 hour)
        
    Returns:
        bool: True if Redis cache enabled, False if using in-memory
    """
    # Get Redis configuration from parameters or environment
    redis_host = redis_host or os.getenv("REDIS_HOST", "localhost")
    redis_port = redis_port or int(os.getenv("REDIS_PORT", 6379))
    redis_password = redis_password or os.getenv("REDIS_PASSWORD", None)
    
    try:
        logger.debug(f"Testing Redis connection at {redis_host}:{redis_port}")
        
        # Test Redis connection
        test_redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            socket_timeout=2,
            decode_responses=True
        )
        
        if not test_redis.ping():
            raise ConnectionError(f"Redis not responding at {redis_host}:{redis_port}")
            
        # Configure LiteLLM Redis cache
        logger.debug("Configuring LiteLLM Redis cache...")
        litellm.cache = LiteLLMCache(
            type=LiteLLMCacheType.REDIS,
            host=redis_host,
            port=str(redis_port),
            password=redis_password,
            supported_call_types=["acompletion", "completion"],
            ttl=ttl,
        )
        
        # Enable caching
        litellm.enable_cache()
        logger.info(f" Redis caching enabled at {redis_host}:{redis_port}")
        
        # Test cache with a simple operation
        try:
            test_key = "mcp_screenshot_cache_test"
            test_redis.set(test_key, "test_value", ex=60)
            result = test_redis.get(test_key)
            test_redis.delete(test_key)
            logger.debug(f"Redis test successful: {result == 'test_value'}")
        except Exception as e:
            logger.warning(f"Redis test failed: {e}")
            
        return True
        
    except (redis.ConnectionError, redis.TimeoutError, ConnectionError) as e:
        logger.warning(f"⚠️ Redis connection failed: {e}. Using in-memory cache.")
        
        # Fall back to in-memory caching
        logger.debug("Configuring in-memory cache fallback...")
        litellm.cache = LiteLLMCache(type=LiteLLMCacheType.LOCAL)
        litellm.enable_cache()
        logger.info("In-memory cache enabled")
        
        return False


# Global initialization status
_cache_initialized = False


def ensure_cache_initialized(ttl: int = 3600) -> bool:
    """
    Ensure cache is initialized (singleton pattern).
    
    Args:
        ttl: Cache TTL in seconds
        
    Returns:
        bool: True if Redis, False if in-memory
    """
    global _cache_initialized
    
    if not _cache_initialized:
        _cache_initialized = True
        return initialize_litellm_cache(ttl=ttl)
    
    # Check if cache is Redis or in-memory
    if hasattr(litellm.cache, 'type'):
        return litellm.cache.type == LiteLLMCacheType.REDIS
    
    return False


def test_cache_functionality() -> Dict[str, Any]:
    """
    Test the cache with a simple completion call.
    
    Returns:
        dict: Test results with cache hit information
    """
    # Initialize cache if not already done
    ensure_cache_initialized()
    
    test_messages = [
        {
            "role": "user",
            "content": "Say 'cache test' in exactly 2 words."
        }
    ]
    
    try:
        # First call - cache miss
        response1 = litellm.completion(
            model="gpt-3.5-turbo",
            messages=test_messages,
            temperature=0  # Ensure deterministic response
        )
        
        # Extract cache hit info
        hidden_params1 = getattr(response1, "_hidden_params", {})
        cache_hit1 = hidden_params1.get("cache_hit", None)
        
        # Second call - should be cache hit
        response2 = litellm.completion(
            model="gpt-3.5-turbo",
            messages=test_messages,
            temperature=0
        )
        
        hidden_params2 = getattr(response2, "_hidden_params", {})
        cache_hit2 = hidden_params2.get("cache_hit", None)
        
        return {
            "success": True,
            "first_call_hit": cache_hit1,
            "second_call_hit": cache_hit2,
            "cache_working": (cache_hit1 is False or cache_hit1 is None) and cache_hit2 is True
        }
        
    except Exception as e:
        logger.error(f"Cache test failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    """Test the cache initialization"""
    logger.info("Testing LiteLLM cache initialization...")
    
    # Initialize cache
    redis_enabled = ensure_cache_initialized()
    logger.info(f"Cache type: {'Redis' if redis_enabled else 'In-memory'}")
    
    # Test functionality
    logger.info("Testing cache functionality...")
    result = test_cache_functionality()
    
    if result["success"]:
        logger.success(f"Cache test successful. Working: {result['cache_working']}")
        logger.info(f"First call hit: {result['first_call_hit']}")
        logger.info(f"Second call hit: {result['second_call_hit']}")
    else:
        logger.error(f"Cache test failed: {result['error']}")