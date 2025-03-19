import os
import json
import logging
import tempfile
from typing import Dict, Any
from datetime import datetime
from utom_feature.utils.s3_utils import S3Handler
from utom_feature.processors.video import process_video
from utom_feature.processors.transcription import transcribe_audio
from utom_utils.functions import env_utils

# Configure logging
logger = logging.getLogger(__name__)

def process_s3_video(s3_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a video from S3 notification event
    
    Args:
        s3_event (dict): S3 event containing video information
        
    Returns:
        dict: Processing status and results
    """
    try:
        # Initialize S3 handler
        s3_handler = S3Handler()
        
        # Extract video information from event
        bucket = s3_event['Records'][0]['s3']['bucket']['name']
        key = s3_event['Records'][0]['s3']['object']['key']
        
        logger.info(f"Processing video: {key} from bucket: {bucket}")
        
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download video
            video_path = os.path.join(temp_dir, 'video.mp4')
            download_result = s3_handler.download_video(key, video_path)
            
            if not download_result['success']:
                logger.error(f"Failed to download video: {download_result['error']}")
                s3_handler.move_to_failed(key)
                return {
                    "success": False,
                    "error": "Failed to download video"
                }
            
            # Process video
            process_result = process_video(video_path)
            
            if not process_result['success']:
                logger.error(f"Failed to process video: {process_result['error']}")
                s3_handler.move_to_failed(key)
                return process_result
            
            # Transcribe audio
            transcribe_result = transcribe_audio(process_result['audio_path'])
            
            if not transcribe_result['success']:
                logger.error(f"Failed to transcribe audio: {transcribe_result['error']}")
                s3_handler.move_to_failed(key)
                return transcribe_result
            
            # Move video to processed folder
            move_result = s3_handler.move_to_processed(key)
            
            if not move_result['success']:
                logger.error(f"Failed to move processed video: {move_result['error']}")
                return {
                    "success": False,
                    "error": "Failed to move processed video"
                }
            
            return {
                "success": True,
                "transcription": transcribe_result['text'],
                "processed_video_key": move_result['new_key']
            }
            
    except Exception as e:
        logger.error(f"Error processing S3 video: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def handle_s3_notification(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle S3 notification event
    
    Args:
        event (dict): S3 notification event
        
    Returns:
        dict: Processing status
    """
    try:
        # Validate event
        if 'Records' not in event or not event['Records']:
            return {
                "success": False,
                "error": "Invalid event format"
            }
        
        # Process video
        result = process_s3_video(event)
        
        # Log result
        if result['success']:
            logger.info(f"Successfully processed video: {result['processed_video_key']}")
        else:
            logger.error(f"Failed to process video: {result['error']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error handling S3 notification: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        } 