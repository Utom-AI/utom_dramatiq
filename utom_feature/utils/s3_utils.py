import os
import boto3
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from botocore.exceptions import ClientError
from utom_utils.functions import env_utils

# Configure logging
logger = logging.getLogger(__name__)

class S3Handler:
    def __init__(self):
        """Initialize S3 handler with credentials from environment variables"""
        # Load environment variables
        env_utils.load_in_env_vars()
        
        # Get AWS credentials from environment, supporting both naming conventions
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID') or os.getenv('s3_access_key')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY') or os.getenv('s3_secret_key')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.bucket_name = os.getenv('AWS_BUCKET_NAME', 'utom-video-processing-bucket')
        
        if not self.aws_access_key_id or not self.aws_secret_access_key:
            logger.warning("AWS credentials not found in environment variables")
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region
        )
        
        # Define bucket structure
        self.folders = {
            'raw': 'raw_videos/',
            'processed': 'processed_videos/',
            'failed': 'failed_videos/'
        }
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
        
        # Setup bucket notification
        self._setup_bucket_notification()
        
    def _ensure_bucket_exists(self):
        """Ensure the S3 bucket exists, create if it doesn't"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.info(f"Creating bucket {self.bucket_name}")
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.aws_region}
                )
                logger.info(f"Bucket {self.bucket_name} created successfully")
            else:
                raise
                
    def _setup_bucket_notification(self):
        """Setup S3 bucket notification for new video uploads"""
        try:
            # Get current notification configuration
            current_config = self.s3_client.get_bucket_notification_configuration(
                Bucket=self.bucket_name
            )
            
            # Define notification configuration
            notification_config = {
                'QueueConfigurations': [
                    {
                        'QueueArn': os.getenv('SQS_QUEUE_ARN'),  # We'll need to create this
                        'Events': ['s3:ObjectCreated:*'],
                        'Filter': {
                            'Key': {
                                'FilterRules': [
                                    {
                                        'Name': 'prefix',
                                        'Value': self.folders['raw']
                                    },
                                    {
                                        'Name': 'suffix',
                                        'Value': '.mp4'
                                    }
                                ]
                            }
                        }
                    }
                ]
            }
            
            # Update notification configuration
            self.s3_client.put_bucket_notification_configuration(
                Bucket=self.bucket_name,
                NotificationConfiguration=notification_config
            )
            logger.info("Bucket notification configured successfully")
            
        except Exception as e:
            logger.error(f"Error setting up bucket notification: {str(e)}")
            raise
            
    def upload_video(self, file_path: str, video_type: str = 'meeting') -> Dict[str, Any]:
        """
        Upload a video to the S3 bucket
        
        Args:
            file_path (str): Local path to the video file
            video_type (str): Type of video (e.g., 'meeting', 'presentation')
            
        Returns:
            dict: Contains upload status and S3 URL
        """
        try:
            # Generate S3 key with timestamp and video type
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_name = os.path.basename(file_path)
            s3_key = f"{self.folders['raw']}{video_type}/{timestamp}_{file_name}"
            
            # Upload file
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                s3_key
            )
            
            # Generate URL
            url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
            
            return {
                "success": True,
                "s3_url": url,
                "s3_key": s3_key
            }
            
        except Exception as e:
            logger.error(f"Error uploading video to S3: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def download_video(self, s3_key: str, local_path: str) -> Dict[str, Any]:
        """
        Download a video from S3
        
        Args:
            s3_key (str): S3 key of the video
            local_path (str): Local path to save the video
            
        Returns:
            dict: Contains download status
        """
        try:
            self.s3_client.download_file(
                self.bucket_name,
                s3_key,
                local_path
            )
            
            return {
                "success": True,
                "local_path": local_path
            }
            
        except Exception as e:
            logger.error(f"Error downloading video from S3: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def move_to_processed(self, s3_key: str) -> Dict[str, Any]:
        """
        Move a processed video to the processed folder
        
        Args:
            s3_key (str): S3 key of the video
            
        Returns:
            dict: Contains move status
        """
        try:
            # Generate new key in processed folder
            file_name = os.path.basename(s3_key)
            new_key = f"{self.folders['processed']}{file_name}"
            
            # Copy to new location
            self.s3_client.copy_object(
                Bucket=self.bucket_name,
                CopySource={'Bucket': self.bucket_name, 'Key': s3_key},
                Key=new_key
            )
            
            # Delete from old location
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return {
                "success": True,
                "new_key": new_key
            }
            
        except Exception as e:
            logger.error(f"Error moving video to processed folder: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def move_to_failed(self, s3_key: str) -> Dict[str, Any]:
        """
        Move a failed video to the failed folder
        
        Args:
            s3_key (str): S3 key of the video
            
        Returns:
            dict: Contains move status
        """
        try:
            # Generate new key in failed folder
            file_name = os.path.basename(s3_key)
            new_key = f"{self.folders['failed']}{file_name}"
            
            # Copy to new location
            self.s3_client.copy_object(
                Bucket=self.bucket_name,
                CopySource={'Bucket': self.bucket_name, 'Key': s3_key},
                Key=new_key
            )
            
            # Delete from old location
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return {
                "success": True,
                "new_key": new_key
            }
            
        except Exception as e:
            logger.error(f"Error moving video to failed folder: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def list_unprocessed_videos(self) -> List[Dict[str, Any]]:
        """
        List all unprocessed videos in the raw folder
        
        Returns:
            list: List of video objects
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.folders['raw']
            )
            
            videos = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['Key'].endswith('.mp4'):
                        videos.append({
                            'key': obj['Key'],
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'],
                            'url': f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{obj['Key']}"
                        })
                        
            return videos
            
        except Exception as e:
            logger.error(f"Error listing unprocessed videos: {str(e)}")
            return [] 