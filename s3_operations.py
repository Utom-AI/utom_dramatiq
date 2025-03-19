import os
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import logging
from datetime import datetime
from typing import Optional, List, Dict, Tuple
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class S3Operations:
    def __init__(self):
        """Initialize S3 operations with credentials from environment"""
        load_dotenv()
        
        self.aws_access_key = os.getenv('s3_access_key')
        self.aws_secret_key = os.getenv('s3_secret_key')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.bucket_name = os.getenv('AWS_BUCKET_NAME', 'utom-content-bucket')
        
        if not all([self.aws_access_key, self.aws_secret_key, self.bucket_name]):
            raise ValueError("Missing required AWS credentials or bucket name")
            
        # Configure the client
        self.config = Config(
            connect_timeout=5,
            read_timeout=5,
            retries={'max_attempts': 2},
            s3={'addressing_style': 'path'}
        )
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.aws_region,
            config=self.config
        )
        
        # Define folder structure
        self.folders = {
            'raw': 'raw_videos',
            'processed': 'processed_videos',
            'failed': 'failed_videos'
        }

    def download_video(self, video_key: str, download_path: str) -> Tuple[bool, str]:
        """
        Download a video from S3 bucket
        
        Args:
            video_key: The S3 key of the video to download
            download_path: Local path where the video should be saved
            
        Returns:
            Tuple[bool, str]: (Success status, Error message if any)
        """
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(download_path), exist_ok=True)
            
            # Download the file
            self.s3_client.download_file(self.bucket_name, video_key, download_path)
            logger.info(f"Successfully downloaded {video_key} to {download_path}")
            return True, ""
            
        except ClientError as e:
            error_message = f"Failed to download {video_key}: {str(e)}"
            logger.error(error_message)
            return False, error_message
            
        except Exception as e:
            error_message = f"Unexpected error downloading {video_key}: {str(e)}"
            logger.error(error_message)
            return False, error_message

    def upload_video(self, local_path: str, s3_key: str, metadata: Optional[Dict] = None) -> Tuple[bool, str]:
        """
        Upload a video to S3 bucket
        
        Args:
            local_path: Path to the local video file
            s3_key: The S3 key where the video should be uploaded
            metadata: Optional metadata to attach to the video
            
        Returns:
            Tuple[bool, str]: (Success status, Error message if any)
        """
        try:
            # Verify local file exists
            if not os.path.exists(local_path):
                return False, f"Local file {local_path} does not exist"
            
            # Prepare upload parameters
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = {
                    k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                    for k, v in metadata.items()
                }
            
            # Upload the file
            self.s3_client.upload_file(
                local_path,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            
            logger.info(f"Successfully uploaded {local_path} to {s3_key}")
            return True, ""
            
        except ClientError as e:
            error_message = f"Failed to upload {local_path}: {str(e)}"
            logger.error(error_message)
            return False, error_message
            
        except Exception as e:
            error_message = f"Unexpected error uploading {local_path}: {str(e)}"
            logger.error(error_message)
            return False, error_message

    def list_videos(self, folder: str = 'raw', prefix: str = '') -> List[Dict]:
        """
        List videos in a specific folder
        
        Args:
            folder: Folder to list ('raw', 'processed', or 'failed')
            prefix: Optional prefix to filter results
            
        Returns:
            List[Dict]: List of video information dictionaries
        """
        try:
            folder_path = f"{self.folders.get(folder, folder)}/"
            if prefix:
                folder_path += prefix
            
            paginator = self.s3_client.get_paginator('list_objects_v2')
            videos = []
            
            for page in paginator.paginate(Bucket=self.bucket_name, Prefix=folder_path):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        if obj['Key'].endswith(('.mp4', '.avi', '.mov', '.mkv')):
                            # Get object metadata
                            try:
                                response = self.s3_client.head_object(
                                    Bucket=self.bucket_name,
                                    Key=obj['Key']
                                )
                                metadata = response.get('Metadata', {})
                            except:
                                metadata = {}
                            
                            videos.append({
                                'key': obj['Key'],
                                'size': obj['Size'],
                                'last_modified': obj['LastModified'].isoformat(),
                                'metadata': metadata
                            })
            
            return videos
            
        except ClientError as e:
            logger.error(f"Failed to list videos: {str(e)}")
            return []
            
        except Exception as e:
            logger.error(f"Unexpected error listing videos: {str(e)}")
            return []

    def get_video_url(self, video_key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for a video
        
        Args:
            video_key: The S3 key of the video
            expires_in: URL expiration time in seconds (default 1 hour)
            
        Returns:
            Optional[str]: Presigned URL if successful, None otherwise
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': video_key
                },
                ExpiresIn=expires_in
            )
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate URL for {video_key}: {str(e)}")
            return None

    def move_video(self, source_key: str, dest_folder: str) -> Tuple[bool, str]:
        """
        Move a video from one folder to another
        
        Args:
            source_key: Current S3 key of the video
            dest_folder: Destination folder ('raw', 'processed', or 'failed')
            
        Returns:
            Tuple[bool, str]: (Success status, Error message if any)
        """
        try:
            # Get the filename from the source key
            filename = os.path.basename(source_key)
            dest_key = f"{self.folders.get(dest_folder, dest_folder)}/{filename}"
            
            # Copy the object
            self.s3_client.copy_object(
                Bucket=self.bucket_name,
                CopySource={'Bucket': self.bucket_name, 'Key': source_key},
                Key=dest_key
            )
            
            # Delete the original
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=source_key
            )
            
            logger.info(f"Successfully moved {source_key} to {dest_key}")
            return True, ""
            
        except ClientError as e:
            error_message = f"Failed to move {source_key}: {str(e)}"
            logger.error(error_message)
            return False, error_message
            
        except Exception as e:
            error_message = f"Unexpected error moving {source_key}: {str(e)}"
            logger.error(error_message)
            return False, error_message

# Example usage
if __name__ == "__main__":
    try:
        s3_ops = S3Operations()
        
        # List videos in raw_videos folder
        logger.info("\nListing videos in raw_videos folder:")
        videos = s3_ops.list_videos('raw')
        for video in videos:
            logger.info(f"Video: {video['key']}, Size: {video['size']} bytes")
            url = s3_ops.get_video_url(video['key'])
            if url:
                logger.info(f"URL: {url}")
        
        # Test download and upload
        if videos:
            test_video = videos[0]
            download_path = f"temp_download_{os.path.basename(test_video['key'])}"
            
            # Download
            success, error = s3_ops.download_video(test_video['key'], download_path)
            if success:
                logger.info(f"Successfully downloaded: {download_path}")
                
                # Upload to processed folder
                processed_key = f"processed_videos/processed_{os.path.basename(test_video['key'])}"
                success, error = s3_ops.upload_video(
                    download_path,
                    processed_key,
                    metadata={'processed_at': datetime.now().isoformat()}
                )
                if success:
                    logger.info(f"Successfully uploaded to: {processed_key}")
                else:
                    logger.error(f"Upload failed: {error}")
                
                # Cleanup
                os.remove(download_path)
            else:
                logger.error(f"Download failed: {error}")
                
    except Exception as e:
        logger.error(f"Test failed: {str(e)}") 