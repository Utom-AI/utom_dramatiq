import os
import pytest
import tempfile
from unittest.mock import Mock, patch
from utom_feature.utils.s3_utils import S3Handler

@pytest.fixture
def s3_handler():
    """Create a mock S3 handler for testing"""
    with patch('boto3.client') as mock_client:
        # Create mock S3 client
        mock_s3 = Mock()
        mock_client.return_value = mock_s3
        
        # Create handler instance
        handler = S3Handler()
        handler.s3_client = mock_s3
        
        yield handler

def test_upload_video(s3_handler):
    """Test video upload functionality"""
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(suffix='.mp4') as temp_file:
        # Mock successful upload
        s3_handler.s3_client.upload_file.return_value = None
        
        # Test upload
        result = s3_handler.upload_video(temp_file.name)
        
        # Verify result
        assert result['success'] is True
        assert 's3_url' in result
        assert 's3_key' in result
        
        # Verify upload was called
        s3_handler.s3_client.upload_file.assert_called_once()

def test_download_video(s3_handler):
    """Test video download functionality"""
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(suffix='.mp4') as temp_file:
        # Mock successful download
        s3_handler.s3_client.download_file.return_value = None
        
        # Test download
        result = s3_handler.download_video('test_key.mp4', temp_file.name)
        
        # Verify result
        assert result['success'] is True
        assert result['local_path'] == temp_file.name
        
        # Verify download was called
        s3_handler.s3_client.download_file.assert_called_once()

def test_move_to_processed(s3_handler):
    """Test moving video to processed folder"""
    # Mock successful copy and delete
    s3_handler.s3_client.copy_object.return_value = None
    s3_handler.s3_client.delete_object.return_value = None
    
    # Test move
    result = s3_handler.move_to_processed('raw_videos/test.mp4')
    
    # Verify result
    assert result['success'] is True
    assert 'new_key' in result
    
    # Verify copy and delete were called
    s3_handler.s3_client.copy_object.assert_called_once()
    s3_handler.s3_client.delete_object.assert_called_once()

def test_move_to_failed(s3_handler):
    """Test moving video to failed folder"""
    # Mock successful copy and delete
    s3_handler.s3_client.copy_object.return_value = None
    s3_handler.s3_client.delete_object.return_value = None
    
    # Test move
    result = s3_handler.move_to_failed('raw_videos/test.mp4')
    
    # Verify result
    assert result['success'] is True
    assert 'new_key' in result
    
    # Verify copy and delete were called
    s3_handler.s3_client.copy_object.assert_called_once()
    s3_handler.s3_client.delete_object.assert_called_once()

def test_list_unprocessed_videos(s3_handler):
    """Test listing unprocessed videos"""
    # Mock S3 list_objects_v2 response
    mock_response = {
        'Contents': [
            {
                'Key': 'raw_videos/test1.mp4',
                'Size': 1024,
                'LastModified': '2024-01-01T00:00:00'
            },
            {
                'Key': 'raw_videos/test2.mp4',
                'Size': 2048,
                'LastModified': '2024-01-02T00:00:00'
            }
        ]
    }
    s3_handler.s3_client.list_objects_v2.return_value = mock_response
    
    # Test listing
    videos = s3_handler.list_unprocessed_videos()
    
    # Verify result
    assert len(videos) == 2
    assert all(video['key'].endswith('.mp4') for video in videos)
    assert all('size' in video for video in videos)
    assert all('last_modified' in video for video in videos)
    assert all('url' in video for video in videos)
    
    # Verify list_objects_v2 was called
    s3_handler.s3_client.list_objects_v2.assert_called_once()

def test_error_handling(s3_handler):
    """Test error handling in S3 operations"""
    # Mock S3 client to raise an exception
    s3_handler.s3_client.upload_file.side_effect = Exception('Test error')
    
    # Test upload with error
    result = s3_handler.upload_video('test.mp4')
    
    # Verify error handling
    assert result['success'] is False
    assert 'error' in result
    assert result['error'] == 'Test error' 