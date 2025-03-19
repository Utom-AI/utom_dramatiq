import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pymongo import MongoClient
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB configuration
MONGODB_URI = 'mongodb://localhost:27017/'
DB_NAME = 'video_processor'
COLLECTION_NAME = 'video_metadata'

class MetadataManager:
    def __init__(self, mongodb_uri: str = MONGODB_URI):
        self.client = MongoClient(mongodb_uri)
        self.db = self.client[DB_NAME]
        self.collection = self.db[COLLECTION_NAME]

    def get_video_metadata(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve metadata for a specific video
        
        Args:
            video_id (str): The unique identifier of the video
            
        Returns:
            dict: The video metadata or None if not found
        """
        try:
            metadata = self.collection.find_one({'video_id': video_id})
            if metadata:
                # Convert datetime objects to string format
                if 'created_at' in metadata:
                    metadata['created_at'] = metadata['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                if 'updated_at' in metadata:
                    metadata['updated_at'] = metadata['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
                    
                # Format file sizes to MB
                if 'size' in metadata:
                    metadata['size_mb'] = f"{metadata['size'] / (1024*1024):.2f}"
                if 'audio_size' in metadata:
                    metadata['audio_size_mb'] = f"{metadata['audio_size'] / (1024*1024):.2f}"
                    
                return metadata
            return None
        except Exception as e:
            logger.error(f"Error retrieving metadata: {str(e)}")
            return None

    def list_videos(self, limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """
        List all processed videos with their metadata
        
        Args:
            limit (int): Maximum number of records to return
            skip (int): Number of records to skip (for pagination)
            
        Returns:
            list: List of video metadata
        """
        try:
            videos = list(self.collection.find({}, limit=limit, skip=skip))
            for video in videos:
                if 'created_at' in video:
                    video['created_at'] = video['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                if 'updated_at' in video:
                    video['updated_at'] = video['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
                if 'size' in video:
                    video['size_mb'] = f"{video['size'] / (1024*1024):.2f}"
                if 'audio_size' in video:
                    video['audio_size_mb'] = f"{video['audio_size'] / (1024*1024):.2f}"
            return videos
        except Exception as e:
            logger.error(f"Error listing videos: {str(e)}")
            return []

    def export_metadata_to_json(self, output_file: str = 'video_metadata.json') -> bool:
        """
        Export all video metadata to a JSON file
        
        Args:
            output_file (str): Path to the output JSON file
            
        Returns:
            bool: True if export was successful
        """
        try:
            videos = self.list_videos(limit=1000)  # Adjust limit as needed
            
            # Ensure the output directory exists
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(videos, f, indent=2, default=str)
                
            logger.info(f"Successfully exported metadata to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error exporting metadata: {str(e)}")
            return False

    def search_videos(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search videos based on metadata criteria
        
        Args:
            query (dict): Search criteria
            
        Returns:
            list: List of matching video metadata
        """
        try:
            return list(self.collection.find(query))
        except Exception as e:
            logger.error(f"Error searching videos: {str(e)}")
            return []

    def __del__(self):
        """Close MongoDB connection when object is destroyed"""
        try:
            self.client.close()
        except:
            pass 