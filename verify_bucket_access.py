import os
import boto3
import datetime
from botocore.config import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_bucket_access():
    """Verify access to the existing S3 bucket"""
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
        
        # Initialize S3 client with config
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region,
            config=config,
            endpoint_url=f'https://s3.{aws_region}.amazonaws.com'
        )
        
        # Check bucket access
        try:
            # Try to list objects (with zero objects to return)
            response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
            logger.info(f"Successfully accessed bucket: {bucket_name}")
            logger.info(f"Response: {response}")
            
            # Check bucket structure
            folders = ['raw_videos', 'processed_videos', 'failed_videos']
            for folder in folders:
                try:
                    s3_client.put_object(
                        Bucket=bucket_name,
                        Key=f"{folder}/",
                        Body=''
                    )
                    logger.info(f"Verified/created folder: {folder}/")
                except ClientError as e:
                    if e.response['Error']['Code'] == '403':
                        logger.warning(f"No write permission for folder: {folder}/")
                    else:
                        raise
            
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Error accessing bucket. Code: {error_code}")
            logger.error(f"Error message: {error_message}")
            
            if error_code == 'RequestTimeTooSkewed':
                logger.error("System time is not synchronized with AWS servers")
                logger.error("Please check your system time settings")
                return False
            elif error_code == '403':
                logger.error("Access denied. Please check your IAM permissions.")
                logger.error("Required permissions: s3:ListBucket, s3:PutObject")
            elif error_code == '404':
                logger.error(f"Bucket {bucket_name} not found")
            return False
                
    except Exception as e:
        logger.error(f"Error verifying bucket access: {str(e)}")
        return False

if __name__ == "__main__":
    success = verify_bucket_access()
    if success:
        logger.info("Bucket access verification completed successfully")
    else:
        logger.error("Failed to verify bucket access") 