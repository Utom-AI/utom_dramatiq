import os
import pytest
import tempfile
from unittest.mock import Mock, patch
from utom_feature.processors.s3_processor import process_s3_video, handle_s3_notification
from utom_feature.processors.video import process_video
from utom_feature.processors.transcription import transcribe_audio

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
def mock_s3_handler():
    """Create a mock S3 handler"""
    with patch('utom_feature.processors.s3_processor.S3Handler') as mock:
        handler = Mock()
        mock.return_value = handler
        yield handler

def test_process_s3_video_success(mock_s3_event, mock_s3_handler):
    """Test successful video processing"""
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock successful operations
        mock_s3_handler.download_video.return_value = {
            'success': True,
            'local_path': os.path.join(temp_dir, 'video.mp4')
        }
        
        process_video.return_value = {
            'success': True,
            'audio_path': os.path.join(temp_dir, 'audio.wav')
        }
        
        transcribe_audio.return_value = {
            'success': True,
            'text': 'Test transcription'
        }
        
        mock_s3_handler.move_to_processed.return_value = {
            'success': True,
            'new_key': 'processed_videos/test.mp4'
        }
        
        # Test processing
        result = process_s3_video(mock_s3_event)
        
        # Verify result
        assert result['success'] is True
        assert result['transcription'] == 'Test transcription'
        assert result['processed_video_key'] == 'processed_videos/test.mp4'
        
        # Verify operations were called
        mock_s3_handler.download_video.assert_called_once()
        process_video.assert_called_once()
        transcribe_audio.assert_called_once()
        mock_s3_handler.move_to_processed.assert_called_once()

def test_process_s3_video_download_failure(mock_s3_event, mock_s3_handler):
    """Test video processing with download failure"""
    # Mock download failure
    mock_s3_handler.download_video.return_value = {
        'success': False,
        'error': 'Download failed'
    }
    
    # Test processing
    result = process_s3_video(mock_s3_event)
    
    # Verify result
    assert result['success'] is False
    assert result['error'] == 'Failed to download video'
    
    # Verify move to failed was called
    mock_s3_handler.move_to_failed.assert_called_once()

def test_process_s3_video_processing_failure(mock_s3_event, mock_s3_handler):
    """Test video processing with processing failure"""
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock successful download but failed processing
        mock_s3_handler.download_video.return_value = {
            'success': True,
            'local_path': os.path.join(temp_dir, 'video.mp4')
        }
        
        process_video.return_value = {
            'success': False,
            'error': 'Processing failed'
        }
        
        # Test processing
        result = process_s3_video(mock_s3_event)
        
        # Verify result
        assert result['success'] is False
        assert result['error'] == 'Processing failed'
        
        # Verify move to failed was called
        mock_s3_handler.move_to_failed.assert_called_once()

def test_process_s3_video_transcription_failure(mock_s3_event, mock_s3_handler):
    """Test video processing with transcription failure"""
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock successful download and processing but failed transcription
        mock_s3_handler.download_video.return_value = {
            'success': True,
            'local_path': os.path.join(temp_dir, 'video.mp4')
        }
        
        process_video.return_value = {
            'success': True,
            'audio_path': os.path.join(temp_dir, 'audio.wav')
        }
        
        transcribe_audio.return_value = {
            'success': False,
            'error': 'Transcription failed'
        }
        
        # Test processing
        result = process_s3_video(mock_s3_event)
        
        # Verify result
        assert result['success'] is False
        assert result['error'] == 'Transcription failed'
        
        # Verify move to failed was called
        mock_s3_handler.move_to_failed.assert_called_once()

def test_handle_s3_notification_success(mock_s3_event):
    """Test successful notification handling"""
    with patch('utom_feature.processors.s3_processor.process_s3_video') as mock_process:
        # Mock successful processing
        mock_process.return_value = {
            'success': True,
            'transcription': 'Test transcription',
            'processed_video_key': 'processed_videos/test.mp4'
        }
        
        # Test notification handling
        result = handle_s3_notification(mock_s3_event)
        
        # Verify result
        assert result['success'] is True
        assert result['transcription'] == 'Test transcription'
        assert result['processed_video_key'] == 'processed_videos/test.mp4'

def test_handle_s3_notification_invalid_event():
    """Test notification handling with invalid event"""
    # Test with invalid event
    result = handle_s3_notification({})
    
    # Verify result
    assert result['success'] is False
    assert result['error'] == 'Invalid event format'

def test_handle_s3_notification_processing_failure(mock_s3_event):
    """Test notification handling with processing failure"""
    with patch('utom_feature.processors.s3_processor.process_s3_video') as mock_process:
        # Mock failed processing
        mock_process.return_value = {
            'success': False,
            'error': 'Processing failed'
        }
        
        # Test notification handling
        result = handle_s3_notification(mock_s3_event)
        
        # Verify result
        assert result['success'] is False
        assert result['error'] == 'Processing failed' 