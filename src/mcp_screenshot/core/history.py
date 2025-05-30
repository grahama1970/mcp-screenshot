#!/usr/bin/env python3
"""
Screenshot History and Search Module

This module provides screenshot history tracking with semantic search capabilities
using SQLite FTS5 (which includes BM25 ranking).

This module is part of the Core Layer.
"""

import os
import json
import sqlite3
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import shutil

from loguru import logger
from PIL import Image

from .constants import IMAGE_SETTINGS
from .image_similarity import get_similarity


class ScreenshotHistory:
    """
    Manages screenshot history with semantic search capabilities.
    Uses SQLite with FTS5 for efficient full-text search with BM25 ranking.
    """
    
    def __init__(self, 
                 db_path: Optional[str] = None,
                 storage_dir: Optional[str] = None):
        """
        Initialize screenshot history manager.
        
        Args:
            db_path: Path to SQLite database (default: ~/.mcp_screenshot/history.db)
            storage_dir: Directory for storing screenshots (default: ~/.mcp_screenshot/screenshots)
        """
        # Set up paths
        base_dir = Path.home() / ".mcp_screenshot"
        base_dir.mkdir(exist_ok=True)
        
        self.db_path = db_path or str(base_dir / "history.db")
        self.storage_dir = storage_dir or str(base_dir / "screenshots")
        
        # Create storage directory
        Path(self.storage_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self.conn = sqlite3.connect(self.db_path)
        self._init_database()
        
        logger.info(f"Screenshot history initialized: {self.db_path}")
    
    def _init_database(self):
        """Initialize SQLite database with FTS5 for semantic search."""
        cursor = self.conn.cursor()
        
        # Create main screenshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS screenshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                original_path TEXT,
                storage_path TEXT NOT NULL,
                file_hash TEXT UNIQUE NOT NULL,
                url TEXT,
                region TEXT,
                timestamp REAL NOT NULL,
                width INTEGER,
                height INTEGER,
                size_bytes INTEGER,
                perceptual_hash TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create FTS5 virtual table for full-text search with BM25
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS screenshots_fts USING fts5(
                filename,
                description,
                extracted_text,
                url,
                region,
                metadata,
                tokenize='porter unicode61'
            )
        ''')
        
        # We'll handle FTS inserts manually, so no need for triggers
        # cursor.execute('''
        #     CREATE TRIGGER IF NOT EXISTS screenshots_ai AFTER INSERT ON screenshots
        #     BEGIN
        #         -- Don't insert description/extracted_text yet (will be updated later)
        #         INSERT INTO screenshots_fts(rowid, filename, url, region, metadata)
        #         VALUES (new.id, new.filename, new.url, new.region, new.metadata);
        #     END
        # ''')
        
        # We'll handle FTS operations manually
        # cursor.execute('''
        #     CREATE TRIGGER IF NOT EXISTS screenshots_ad AFTER DELETE ON screenshots
        #     BEGIN
        #         DELETE FROM screenshots_fts WHERE rowid = old.id;
        #     END
        # ''')
        # 
        # cursor.execute('''
        #     CREATE TRIGGER IF NOT EXISTS screenshots_au AFTER UPDATE ON screenshots
        #     BEGIN
        #         UPDATE screenshots_fts 
        #         SET filename = new.filename,
        #             url = new.url,
        #             region = new.region,
        #             metadata = new.metadata
        #         WHERE rowid = new.id;
        #     END
        # ''')
        
        # Create search history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                results_count INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.conn.commit()
    
    def add_screenshot(self,
                      file_path: str,
                      description: Optional[str] = None,
                      extracted_text: Optional[str] = None,
                      url: Optional[str] = None,
                      region: Optional[str] = None,
                      metadata: Optional[Dict[str, Any]] = None,
                      compute_hash: bool = True) -> int:
        """
        Add a screenshot to history with searchable metadata.
        
        Args:
            file_path: Path to the screenshot file
            description: AI-generated description of the screenshot
            extracted_text: Text extracted from the screenshot
            url: URL if this was a web capture
            region: Screen region if this was a partial capture
            metadata: Additional metadata
            
        Returns:
            int: ID of the inserted record
        """
        try:
            # Calculate file hash to detect duplicates
            file_hash = self._calculate_file_hash(file_path)
            
            # Check if already exists
            cursor = self.conn.cursor()
            cursor.execute('SELECT id, storage_path FROM screenshots WHERE file_hash = ?', (file_hash,))
            existing = cursor.fetchone()
            
            if existing:
                logger.info(f"Screenshot already in history: {file_path}")
                return existing[0]
            
            # Copy to storage directory
            timestamp = datetime.now()
            filename = os.path.basename(file_path)
            storage_filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{filename}"
            storage_path = os.path.join(self.storage_dir, storage_filename)
            
            shutil.copy2(file_path, storage_path)
            
            # Get image metadata
            with Image.open(file_path) as img:
                width, height = img.size
                size_bytes = os.path.getsize(file_path)
            
            # Compute perceptual hash if enabled
            perceptual_hash = None
            if compute_hash:
                try:
                    similarity = get_similarity()
                    perceptual_hash = similarity.compute_hash(file_path)
                    if perceptual_hash:
                        logger.debug(f"Computed perceptual hash: {perceptual_hash}")
                except Exception as e:
                    logger.warning(f"Failed to compute perceptual hash: {e}")
            
            # Prepare metadata
            if metadata is None:
                metadata = {}
            metadata.update({
                'description': description,
                'extracted_text': extracted_text,
                'original_filename': filename
            })
            
            # Insert into database
            try:
                cursor.execute('''
                    INSERT INTO screenshots 
                    (filename, original_path, storage_path, file_hash, url, region, 
                     timestamp, width, height, size_bytes, perceptual_hash, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    storage_filename,
                    file_path,
                    storage_path,
                    file_hash,
                    url,
                    region,
                    timestamp.timestamp(),
                    width,
                    height,
                    size_bytes,
                    perceptual_hash,
                    json.dumps(metadata)
                ))
                
                screenshot_id = cursor.lastrowid
            except Exception as e:
                logger.error(f"Database error: {e}")
                raise
            
            # Instead of updating, insert into the FTS table
            cursor.execute('''
                INSERT INTO screenshots_fts(rowid, filename, description, extracted_text, url, region, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                screenshot_id,
                storage_filename,
                description,
                extracted_text,
                url,
                region,
                json.dumps(metadata)
            ))
            
            # Commit the transaction
            self.conn.commit()
            
            logger.info(f"Added screenshot to history: {storage_filename} (ID: {screenshot_id})")
            return screenshot_id
            
        except Exception as e:
            logger.error(f"Error adding screenshot to history: {str(e)}")
            self.conn.rollback()
            raise
    
    def search(self,
              query: str,
              limit: int = 10,
              offset: int = 0,
              date_from: Optional[datetime] = None,
              date_to: Optional[datetime] = None,
              region: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search screenshots using BM25 ranking via SQLite FTS5.
        
        Args:
            query: Search query
            limit: Maximum number of results
            offset: Offset for pagination
            date_from: Filter by start date
            date_to: Filter by end date
            region: Filter by capture region
            
        Returns:
            List of matching screenshots with metadata
        """
        try:
            cursor = self.conn.cursor()
            
            # Log search query
            cursor.execute(
                'INSERT INTO search_history (query, results_count) VALUES (?, 0)',
                (query,)
            )
            
            # Build the search query
            sql = '''
                SELECT 
                    s.id,
                    s.filename,
                    s.storage_path,
                    s.url,
                    s.region,
                    s.timestamp,
                    s.width,
                    s.height,
                    s.size_bytes,
                    s.perceptual_hash,
                    s.metadata,
                    bm25(screenshots_fts) as rank
                FROM screenshots s
                JOIN screenshots_fts fts ON s.id = fts.rowid
                WHERE screenshots_fts MATCH ?
            '''
            
            params = [query]
            
            # Add filters
            if date_from:
                sql += ' AND s.timestamp >= ?'
                params.append(date_from.timestamp())
            
            if date_to:
                sql += ' AND s.timestamp <= ?'
                params.append(date_to.timestamp())
            
            if region:
                sql += ' AND s.region = ?'
                params.append(region)
            
            # Order by BM25 score and limit
            sql += ' ORDER BY rank LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor.execute(sql, params)
            
            results = []
            for row in cursor.fetchall():
                metadata = json.loads(row[10]) if row[10] else {}
                results.append({
                    'id': row[0],
                    'filename': row[1],
                    'storage_path': row[2],
                    'url': row[3],
                    'region': row[4],
                    'timestamp': datetime.fromtimestamp(row[5]),
                    'width': row[6],
                    'height': row[7],
                    'size_bytes': row[8],
                    'perceptual_hash': row[9],
                    'metadata': metadata,
                    'rank': row[11],
                    'description': metadata.get('description'),
                    'extracted_text': metadata.get('extracted_text')
                })
            
            # Update search history with results count
            cursor.execute(
                'UPDATE search_history SET results_count = ? WHERE id = last_insert_rowid()',
                (len(results),)
            )
            
            self.conn.commit()
            
            logger.info(f"Search '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching screenshots: {str(e)}")
            raise
    
    def get_recent(self, 
                   limit: int = 10,
                   region: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent screenshots.
        
        Args:
            limit: Maximum number of results
            region: Filter by capture region
            
        Returns:
            List of recent screenshots
        """
        try:
            cursor = self.conn.cursor()
            
            sql = '''
                SELECT 
                    id,
                    filename,
                    storage_path,
                    url,
                    region,
                    timestamp,
                    width,
                    height,
                    size_bytes,
                    perceptual_hash,
                    metadata
                FROM screenshots
                WHERE 1=1
            '''
            
            params = []
            
            if region:
                sql += ' AND region = ?'
                params.append(region)
            
            sql += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(sql, params)
            
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                metadata = json.loads(row[10]) if row[10] else {}
                results.append({
                    'id': row[0],
                    'filename': row[1],
                    'storage_path': row[2],
                    'url': row[3],
                    'region': row[4],
                    'timestamp': datetime.fromtimestamp(row[5]),
                    'width': row[6],
                    'height': row[7],
                    'size_bytes': row[8],
                    'perceptual_hash': row[9],
                    'metadata': metadata,
                    'description': metadata.get('description'),
                    'extracted_text': metadata.get('extracted_text')
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting recent screenshots: {str(e)}")
            raise
    
    def get_by_id(self, screenshot_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific screenshot by ID."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT 
                    id,
                    filename,
                    storage_path,
                    url,
                    region,
                    timestamp,
                    width,
                    height,
                    size_bytes,
                    perceptual_hash,
                    metadata
                FROM screenshots
                WHERE id = ?
            ''', (screenshot_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            metadata = json.loads(row[10]) if row[10] else {}
            return {
                'id': row[0],
                'filename': row[1],
                'storage_path': row[2],
                'url': row[3],
                'region': row[4],
                'timestamp': datetime.fromtimestamp(row[5]),
                'width': row[6],
                'height': row[7],
                'size_bytes': row[8],
                'perceptual_hash': row[9],
                'metadata': metadata,
                'description': metadata.get('description'),
                'extracted_text': metadata.get('extracted_text')
            }
            
        except Exception as e:
            logger.error(f"Error getting screenshot by ID: {str(e)}")
            raise
    
    def delete_screenshot(self, screenshot_id: int) -> bool:
        """Delete a screenshot from history and storage."""
        try:
            cursor = self.conn.cursor()
            
            # Get file path
            cursor.execute('SELECT storage_path FROM screenshots WHERE id = ?', (screenshot_id,))
            row = cursor.fetchone()
            
            if not row:
                return False
            
            storage_path = row[0]
            
            # Delete from database
            cursor.execute('DELETE FROM screenshots WHERE id = ?', (screenshot_id,))
            self.conn.commit()
            
            # Delete file
            if os.path.exists(storage_path):
                os.remove(storage_path)
            
            logger.info(f"Deleted screenshot ID {screenshot_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting screenshot: {str(e)}")
            self.conn.rollback()
            raise
    
    def cleanup_old_screenshots(self, days: int = 30) -> int:
        """
        Delete screenshots older than specified days.
        
        Args:
            days: Number of days to keep screenshots
            
        Returns:
            Number of screenshots deleted
        """
        try:
            cursor = self.conn.cursor()
            cutoff_time = datetime.now().timestamp() - (days * 86400)
            
            # Get screenshots to delete
            cursor.execute('''
                SELECT id, storage_path 
                FROM screenshots 
                WHERE timestamp < ?
            ''', (cutoff_time,))
            
            to_delete = cursor.fetchall()
            
            for screenshot_id, storage_path in to_delete:
                # Delete file
                if os.path.exists(storage_path):
                    os.remove(storage_path)
                
                # Delete from database
                cursor.execute('DELETE FROM screenshots WHERE id = ?', (screenshot_id,))
            
            self.conn.commit()
            
            logger.info(f"Cleaned up {len(to_delete)} old screenshots")
            return len(to_delete)
            
        except Exception as e:
            logger.error(f"Error cleaning up old screenshots: {str(e)}")
            self.conn.rollback()
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about screenshot history."""
        try:
            cursor = self.conn.cursor()
            
            # Total screenshots
            cursor.execute('SELECT COUNT(*) FROM screenshots')
            total = cursor.fetchone()[0]
            
            # Total size
            cursor.execute('SELECT SUM(size_bytes) FROM screenshots')
            total_size = cursor.fetchone()[0] or 0
            
            # By region
            cursor.execute('''
                SELECT region, COUNT(*) 
                FROM screenshots 
                GROUP BY region
            ''')
            by_region = dict(cursor.fetchall())
            
            # Recent searches
            cursor.execute('''
                SELECT query, results_count, timestamp
                FROM search_history
                ORDER BY timestamp DESC
                LIMIT 10
            ''')
            recent_searches = [
                {
                    'query': row[0],
                    'results': row[1],
                    'timestamp': row[2]
                }
                for row in cursor.fetchall()
            ]
            
            return {
                'total_screenshots': total,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'by_region': by_region,
                'recent_searches': recent_searches
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {str(e)}")
            raise
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def close(self):
        """Close database connection."""
        self.conn.close()

    def combined_search(self,
                        text_query: Optional[str] = None,
                        image_path: Optional[str] = None,
                        text_weight: float = 1.0,
                        image_weight: float = 1.0,
                        threshold: float = 0.5,
                        limit: int = 10,
                        region: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Perform combined text and image similarity search.
        
        Args:
            text_query: Text search query (using BM25)
            image_path: Path to image to find similar images
            text_weight: Weight for text search results (any positive number)
            image_weight: Weight for image similarity results (any positive number)
            threshold: Overall similarity threshold (0.0-1.0)
            limit: Maximum number of results
            region: Filter by screen region
            
        Returns:
            List of matching screenshots with combined scores
        """
        try:
            # Validate inputs
            if text_query is None and image_path is None:
                raise ValueError("At least one of text_query or image_path must be provided")
            
            # Validate weights based on search modalities
            if text_query is not None and text_weight <= 0:
                raise ValueError("Text weight must be positive when using text search")
                
            if image_path is not None and image_weight <= 0:
                raise ValueError("Image weight must be positive when using image search")
            
            # Adjust weights for single-modality searches
            if text_query is None:
                # Image-only search
                text_weight = 0.0
                image_weight = 1.0
            elif image_path is None:
                # Text-only search
                text_weight = 1.0
                image_weight = 0.0
                
            total_weight = text_weight + image_weight
            if total_weight <= 0:
                raise ValueError("At least one weight must be positive")
                
            normalized_text_weight = text_weight / total_weight if total_weight > 0 else 0.0
            normalized_image_weight = image_weight / total_weight if total_weight > 0 else 0.0
            
            # Log the normalized weights
            logger.debug(f"Normalized weights: text={normalized_text_weight:.2f}, image={normalized_image_weight:.2f}")
            
            # Get text search results if requested
            text_results = []
            if text_query is not None and normalized_text_weight > 0:
                text_results = self.search(query=text_query, limit=1000, region=region)
            
            # Get image similarity results if requested
            image_results = []
            if image_path is not None and normalized_image_weight > 0:
                similarity = get_similarity()
                target_hash = similarity.compute_hash(image_path)
                if target_hash:  # Only proceed if hash computation succeeded
                    image_results = self.find_similar_images(
                        image_hash=target_hash,
                        threshold=0.1,  # Low threshold to get more candidates
                        limit=1000,
                        region=region
                    )
            
            # Create a mapping of screenshot ID to combined result
            combined_results = {}
            
            # Process text results
            max_bm25 = max([r.get('rank', 0) for r in text_results], default=1)
            for result in text_results:
                screenshot_id = result['id']
                # Normalize BM25 score (higher is better)
                normalized_score = result.get('rank', 0) / max_bm25 if max_bm25 > 0 else 0
                combined_results[screenshot_id] = {
                    **result,
                    'text_score': normalized_score,
                    'image_score': 0,
                    'combined_score': normalized_score * normalized_text_weight
                }
            
            # Process image results
            for result in image_results:
                screenshot_id = result['id']
                similarity_score = result.get('similarity', 0)
                
                if screenshot_id in combined_results:
                    # Update existing result
                    combined_results[screenshot_id]['image_score'] = similarity_score
                    combined_results[screenshot_id]['combined_score'] += similarity_score * normalized_image_weight
                else:
                    # Add new result
                    combined_results[screenshot_id] = {
                        **result,
                        'text_score': 0,
                        'image_score': similarity_score,
                        'combined_score': similarity_score * normalized_image_weight
                    }
            
            # Convert to list and filter by threshold
            results = [
                result for result in combined_results.values()
                if result['combined_score'] >= threshold
            ]
            
            # Sort by combined score (highest first)
            results.sort(key=lambda x: x['combined_score'], reverse=True)
            
            # Limit results
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error in combined search: {str(e)}")
            raise
    
    def find_similar_images(self,
                          image_path: Optional[str] = None,
                          image_hash: Optional[str] = None,
                          threshold: float = 0.8,
                          limit: int = 10,
                          region: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Find similar images based on perceptual hash.
        
        Args:
            image_path: Path to image to compare against (compute hash)
            image_hash: Perceptual hash to compare against (alternative to image_path)
            threshold: Similarity threshold (0.0-1.0)
            limit: Maximum number of results
            
        Returns:
            List of matching screenshots with similarity scores
        """
        try:
            # One of image_path or image_hash must be provided
            if not image_path and not image_hash:
                raise ValueError("Either image_path or image_hash must be provided")
                
            # Compute hash if image_path is provided
            target_hash = image_hash
            if image_path:
                similarity = get_similarity()
                target_hash = similarity.compute_hash(image_path)
                if not target_hash:
                    raise ValueError(f"Failed to compute hash for {image_path}")
            
            # Get all hashes from the database
            cursor = self.conn.cursor()
            sql = """
                SELECT id, filename, storage_path, perceptual_hash 
                FROM screenshots 
                WHERE perceptual_hash IS NOT NULL
            """
            
            params = []
            
            # Add region filter if specified
            if region:
                sql += " AND region = ?"
                params.append(region)
                
            cursor.execute(sql, params)
            
            rows = cursor.fetchall()
            similarity_instance = get_similarity()
            
            # Calculate similarity scores
            results = []
            for row in rows:
                screenshot_id, filename, storage_path, hash_value = row
                if not hash_value or hash_value == target_hash:  # Skip empty hashes or exact same hash
                    continue
                    
                score = similarity_instance.similarity_score(target_hash, hash_value)
                if score >= threshold:
                    # Get full screenshot data
                    screenshot = self.get_by_id(screenshot_id)
                    if screenshot:
                        screenshot['similarity'] = score
                        results.append(screenshot)
            
            # Sort by similarity (highest first)
            results.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Limit results
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error finding similar images: {str(e)}")
            raise


# Global instance for singleton pattern
_history_instance = None


def get_history() -> ScreenshotHistory:
    """Get or create singleton history instance."""
    global _history_instance
    if _history_instance is None:
        _history_instance = ScreenshotHistory()
    return _history_instance