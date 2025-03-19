import os
import logging
from datetime import datetime
from metadata_utils import MetadataManager
from utom_feature.processors.video import process_video
import boto3
from botocore.exceptions import ClientError
import json
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_s3_video_url(bucket_name: str, video_key: str, expiration: int = 3600) -> str:
    """
    Generate a presigned URL for the S3 video
    
    Args:
        bucket_name (str): S3 bucket name
        video_key (str): Key of the video in the bucket
        expiration (int): URL expiration time in seconds
        
    Returns:
        str: Presigned URL for the video
    """
    try:
        s3_client = boto3.client('s3',
            aws_access_key_id=os.getenv('s3_access_key'),
            aws_secret_access_key=os.getenv('s3_secret_key'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': video_key
            },
            ExpiresIn=expiration
        )
        return url
    except ClientError as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        raise

def generate_markdown_report(metadata: dict, output_file: str = 'video_report.md'):
    """Generate a markdown report from the video metadata"""
    try:
        report = f"""# Video Processing Report

## Video Information
- **Video ID**: {metadata.get('video_id')}
- **Filename**: {metadata.get('filename')}
- **Duration**: {metadata.get('duration', 0):.2f} seconds
- **Resolution**: {metadata.get('resolution')}
- **FPS**: {metadata.get('fps')}
- **File Size**: {float(metadata.get('size', 0)) / (1024*1024):.2f} MB

## Processing Details
- **Status**: {'✅ Completed' if metadata.get('processed') else '⏳ Processing'}
- **Has Audio**: {'Yes' if metadata.get('has_audio') else 'No'}
- **Created At**: {metadata.get('created_at')}
- **Updated At**: {metadata.get('updated_at')}

## Features
- **Transcription**: {'Available' if metadata.get('features', {}).get('transcription') else 'Not Available'}
- **Action Points**: {len(metadata.get('features', {}).get('action_points', []))} points identified

## Technical Details
- **Original URL**: {metadata.get('url')}
- **Audio Size**: {float(metadata.get('audio_size', 0)) / (1024*1024):.2f} MB
"""
        
        with open(output_file, 'w') as f:
            f.write(report)
            
        logger.info(f"Generated markdown report: {output_file}")
        return True
    except Exception as e:
        logger.error(f"Error generating markdown report: {str(e)}")
        return False

def run_end_to_end_test():
    """Run end-to-end test of video processing pipeline"""
    try:
        # Load test info
        with open('test_output/test_info.json', 'r') as f:
            test_info = json.load(f)
            
        bucket_name = test_info['bucket']
        video_key = test_info['key']
        
        # Step 1: Get video URL from S3
        logger.info("Getting video URL from S3...")
        video_url = get_s3_video_url(bucket_name, video_key)
        
        # Step 2: Process the video
        logger.info("Processing video...")
        result = process_video(video_url)
        
        if not result['success']:
            raise Exception(f"Video processing failed: {result.get('error')}")
            
        video_id = result['video_id']
        logger.info(f"Video processed successfully. ID: {video_id}")
        
        # Step 3: Retrieve and export metadata
        logger.info("Retrieving metadata...")
        metadata_manager = MetadataManager()
        metadata = metadata_manager.get_video_metadata(video_id)
        
        if not metadata:
            raise Exception("Failed to retrieve metadata")
            
        # Export to JSON
        json_output = 'test_output/metadata.json'
        Path('test_output').mkdir(parents=True, exist_ok=True)
        
        with open(json_output, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
        logger.info(f"Exported metadata to {json_output}")
        
        # Generate markdown report
        markdown_output = 'test_output/video_report.md'
        generate_markdown_report(metadata, markdown_output)
        logger.info(f"Generated report at {markdown_output}")
        
        # Cleanup
        if result.get('video_path') and os.path.exists(result['video_path']):
            os.remove(result['video_path'])
        if result.get('audio_path') and os.path.exists(result['audio_path']):
            os.remove(result['audio_path'])
            
        logger.info("Test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    print("Starting end-to-end test...")
    print("=" * 50)
    run_end_to_end_test() 