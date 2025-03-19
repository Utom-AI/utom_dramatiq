import os
import json
import logging
import boto3
from botocore.exceptions import ClientError
from utom_utils.functions import env_utils

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sqs_queue(sqs_client, queue_name: str) -> str:
    """Create SQS queue and return its ARN"""
    try:
        # Create queue with 20-minute visibility timeout
        response = sqs_client.create_queue(
            QueueName=queue_name,
            Attributes={
                'VisibilityTimeout': '1200',
                'MessageRetentionPeriod': '345600'  # 4 days
            }
        )
        
        # Get queue ARN
        queue_url = response['QueueUrl']
        queue_arn = sqs_client.get_queue_attributes(
            QueueUrl=queue_url,
            AttributeNames=['QueueArn']
        )['Attributes']['QueueArn']
        
        logger.info(f"Created SQS queue: {queue_name}")
        logger.info(f"Queue ARN: {queue_arn}")
        
        return queue_arn
        
    except ClientError as e:
        logger.error(f"Error creating SQS queue: {str(e)}")
        raise

def create_iam_role(iam_client, role_name: str) -> str:
    """Create IAM role for Lambda function"""
    try:
        # Define trust policy for Lambda
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        # Create role
        response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        
        role_arn = response['Role']['Arn']
        logger.info(f"Created IAM role: {role_name}")
        logger.info(f"Role ARN: {role_arn}")
        
        return role_arn
        
    except ClientError as e:
        logger.error(f"Error creating IAM role: {str(e)}")
        raise

def attach_iam_policies(iam_client, role_name: str):
    """Attach necessary policies to IAM role"""
    try:
        # Define policy for S3 access
        s3_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::{os.getenv('AWS_BUCKET_NAME')}",
                        f"arn:aws:s3:::{os.getenv('AWS_BUCKET_NAME')}/*"
                    ]
                }
            ]
        }
        
        # Define policy for SQS access
        sqs_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "sqs:SendMessage",
                        "sqs:ReceiveMessage",
                        "sqs:DeleteMessage",
                        "sqs:GetQueueAttributes"
                    ],
                    "Resource": os.getenv('SQS_QUEUE_ARN')
                }
            ]
        }
        
        # Define policy for CloudWatch Logs
        logs_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": "arn:aws:logs:*:*:*"
                }
            ]
        }
        
        # Attach policies
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName='s3-access',
            PolicyDocument=json.dumps(s3_policy)
        )
        
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName='sqs-access',
            PolicyDocument=json.dumps(sqs_policy)
        )
        
        iam_client.put_role_policy(
            RoleName=role_name,
            PolicyName='logs-access',
            PolicyDocument=json.dumps(logs_policy)
        )
        
        logger.info(f"Attached policies to role: {role_name}")
        
    except ClientError as e:
        logger.error(f"Error attaching IAM policies: {str(e)}")
        raise

def setup_s3_notification(s3_client, bucket_name: str, queue_arn: str):
    """Configure S3 bucket notification to SQS"""
    try:
        # Define notification configuration
        notification_config = {
            'QueueConfigurations': [
                {
                    'QueueArn': queue_arn,
                    'Events': ['s3:ObjectCreated:*'],
                    'Filter': {
                        'Key': {
                            'FilterRules': [
                                {
                                    'Name': 'prefix',
                                    'Value': 'raw_videos/'
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
        
        # Update bucket notification
        s3_client.put_bucket_notification_configuration(
            Bucket=bucket_name,
            NotificationConfiguration=notification_config
        )
        
        logger.info(f"Configured S3 notification for bucket: {bucket_name}")
        
    except ClientError as e:
        logger.error(f"Error configuring S3 notification: {str(e)}")
        raise

def main():
    """Main function to set up AWS infrastructure"""
    try:
        # Load environment variables
        env_utils.load_in_env_vars()
        
        # Initialize AWS clients
        sqs_client = boto3.client('sqs')
        iam_client = boto3.client('iam')
        s3_client = boto3.client('s3')
        
        # Create SQS queue
        queue_arn = create_sqs_queue(
            sqs_client,
            'utom-video-processing-queue'
        )
        
        # Create IAM role
        role_arn = create_iam_role(
            iam_client,
            'utom-video-processing-role'
        )
        
        # Attach policies
        attach_iam_policies(
            iam_client,
            'utom-video-processing-role'
        )
        
        # Configure S3 notification
        setup_s3_notification(
            s3_client,
            os.getenv('AWS_BUCKET_NAME'),
            queue_arn
        )
        
        # Save ARNs to environment file
        with open('.env', 'a') as f:
            f.write(f"\nSQS_QUEUE_ARN={queue_arn}")
            f.write(f"\nLAMBDA_ROLE_ARN={role_arn}")
        
        logger.info("AWS infrastructure setup completed successfully")
        
    except Exception as e:
        logger.error(f"Error setting up AWS infrastructure: {str(e)}")
        raise

if __name__ == "__main__":
    main() 