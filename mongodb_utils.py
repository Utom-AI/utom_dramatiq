from pymongo import MongoClient
import json
from datetime import datetime
import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB configuration
MONGODB_URI = 'mongodb://localhost:27017/'
DB_NAME = 'video_processor'
COLLECTION_NAME = 'video_metadata'

def get_mongodb_client():
    """Get MongoDB client instance"""
    return MongoClient(MONGODB_URI)

def get_video_metadata(video_id: str) -> dict:
    """
    Retrieve video metadata from MongoDB by video ID
    """
    try:
        client = get_mongodb_client()
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        metadata = collection.find_one({"video_id": video_id})
        if metadata:
            # Convert ObjectId to string for JSON serialization
            metadata['_id'] = str(metadata['_id'])
            return metadata
        return None
    except Exception as e:
        logger.error(f"Error retrieving metadata: {str(e)}")
        return None
    finally:
        client.close()

def get_all_video_metadata() -> list:
    """
    Retrieve all video metadata from MongoDB
    """
    try:
        client = get_mongodb_client()
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        metadata_list = list(collection.find())
        # Convert ObjectId to string for JSON serialization
        for metadata in metadata_list:
            metadata['_id'] = str(metadata['_id'])
        return metadata_list
    except Exception as e:
        logger.error(f"Error retrieving all metadata: {str(e)}")
        return []
    finally:
        client.close()

def save_metadata_locally(metadata: dict, output_dir: str = 'test_output') -> str:
    """
    Save metadata to a local JSON file
    """
    try:
        # Create output directory if it doesn't exist
        Path(output_dir).mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'video_metadata_{timestamp}.json'
        filepath = os.path.join(output_dir, filename)
        
        # Save metadata to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        logger.info(f"Saved metadata to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error saving metadata locally: {str(e)}")
        return None 