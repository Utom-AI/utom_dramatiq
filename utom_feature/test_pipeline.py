import os
import logging
from processors.video import download_video, extract_audio, cleanup_files
from processors.transcription import transcribe_audio
from processors.action_points import extract_action_points, format_action_points

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pipeline(video_url: str):
    """
    Test the complete video processing pipeline
    
    Args:
        video_url (str): URL of the video to process
    """
    try:
        # Step 1: Download video
        logger.info("Step 1: Downloading video...")
        video_result = download_video(video_url, "temp")
        if not video_result["success"]:
            raise Exception(f"Failed to download video: {video_result.get('error')}")
            
        # Step 2: Extract audio
        logger.info("Step 2: Extracting audio...")
        audio_result = extract_audio(video_result["video_path"], "temp")
        if not audio_result:
            raise Exception("Failed to extract audio")
            
        # Step 3: Transcribe audio
        logger.info("Step 3: Transcribing audio...")
        transcription_result = transcribe_audio(audio_result)
        if not transcription_result["success"]:
            raise Exception(f"Failed to transcribe audio: {transcription_result.get('error')}")
            
        # Step 4: Extract action points
        logger.info("Step 4: Extracting action points...")
        action_points_result = extract_action_points(transcription_result)
        if not action_points_result["success"]:
            raise Exception(f"Failed to extract action points: {action_points_result.get('error')}")
            
        # Step 5: Format results
        logger.info("Step 5: Formatting results...")
        formatted_result = format_action_points(action_points_result)
        
        # Print results
        print("\nTranscription:")
        print("-" * 50)
        print(transcription_result["text"])
        print("\nAction Points and Context:")
        print("-" * 50)
        print(formatted_result)
        
        # Cleanup
        cleanup_files(video_result["video_path"], audio_result)
        
    except Exception as e:
        logger.error(f"Pipeline test failed: {str(e)}")
        raise

if __name__ == "__main__":
    # Test with a sample video URL
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Replace with your test video URL
    test_pipeline(test_url) 