import json
import pytest
from unittest.mock import patch
from utom_feature.lambda.s3_notification_handler import lambda_handler

@pytest.fixture
def mock_s3_event():
    """Create a mock S3 event"""
    return {
        'Records': [
            {
                's3': {
                    'bucket': {
                        'name': 'test-bucket'
                    },
                    'object': {
                        'key': 'raw_videos/test.mp4'
                    }
                }
            }
        ]
    }

@pytest.fixture
def mock_context():
    """Create a mock Lambda context"""
    return type('Context', (), {
        'function_name': 'test-function',
        'memory_limit_in_mb': 128,
        'invoked_function_arn': 'arn:aws:lambda:region:account:function:test-function',
        'aws_request_id': 'test-request-id'
    })()

def test_lambda_handler_success(mock_s3_event, mock_context):
    """Test successful Lambda execution"""
    with patch('utom_feature.lambda.s3_notification_handler.handle_s3_notification') as mock_handle:
        # Mock successful processing
        mock_handle.return_value = {
            'success': True,
            'transcription': 'Test transcription',
            'processed_video_key': 'processed_videos/test.mp4'
        }
        
        # Test Lambda handler
        response = lambda_handler(mock_s3_event, mock_context)
        
        # Verify response
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['success'] is True
        assert body['transcription'] == 'Test transcription'
        assert body['processed_video_key'] == 'processed_videos/test.mp4'

def test_lambda_handler_processing_failure(mock_s3_event, mock_context):
    """Test Lambda execution with processing failure"""
    with patch('utom_feature.lambda.s3_notification_handler.handle_s3_notification') as mock_handle:
        # Mock failed processing
        mock_handle.return_value = {
            'success': False,
            'error': 'Processing failed'
        }
        
        # Test Lambda handler
        response = lambda_handler(mock_s3_event, mock_context)
        
        # Verify response
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['success'] is False
        assert body['error'] == 'Processing failed'

def test_lambda_handler_exception(mock_s3_event, mock_context):
    """Test Lambda execution with exception"""
    with patch('utom_feature.lambda.s3_notification_handler.handle_s3_notification') as mock_handle:
        # Mock exception
        mock_handle.side_effect = Exception('Test exception')
        
        # Test Lambda handler
        response = lambda_handler(mock_s3_event, mock_context)
        
        # Verify response
        assert response['statusCode'] == 500
        body = json.loads(response['body'])
        assert body['success'] is False
        assert body['error'] == 'Test exception'

def test_lambda_handler_invalid_event(mock_context):
    """Test Lambda execution with invalid event"""
    # Test with invalid event
    response = lambda_handler({}, mock_context)
    
    # Verify response
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert body['success'] is False
    assert 'error' in body 