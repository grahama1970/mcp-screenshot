"""
Module: image_similarity.py

External Dependencies:
- imagehash: [Documentation URL]
- PIL: [Documentation URL]
- numpy: https://numpy.org/doc/
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
Image Similarity Module using perceptual hashing

This module provides image similarity search capabilities using
perceptual hashing techniques.

This module is part of the Core Layer.
"""

import os
from typing import Dict, Any, List, Optional, Tuple
import imagehash
from PIL import Image
import numpy as np
from pathlib import Path
from loguru import logger

class ImageSimilarity:
    """
    Provides methods for calculating and comparing perceptual hashes
    of images for similarity search.
    """
    
    def __init__(self):
        """Initialize the image similarity module."""
        # Use average_hash by default as it's faster, but can be changed to:
        # - phash (better but slower)
        # - dhash (better for sequences)
        # - whash (wavelets-based)
        self.hash_algorithm = 'average_hash'
    
    def compute_hash(self, image_path: str) -> str:
        """
        Compute perceptual hash for an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            String representation of the hash
        """
        try:
            img = Image.open(image_path)
            
            if self.hash_algorithm == 'phash':
                hash_value = imagehash.phash(img)
            elif self.hash_algorithm == 'dhash':
                hash_value = imagehash.dhash(img)
            elif self.hash_algorithm == 'whash':
                hash_value = imagehash.whash(img)
            else:  # Default to average_hash
                hash_value = imagehash.average_hash(img)
                
            return str(hash_value)
        except Exception as e:
            logger.error(f"Error computing hash for {image_path}: {str(e)}")
            return None
    
    def compute_hash_batch(self, image_paths: List[str]) -> Dict[str, str]:
        """
        Compute perceptual hashes for multiple images.
        
        Args:
            image_paths: List of paths to image files
            
        Returns:
            Dictionary mapping file paths to hash strings
        """
        results = {}
        for path in image_paths:
            hash_val = self.compute_hash(path)
            if hash_val:
                results[path] = hash_val
        return results
    
    def hamming_distance(self, hash1: str, hash2: str) -> int:
        """
        Calculate Hamming distance between two hashes.
        
        Args:
            hash1: First hash as a string
            hash2: Second hash as a string
            
        Returns:
            Integer Hamming distance (0-64, lower is more similar)
        """
        try:
            h1 = int(hash1, 16)
            h2 = int(hash2, 16)
            return bin(h1 ^ h2).count('1')
        except Exception as e:
            logger.error(f"Error calculating hamming distance: {str(e)}")
            return 64  # Maximum distance as fallback
    
    def similarity_score(self, hash1: str, hash2: str) -> float:
        """
        Calculate similarity score between two hashes.
        
        Args:
            hash1: First hash as a string
            hash2: Second hash as a string
            
        Returns:
            Float similarity score (0.0 to 1.0, higher is more similar)
        """
        distance = self.hamming_distance(hash1, hash2)
        # 64 bits is the maximum distance for a 16-character hex hash
        return 1.0 - (distance / 64.0)
    
    def find_similar_images(
        self,
        target_hash: str,
        candidate_hashes: Dict[str, str],
        threshold: float = 0.9
    ) -> List[Tuple[str, float]]:
        """
        Find similar images based on hash similarity.
        
        Args:
            target_hash: Hash to compare against
            candidate_hashes: Dictionary of path->hash for candidates
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            List of (path, similarity_score) tuples for matches
        """
        results = []
        
        for path, hash_val in candidate_hashes.items():
            similarity = self.similarity_score(target_hash, hash_val)
            if similarity >= threshold:
                results.append((path, similarity))
        
        # Sort by similarity (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def find_duplicate_groups(
        self,
        hashes: Dict[str, str],
        threshold: float = 0.9
    ) -> List[List[str]]:
        """
        Find groups of similar/duplicate images.
        
        Args:
            hashes: Dictionary of path->hash for all images
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            List of lists, where each inner list contains paths to similar images
        """
        # Maps image path to a group id
        path_to_group = {}
        # Maps group id to list of image paths
        groups = {}
        group_id = 0
        
        paths = list(hashes.keys())
        
        for i in range(len(paths)):
            if paths[i] in path_to_group:
                continue  # Already assigned to a group
                
            # Create a new group for this image
            current_group = [paths[i]]
            path_to_group[paths[i]] = group_id
            
            # Find similar images
            for j in range(i + 1, len(paths)):
                if paths[j] in path_to_group:
                    continue  # Already assigned to a group
                    
                similarity = self.similarity_score(hashes[paths[i]], hashes[paths[j]])
                if similarity >= threshold:
                    current_group.append(paths[j])
                    path_to_group[paths[j]] = group_id
            
            # Save the group if it has more than one image
            if len(current_group) > 1:
                groups[group_id] = current_group
                group_id += 1
        
        return list(groups.values())


# Singleton instance
_similarity_instance: Optional[ImageSimilarity] = None


def get_similarity() -> ImageSimilarity:
    """Get or create singleton image similarity instance."""
    global _similarity_instance
    if _similarity_instance is None:
        _similarity_instance = ImageSimilarity()
    return _similarity_instance