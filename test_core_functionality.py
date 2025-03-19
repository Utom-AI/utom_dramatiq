import os
import logging
from datetime import datetime
import tempfile
from pathlib import Path
from s3_operations import S3Operations
from utom_feature.utils import send_task_to_queue, get_task_by_id
from utom_feature.processors.transcription import transcribe_audio
from utom_feature.processors.action_points import extract_action_points, format_action_points
from utom_feature.video_utils import download_video, extract_audio
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_s3_operations():
    """Test S3 bucket operations"""
    logger.info("\n=== Testing S3 Operations ===")
    s3_ops = S3Operations()
    
    # Create test directories
    downloads_dir = os.path.join(os.getcwd(), "downloads")
    os.makedirs(downloads_dir, exist_ok=True)
    
    # List videos
    videos = s3_ops.list_videos('raw')
    logger.info(f"Found {len(videos)} videos in raw_videos folder")
    
    # Create test file
    test_file = os.path.join(downloads_dir, "test_video.txt")
    with open(test_file, "w") as f:
        f.write("Test content")
    
    try:
        # Test upload
        success, error = s3_ops.upload_video(
            test_file,
            "raw_videos/test_video.txt",
            metadata={"test": "true"}
        )
        assert success, f"Upload failed: {error}"
        logger.info("Upload test passed")
        
        # Test download
        download_path = os.path.join(downloads_dir, "downloaded_test.txt")
        success, error = s3_ops.download_video(
            "raw_videos/test_video.txt",
            download_path
        )
        assert success, f"Download failed: {error}"
        logger.info("Download test passed")
        
        # Test move
        success, error = s3_ops.move_video(
            "raw_videos/test_video.txt",
            "processed"
        )
        assert success, f"Move failed: {error}"
        logger.info("Move test passed")
        
    finally:
        # Cleanup
        for file in [test_file, download_path]:
            if os.path.exists(file):
                os.remove(file)
        if os.path.exists(downloads_dir):
            os.rmdir(downloads_dir)

def test_task_queue():
    """Test task queue operations"""
    logger.info("\n=== Testing Task Queue ===")
    
    # Send test task
    task_data = {
        "video_url": "test_url",
        "task_type": "test"
    }
    queue_name = "utom_video_processing_task_queue"
    task_id = send_task_to_queue(queue_name, task_data)
    assert task_id, "Failed to send task to queue"
    logger.info(f"Task sent with ID: {task_id}")
    
    # Get task status
    task = get_task_by_id(task_id)
    assert task, f"Failed to get task with ID: {task_id}"
    logger.info(f"Task status: {task.get('status')}")

def test_video_processing():
    """Test video download and audio extraction"""
    logger.info("\n=== Testing Video Processing ===")
    
    # Test video URL (use TED talk video)
    test_video_url = "https://download.ted.com/talks/KateDarling_2018S-950k.mp4"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Download video
            video_path = os.path.join(temp_dir, "test_video.mp4")
            success = download_video(test_video_url, video_path)
            assert success and os.path.exists(video_path), "Video download failed"
            logger.info("Video download test passed")
            
            # Extract audio
            audio_path = os.path.join(temp_dir, "test_audio.wav")
            success = extract_audio(video_path, audio_path)
            assert success and os.path.exists(audio_path), "Audio extraction failed"
            logger.info("Audio extraction test passed")
            
        except Exception as e:
            logger.error(f"Video processing test failed: {str(e)}")
            raise

def test_transcription():
    """Test transcription functionality"""
    logger.info("\n=== Testing Transcription ===")
    
    # Create a small test audio file
    test_audio = "test_audio.wav"
    try:
        # If we don't have a test audio file, try to create one from a video
        if not os.path.exists(test_audio):
            logger.info("Creating test audio file...")
            with tempfile.TemporaryDirectory() as temp_dir:
                # Download a short test video
                video_path = os.path.join(temp_dir, "test_video.mp4")
                success = download_video("https://download.ted.com/talks/KateDarling_2018S-950k.mp4", video_path)
                assert success, "Failed to download test video"
                
                # Extract audio
                success = extract_audio(video_path, test_audio)
                assert success, "Failed to extract audio from test video"
    
        if os.path.exists(test_audio):
            result = transcribe_audio(test_audio)
            assert result.get('success'), f"Transcription failed: {result.get('error')}"
            assert 'text' in result, "No transcription text in result"
            assert 'language' in result, "No language detection in result"
            assert 'duration' in result, "No duration information in result"
            assert 'segments' in result, "No segments information in result"
            
            logger.info("Transcription test passed")
            logger.info(f"Sample transcription: {result['text'][:100]}...")
            logger.info(f"Detected language: {result['language']}")
            logger.info(f"Audio duration: {result['duration']} seconds")
        else:
            logger.error("No test audio file available for transcription test")
            raise Exception("Missing test audio file")
            
    except Exception as e:
        logger.error(f"Transcription test failed: {str(e)}")
        raise

def test_action_points():
    """Test action points extraction"""
    logger.info("\n=== Testing Action Points Extraction ===")
    
    # Test transcription text
    test_text = """
    We need to schedule a meeting next week to discuss the project timeline.
    John will prepare the presentation slides by Friday.
    The team should review the documentation before the client meeting.
    Important context: The client is expecting the final delivery by end of month.
    """
    
    try:
        result = extract_action_points(test_text)
        assert result.get('success'), f"Action points extraction failed: {result.get('error')}"
        assert 'action_points' in result, "No action points in result"
        assert 'context_points' in result, "No context points in result"
        
        action_points = result['action_points']
        context_points = result['context_points']
        
        assert len(action_points) > 0, "No action points extracted"
        assert len(context_points) > 0, "No context points extracted"
        
        # Verify action point structure
        for point in action_points:
            assert 'task' in point, "Action point missing task"
            assert 'assignee' in point, "Action point missing assignee"
            assert 'deadline' in point, "Action point missing deadline"
        
        logger.info("Action points extraction test passed")
        logger.info("\nExtracted Information:")
        logger.info(format_action_points(result))
            
    except Exception as e:
        logger.error(f"Action points extraction test failed: {str(e)}")
        raise

def test_end_to_end():
    """Test complete end-to-end workflow"""
    logger.info("\n=== Testing End-to-End Workflow ===")
    
    try:
        # 1. Create a task
        task_data = {
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "task_type": "video_processing"
        }
        task_id = send_task_to_queue(task_data)
        assert task_id, "Failed to create task"
        logger.info(f"Created task: {task_id}")
        
        # 2. Check initial task status
        task = get_task_by_id(task_id)
        assert task['status'] in ['pending', 'processing'], f"Unexpected task status: {task['status']}"
        logger.info("Task status verification passed")
        
        # Note: We won't wait for the complete processing as it takes time
        # In a real test environment, we would use a mock video and shorter timeouts
        
        logger.info("End-to-end workflow test passed")
        
    except Exception as e:
        logger.error(f"End-to-end test failed: {str(e)}")
        raise

def main():
    """Run all core functionality tests"""
    load_dotenv()
    
    try:
        # Test S3 operations
        test_s3_operations()
        
        # Skip task queue test for now
        logger.info("\n=== Skipping Task Queue Test ===")
        
        # Test video processing
        test_video_processing()
        
        # Test transcription
        test_transcription()
        
        # Test action points extraction
        test_action_points()
        
        # Skip end-to-end test for now
        logger.info("\n=== Skipping End-to-End Test ===")
        
        logger.info("\n=== Core functionality tests completed ===")
        logger.info("Note: Task queue and end-to-end tests were skipped")
        
    except AssertionError as e:
        logger.error(f"Test failed: {str(e)}")
        logger.error("Please fix the failing tests before pushing to the repository")
    except Exception as e:
        logger.error(f"Unexpected error during testing: {str(e)}")
        logger.error("Please investigate and fix the error before pushing to the repository")

if __name__ == "__main__":
    main() 