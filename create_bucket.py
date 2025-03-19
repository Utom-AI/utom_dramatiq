import os
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_s3_bucket():
    """Create the S3 bucket if it doesn't exist"""
    # Load environment variables
    load_dotenv()
    
    # Get AWS credentials
    aws_access_key = os.getenv('s3_access_key')
    aws_secret_key = os.getenv('s3_secret_key')
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    bucket_name = os.getenv('AWS_BUCKET_NAME', 'utom-video-processing-bucket')
    
    if not aws_access_key or not aws_secret_key:
        logger.error("AWS credentials not found in environment variables")
        return False
        
    try:
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        # Check if bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            logger.info(f"Bucket {bucket_name} already exists")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Create bucket
                logger.info(f"Creating bucket {bucket_name}")
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': aws_region}
                )
                logger.info(f"Bucket {bucket_name} created successfully")
                return True
            else:
                logger.error(f"Error checking bucket: {str(e)}")
                return False
                
    except Exception as e:
        logger.error(f"Error creating bucket: {str(e)}")
        return False

if __name__ == "__main__":
    success = create_s3_bucket()
    if success:
        logger.info("Bucket setup completed successfully")
    else:
        logger.error("Failed to create bucket") 