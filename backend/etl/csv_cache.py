"""
CSV Cache Manager: Download and cache CSV files locally
"""
import os
import requests
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CSVCache:
    """Manages local caching of CSV files to avoid repeated downloads"""
    
    def __init__(self, cache_dir='backend/data/cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def get_cached_path(self, url: str, max_age_hours: int = 24) -> str:
        """
        Get path to cached CSV file, downloading if necessary
        
        Args:
            url: URL of CSV file
            max_age_hours: Maximum age of cached file before re-downloading
            
        Returns:
            Path to local cached file
        """
        # Generate filename from URL
        filename = url.split('/')[-1].split('?')[0]
        if not filename.endswith('.csv'):
            filename = f"{filename}.csv"
            
        cache_path = self.cache_dir / filename
        
        # Check if cache exists and is fresh
        if cache_path.exists():
            age = datetime.now() - datetime.fromtimestamp(cache_path.stat().st_mtime)
            if age < timedelta(hours=max_age_hours):
                logger.info(f"✅ Using cached file: {cache_path} (age: {age.seconds//3600}h)")
                return str(cache_path)
            else:
                logger.info(f"♻️  Cache expired (age: {age.seconds//3600}h), re-downloading...")
        
        # Download file
        logger.info(f"📥 Downloading {filename}...")
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Write to cache
            with open(cache_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            file_size = cache_path.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"✅ Downloaded {filename} ({file_size:.1f} MB)")
            return str(cache_path)
            
        except Exception as e:
            logger.error(f"❌ Failed to download {url}: {e}")
            # If download fails but cache exists, use stale cache
            if cache_path.exists():
                logger.warning(f"⚠️  Using stale cache as fallback")
                return str(cache_path)
            raise
    
    def clear_cache(self):
        """Remove all cached files"""
        for file in self.cache_dir.glob('*.csv'):
            file.unlink()
        logger.info(f"🗑️  Cleared cache directory: {self.cache_dir}")
