import os
from pymongo import MongoClient
from datetime import datetime
from pprint import pprint
from utom_feature.processors.video import process_video
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_video_processing_and_mongo():
    """Test video processing and MongoDB integration"""
    
    # MongoDB connection
    logger.info("Connecting to MongoDB...")
    client = MongoClient('mongodb://localhost:27017/')
    db = client['video_processor']
    collection = db['video_metadata']
    
    # Test with a public video URL
    test_video_url = "https://www.learningcontainer.com/wp-content/uploads/2020/05/sample-mp4-file.mp4"
    logger.info(f"Using test video URL: {test_video_url}")
    
    try:
        # Process video
        logger.info("Processing video...")
        result = process_video(test_video_url)
        
        if result['success']:
            logger.info("Video processing successful")
            # Get video ID from the result
            video_id = result.get('video_id')
            
            if video_id:
                logger.info(f"Video ID: {video_id}")
                # Retrieve metadata from MongoDB
                logger.info("Retrieving metadata from MongoDB...")
                metadata = collection.find_one({'video_id': video_id})
                
                if metadata:
                    print("\nVideo Metadata:")
                    print("=" * 50)
                    # Format and print metadata
                    formatted_metadata = {
                        'video_id': metadata['video_id'],
                        'filename': metadata['filename'],
                        'url': metadata['url'],
                        'duration': f"{metadata['duration']:.2f} seconds",
                        'resolution': metadata['resolution'],
                        'size': f"{metadata['size'] / (1024*1024):.2f} MB",
                        'fps': metadata['fps'],
                        'has_audio': metadata['has_audio'],
                        'processed': metadata['processed'],
                        'created_at': metadata['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                        'features': metadata['features']
                    }
                    
                    # Pretty print the formatted metadata
                    pprint(formatted_metadata, indent=2)
                    
                    # Also show raw metadata for verification
                    print("\nRaw Metadata from MongoDB:")
                    print("=" * 50)
                    pprint(metadata, indent=2)
                else:
                    logger.error("No metadata found for video ID:", video_id)
            else:
                logger.error("No video ID in processing result")
        else:
            logger.error("Video processing failed:", result.get('error'))
            
    except Exception as e:
        logger.error(f"Error during testing: {str(e)}")
        raise  # Re-raise to see full traceback
    finally:
        # Cleanup
        if 'result' in locals() and result.get('success'):
            logger.info("Cleaning up temporary files...")
            if result.get('video_path') and os.path.exists(result['video_path']):
                os.remove(result['video_path'])
            if result.get('audio_path') and os.path.exists(result['audio_path']):
                os.remove(result['audio_path'])
        client.close()
        logger.info("MongoDB connection closed")

if __name__ == "__main__":
    print("Starting MongoDB integration test...")
    print("=" * 50)
    test_video_processing_and_mongo() 