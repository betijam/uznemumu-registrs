import os
import requests
import logging
from .config import DATA_URLS

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = "/tmp/etl_data"

def download_file(url: str, filename: str) -> str:
    """Downloads a file from a URL to the local temporary directory."""
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
    
    local_path = os.path.join(DOWNLOAD_DIR, filename)
    logger.info(f"Downloading {url} to {local_path}...")
    
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        logger.info(f"Downloaded {filename}")
        return local_path
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        raise

def download_all_data():
    """Downloads all configured data files."""
    downloaded_files = {}
    for key, url in DATA_URLS.items():
        filename = f"{key}.csv"
        path = download_file(url, filename)
        downloaded_files[key] = path
    return downloaded_files
