"""
API Client module for interacting with the fonki.pro music service.
"""
import requests
import re
from typing import Dict, List, Optional, Any, Union


class APIClient:
    """Client for interacting with the fonki.pro music service API."""
    
    BASE_URL = "https://fonki.pro"
    
    # Common HTTP headers for all requests
    COMMON_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://fonki.pro/"
    }
    
    def __init__(self):
        """Initialize the API client."""
        self.session = requests.Session()
        self.session.headers.update(self.COMMON_HEADERS)
    
    def search_songs(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for songs by name.
        
        Args:
            query: Song name to search for
            
        Returns:
            List of song dictionaries with metadata
            
        Raises:
            requests.RequestException: If the API request fails
        """
        search_url = f"{self.BASE_URL}/search?name={query}"
        response = self.session.get(search_url, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        return data.get('musics', {}).get('data', [])
    
    def download_mp3(self, url: str) -> Optional[bytes]:
        """
        Download an MP3 file from a URL.
        
        Args:
            url: URL of the MP3 file to download
            
        Returns:
            Binary content of the MP3 file, or None if download failed
            
        Raises:
            requests.RequestException: If the request fails
        """
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                return response.content
            else:
                print(f"Download error: {response.status_code}")
                return None
        except Exception as e:
            print(f"Exception during MP3 download: {e}")
            return None
    
    def get_minus_versions(self, song_id: Union[str, int]) -> List[str]:
        """
        Get available minus (instrumental) versions for a song.
        
        Args:
            song_id: ID of the song
            
        Returns:
            List of minus version IDs
            
        Raises:
            requests.RequestException: If the API request fails
        """
        url = f"{self.BASE_URL}/minus/{song_id}"
        response = self.session.get(url, timeout=15)
        response.raise_for_status()
        
        # Extract minus IDs from the HTML response
        return re.findall(r'data-source="/plugin/sounds/uploads/(\d+)\.mp3"', response.text)
    
    def get_minus_url(self, minus_id: str) -> str:
        """
        Get the download URL for a minus version.
        
        Args:
            minus_id: ID of the minus version
            
        Returns:
            URL to download the minus version
        """
        return f"{self.BASE_URL}/plugin/sounds/uploads/{minus_id}.mp3"