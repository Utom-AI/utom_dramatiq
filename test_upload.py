import os
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import logging
from datetime import datetime
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_file(filename):
    """Create a small test file with timestamp"""
    content = f"Test file created at {datetime.now().isoformat()}"
    with open(filename, 'w') as f:
        f.write(content)
    return os.path.abspath(filename)

def test_upload():
    """Test uploading files to different folders in the S3 bucket"""
    # Load environment variables
    load_dotenv()
    
    # Get AWS credentials
    aws_access_key = os.getenv('s3_access_key')
    aws_secret_key = os.getenv('s3_secret_key')
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    bucket_name = os.getenv('AWS_BUCKET_NAME', 'utom-content-bucket')
    
    if not aws_access_key or not aws_secret_key:
        logger.error("AWS credentials not found in environment variables")
        return False
    
    try:
        # Configure the client with path-style addressing
        config = Config(
            connect_timeout=5,
            read_timeout=5,
            retries={'max_attempts': 2},
            s3={'addressing_style': 'path'}
        )
        
        # Initialize S3 client without endpoint_url
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region,
            config=config
        )
        
        # Test upload to each folder
        folders = ['raw_videos', 'processed_videos', 'failed_videos']
        test_files = []
        
        for folder in folders:
            try:
                # Create test file
                test_filename = f'test_{folder}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
                local_path = create_test_file(test_filename)
                test_files.append(local_path)
                
                # Upload to S3
                s3_key = f"{folder}/{test_filename}"
                logger.info(f"Uploading {test_filename} to {folder}/")
                
                s3_client.upload_file(
                    local_path,
                    bucket_name,
                    s3_key
                )
                
                # Verify upload by trying to get object metadata
                s3_client.head_object(Bucket=bucket_name, Key=s3_key)
                logger.info(f"Successfully uploaded and verified {s3_key}")
                
                # Get the actual URL using generate_presigned_url
                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': s3_key},
                    ExpiresIn=3600  # URL valid for 1 hour
                )
                logger.info(f"File URL (valid for 1 hour): {url}")
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                logger.error(f"Error uploading to {folder}/. Code: {error_code}")
                logger.error(f"Error message: {error_message}")
                return False
                
        logger.info("All test uploads completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during test upload: {str(e)}")
        return False
        
    finally:
        # Cleanup local test files
        for file_path in test_files:
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up local file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not delete local file {file_path}: {str(e)}")

def test_video_workflow():
    """Test downloading a video from raw_videos, simulating processing, and uploading to processed_videos"""
    # Load environment variables
    load_dotenv()
    
    # Get AWS credentials
    aws_access_key = os.getenv('s3_access_key')
    aws_secret_key = os.getenv('s3_secret_key')
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    bucket_name = os.getenv('AWS_BUCKET_NAME', 'utom-content-bucket')
    
    if not aws_access_key or not aws_secret_key:
        logger.error("AWS credentials not found in environment variables")
        return False
    
    # Create temp directory for downloads
    temp_dir = 'temp_downloads'
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Configure the client
        config = Config(
            connect_timeout=5,
            read_timeout=5,
            retries={'max_attempts': 2},
            s3={'addressing_style': 'path'}
        )
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region,
            config=config
        )
        
        # First, upload a test video to raw_videos
        test_video_name = f'test_video_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4'
        raw_video_key = f'raw_videos/{test_video_name}'
        
        # Create a dummy video file (just a text file for testing)
        local_video_path = os.path.join(temp_dir, test_video_name)
        with open(local_video_path, 'w') as f:
            f.write("This is a simulated video file for testing purposes")
        
        # Upload to raw_videos
        logger.info(f"Uploading test video to {raw_video_key}")
        s3_client.upload_file(local_video_path, bucket_name, raw_video_key)
        logger.info("Test video uploaded successfully")
        
        # Download the video
        download_path = os.path.join(temp_dir, 'downloaded_' + test_video_name)
        logger.info(f"Downloading video from {raw_video_key}")
        s3_client.download_file(bucket_name, raw_video_key, download_path)
        logger.info("Video downloaded successfully")
        
        # Simulate video processing (just create a modified file)
        processed_path = os.path.join(temp_dir, 'processed_' + test_video_name)
        with open(download_path, 'r') as source, open(processed_path, 'w') as target:
            content = source.read()
            target.write(content + "\nProcessed at " + datetime.now().isoformat())
        logger.info("Simulated video processing completed")
        
        # Upload processed video
        processed_key = f'processed_videos/processed_{test_video_name}'
        logger.info(f"Uploading processed video to {processed_key}")
        s3_client.upload_file(processed_path, bucket_name, processed_key)
        logger.info("Processed video uploaded successfully")
        
        # Verify both files exist
        s3_client.head_object(Bucket=bucket_name, Key=raw_video_key)
        s3_client.head_object(Bucket=bucket_name, Key=processed_key)
        logger.info("Verified both raw and processed videos exist in bucket")
        
        # Generate URLs for both files
        raw_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': raw_video_key},
            ExpiresIn=3600
        )
        processed_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': processed_key},
            ExpiresIn=3600
        )
        
        logger.info(f"Raw video URL (valid for 1 hour): {raw_url}")
        logger.info(f"Processed video URL (valid for 1 hour): {processed_url}")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"Error in video workflow. Code: {error_code}")
        logger.error(f"Error message: {error_message}")
        return False
        
    except Exception as e:
        logger.error(f"Error during video workflow: {str(e)}")
        return False
        
    finally:
        # Cleanup temp directory
        try:
            shutil.rmtree(temp_dir)
            logger.info("Cleaned up temporary directory")
        except Exception as e:
            logger.warning(f"Could not delete temp directory: {str(e)}")

if __name__ == "__main__":
    # Test basic uploads
    logger.info("\n=== Testing basic uploads ===")
    if test_upload():
        logger.info("Basic upload tests completed successfully")
    else:
        logger.error("Basic upload tests failed")
    
    # Test video workflow
    logger.info("\n=== Testing video workflow ===")
    if test_video_workflow():
        logger.info("Video workflow test completed successfully")
    else:
        logger.error("Video workflow test failed") 