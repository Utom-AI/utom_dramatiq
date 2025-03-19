import os
import pytest
import logging
from unittest.mock import patch, MagicMock

@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing"""
    with patch.dict(os.environ, {
        'AWS_ACCESS_KEY_ID': 'test_access_key',
        'AWS_SECRET_ACCESS_KEY': 'test_secret_key',
        'AWS_REGION': 'us-east-1',
        'AWS_BUCKET_NAME': 'test-bucket',
        'AWS_SQS_QUEUE_URL': 'https://sqs.test.amazonaws.com/123456789012/test-queue',
        'AWS_LAMBDA_FUNCTION_NAME': 'test-lambda-function',
        'VIDEO_PROCESSING_TIMEOUT': '1200',
        'LOG_LEVEL': 'INFO',
        'MONGODB_URI': 'mongodb://localhost:27017',
        'MONGODB_DB_NAME': 'test_db',
        'RABBITMQ_HOST': 'localhost',
        'RABBITMQ_PORT': '5672',
        'RABBITMQ_USER': 'guest',
        'RABBITMQ_PASSWORD': 'guest',
        'RABBITMQ_VHOST': '/',
        'RABBITMQ_QUEUE': 'test_queue'
    }):
        yield

@pytest.fixture
def mock_s3_client():
    """Mock S3 client for testing"""
    with patch('boto3.client') as mock_client:
        mock_s3 = MagicMock()
        mock_client.return_value = mock_s3
        yield mock_s3

@pytest.fixture
def mock_sqs_client():
    """Mock SQS client for testing"""
    with patch('boto3.client') as mock_client:
        mock_sqs = MagicMock()
        mock_client.return_value = mock_sqs
        yield mock_sqs

@pytest.fixture
def mock_lambda_client():
    """Mock Lambda client for testing"""
    with patch('boto3.client') as mock_client:
        mock_lambda = MagicMock()
        mock_client.return_value = mock_lambda
        yield mock_lambda

@pytest.fixture
def mock_logger():
    """Mock logger for testing"""
    with patch('logging.getLogger') as mock_get_logger:
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger 