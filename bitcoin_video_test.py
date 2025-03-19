import os
import sys
import numpy as np
import cv2
from datetime import datetime
import boto3
import logging
from pathlib import Path
import json
from dotenv import load_dotenv
from gtts import gTTS
import moviepy.editor as mp
from moviepy.editor import VideoFileClip, AudioFileClip
import uuid
from pymongo import MongoClient
import openai
from video_processor import process_video
from utom_feature.processors.action_points import extract_action_points, format_action_points

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DB_NAME = 'video_processor'
COLLECTION_NAME = 'video_metadata'

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

def get_mongodb_client():
    """Get MongoDB client instance"""
    return MongoClient(MONGODB_URI)

def create_bitcoin_script():
    """Create a concise, information-rich script about Bitcoin"""
    return """
    Bitcoin is revolutionizing finance, and here's why you should pay attention:
    
    First, Bitcoin provides unmatched financial freedom. It's decentralized, secure, and operates 24/7 without intermediaries.
    
    Second, its growth potential is extraordinary. From $0.01 in 2009 to over $60,000 at its peak, Bitcoin has outperformed traditional assets.
    
    Third, major institutions, including banks and tech companies, are now embracing cryptocurrency.
    
    Key investment considerations: Start small, diversify your portfolio, secure your assets with hardware wallets,
    and stay informed about market trends. Remember, while the potential is significant, invest responsibly and within your means.
    
    The future of finance is digital, and Bitcoin is leading this transformation. Consider joining the cryptocurrency revolution today.
    """

def create_test_video(output_path: str, duration: int = 60):
    """Create a test video with Bitcoin content"""
    try:
        logger.info("Starting video creation process...")
        
        # Create narration audio
        logger.info("Generating narration audio...")
        script = create_bitcoin_script()
        tts = gTTS(text=script, lang='en', slow=False)
        audio_path = os.path.join(os.path.dirname(output_path), "narration.mp3")
        tts.save(audio_path)
        logger.info(f"Saved narration to {audio_path}")
        
        # Video settings
        width, height = 1280, 720
        fps = 30
        total_frames = duration * fps
        
        logger.info(f"Generating {total_frames} frames at {width}x{height} resolution...")
        frames = []
        for i in range(total_frames):
            if i % fps == 0:
                logger.info(f"Processing frame {i}/{total_frames} ({i/total_frames*100:.1f}%)")
            
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Simplified gradient background
            bg_color = [
                int(40 + 20 * np.sin(i/fps)),
                int(40 + 20 * np.cos(i/fps)),
                int(60 + 20 * np.sin(i/fps))
            ]
            frame[:] = bg_color
            
            # Draw Bitcoin logo with dynamic effects
            center_x, center_y = width//2, height//2
            radius = 100 + int(10 * np.sin(i/fps * 2))  # Pulsing effect
            
            # Draw the ₿ symbol with glowing effect
            glow_color = (0, int(165 + 90 * np.sin(i/fps * 3)), 255)
            cv2.circle(frame, (center_x, center_y), radius, glow_color, 3)
            cv2.putText(frame, '₿', (center_x-30, center_y+30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 3, glow_color, 3)
            
            # Add dynamic price chart
            chart_height = 150
            for x in range(20):
                x1 = int(width/4 + x * 30)
                y1 = int(height/4 + chart_height * np.sin(i/fps + x/5))
                x2 = int(width/4 + (x+1) * 30)
                y2 = int(height/4 + chart_height * np.sin(i/fps + (x+1)/5))
                cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Add key statistics
            stats = [
                f"Market Cap: ${int(800 + 100 * np.sin(i/fps)):,}B",
                f"24h Volume: ${int(50 + 10 * np.cos(i/fps)):,}B",
                f"Growth: {int(1000 + 100 * np.sin(i/fps))}%"
            ]
            
            for idx, stat in enumerate(stats):
                cv2.putText(frame, stat, (50, height-150+idx*40), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Add title and subtitle
            title = "Cryptocurrency: The Future of Finance"
            subtitle = "Investment Insights"
            
            # Get text sizes
            title_size = cv2.getTextSize(title, cv2.FONT_HERSHEY_TRIPLEX, 1.5, 2)[0]
            subtitle_size = cv2.getTextSize(subtitle, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
            
            # Calculate positions to center the text
            title_x = (width - title_size[0]) // 2
            subtitle_x = (width - subtitle_size[0]) // 2
            
            # Add text with shadow effect
            cv2.putText(frame, title, (title_x+2, 82), 
                       cv2.FONT_HERSHEY_TRIPLEX, 1.5, (0, 0, 0), 2)
            cv2.putText(frame, title, (title_x, 80), 
                       cv2.FONT_HERSHEY_TRIPLEX, 1.5, (255, 255, 255), 2)
            
            cv2.putText(frame, subtitle, (subtitle_x+2, 132), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            cv2.putText(frame, subtitle, (subtitle_x, 130), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            frames.append(frame)
        
        logger.info("Frame generation complete. Creating video clip...")
        
        try:
            video_clip = mp.ImageSequenceClip(frames, fps=fps)
            logger.info("Created video clip successfully")
            
            logger.info("Loading audio clip...")
            audio_clip = mp.AudioFileClip(audio_path)
            logger.info("Audio clip loaded successfully")
            
            logger.info("Combining video and audio...")
            final_clip = video_clip.set_audio(audio_clip)
            
            logger.info(f"Writing final video to {output_path}...")
            final_clip.write_videofile(output_path, 
                                     codec='libx264', 
                                     audio_codec='aac',
                                     preset='faster',
                                     threads=4,
                                     logger=None)
            
            logger.info("Video creation completed successfully")
            
            # Cleanup
            logger.info("Cleaning up resources...")
            audio_clip.close()
            video_clip.close()
            final_clip.close()
            os.remove(audio_path)
            logger.info("Cleanup completed")
            
            return True
            
        except Exception as inner_e:
            logger.error(f"Error during video processing: {str(inner_e)}")
            raise
            
    except Exception as e:
        logger.error(f"Error creating video: {str(e)}")
        return False

def upload_to_s3(file_path: str, bucket: str, key: str) -> bool:
    """Upload file to S3"""
    try:
        s3_client = boto3.client('s3',
            aws_access_key_id=os.getenv('s3_access_key'),
            aws_secret_access_key=os.getenv('s3_secret_key'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        s3_client.upload_file(file_path, bucket, key)
        logger.info(f"Uploaded {file_path} to s3://{bucket}/{key}")
        return True
    except Exception as e:
        logger.error(f"Error uploading to S3: {str(e)}")
        return False

def extract_audio(video_path: str) -> str:
    """Extract audio from video file"""
    try:
        logger.info("Extracting audio from video...")
        output_dir = os.path.dirname(video_path)
        audio_path = os.path.join(output_dir, f"audio_{os.path.basename(video_path)}.mp3")
        
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(audio_path)
        video.close()
        
        logger.info(f"Audio extracted to {audio_path}")
        return audio_path
    except Exception as e:
        logger.error(f"Error extracting audio: {str(e)}")
        raise

def transcribe_audio(audio_path: str) -> dict:
    """Transcribe audio using OpenAI Whisper API"""
    try:
        logger.info("Transcribing audio using OpenAI Whisper...")
        with open(audio_path, "rb") as audio_file:
            client = openai.OpenAI()
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        
        logger.info("Audio transcription completed")
        return {"text": transcription.text}
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        raise

def store_video_metadata(video_path: str, bucket: str, key: str) -> dict:
    """Process video and store metadata using our existing dramatiq app functions"""
    try:
        # Get basic video info
        video = VideoFileClip(video_path)
        video_id = str(uuid.uuid4())
        video_url = f"s3://{bucket}/{key}"
        
        logger.info(f"Processing video from {video_path}")
        
        # Process video using our existing processor
        result = process_video(video_path, is_url=False)
        
        # Generate action points using our processor
        action_points_result = extract_action_points(result["transcription"])
        if not action_points_result["success"]:
            raise Exception(f"Failed to extract action points: {action_points_result['error']}")
            
        formatted_points = format_action_points(action_points_result["points"])
        if not formatted_points["success"]:
            raise Exception(f"Failed to format action points: {formatted_points['error']}")
        
        # Create metadata
        metadata = {
            "video_id": video_id,
            "filename": os.path.basename(video_path),
            "url": video_url,
            "duration": video.duration,
            "size": os.path.getsize(video_path),
            "resolution": f"{video.size[0]}x{video.size[1]}",
            "fps": video.fps,
            "status": "completed",
            "created_at": datetime.utcnow(),
            "features": {
                "transcription": result["transcription"],
                "action_points": formatted_points["tasks"],
                "summary": formatted_points["summary"]
            }
        }
        
        # Store in MongoDB
        client = get_mongodb_client()
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        collection.insert_one(metadata)
        
        # Save metadata locally
        output_dir = 'test_output'
        Path(output_dir).mkdir(exist_ok=True)
        json_path = os.path.join(output_dir, f'video_metadata_{video_id}.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        # Print the results
        logger.info("\n=== Video Processing Results ===")
        logger.info(f"Video ID: {video_id}")
        logger.info(f"Video URL: {video_url}")
        logger.info("\nTranscription:")
        logger.info(result["transcription"])
        logger.info("\nAction Points:")
        logger.info(json.dumps(formatted_points["tasks"], indent=2))
        logger.info("\nSummary:")
        logger.info(json.dumps(formatted_points["summary"], indent=2))
        logger.info("\nMetadata saved to: " + json_path)
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        raise
    finally:
        if 'video' in locals():
            video.close()
        if 'client' in locals():
            client.close()

def process_bitcoin_video(video_path: str):
    """Process the Bitcoin video using our Dramatiq app functions"""
    try:
        # Step 1: Upload to S3
        bucket = "utom-content-bucket"
        key = f'test_videos/bitcoin_video_{datetime.now().strftime("%Y%m%d_%H%M%S")}.mp4'
        
        s3_client = boto3.client('s3',
            aws_access_key_id=os.getenv('s3_access_key'),
            aws_secret_access_key=os.getenv('s3_secret_key'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        logger.info(f"Uploading video to S3...")
        s3_client.upload_file(video_path, bucket, key)
        video_url = f"s3://{bucket}/{key}"
        
        # Step 2: Process video using our existing processor
        logger.info("Processing video using Dramatiq app functions...")
        result = process_video(video_path, is_url=False)
        
        # Step 3: Generate detailed action points
        logger.info("Generating detailed action points...")
        action_points_result = extract_action_points(result["transcription"])
        if not action_points_result["success"]:
            raise Exception(f"Failed to extract action points: {action_points_result['error']}")
        
        action_points = action_points_result["points"]
        
        # Step 4: Create metadata
        metadata = {
            "video_id": f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "url": video_url,
            "filename": os.path.basename(video_path),
            "transcription": result["transcription"],
            "action_points": action_points["action_points"],
            "tasks": action_points["key_points"],
            "summary": action_points["summary"],
            "risk_assessment": action_points["risk_assessment"]
        }
        
        # Step 5: Store in MongoDB
        client = MongoClient(MONGODB_URI)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        collection.insert_one(metadata)
        
        # Save metadata locally for testing
        output_dir = 'test_output'
        Path(output_dir).mkdir(exist_ok=True)
        json_path = os.path.join(output_dir, f'video_metadata_{metadata["video_id"]}.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, default=str)
        
        # Print results
        logger.info("\n=== Video Processing Results ===")
        logger.info(f"Video ID: {metadata['video_id']}")
        logger.info(f"Video URL: {metadata['url']}")
        logger.info("\nTranscription:")
        logger.info(metadata['transcription'])
        logger.info("\nAction Points:")
        logger.info(json.dumps(metadata['action_points'], indent=2))
        logger.info("\nTasks:")
        logger.info(json.dumps(metadata['tasks'], indent=2))
        logger.info("\nSummary:")
        logger.info(metadata['summary'])
        logger.info("\nMetadata saved to: " + json_path)
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}")
        raise

def main():
    try:
        logger.info("=== Starting Bitcoin Video Test ===")
        
        # Create output directory
        output_dir = Path('test_output')
        output_dir.mkdir(exist_ok=True)
        
        # Create test video
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        video_path = str(output_dir / f'bitcoin_video_{timestamp}.mp4')
        
        if not create_test_video(video_path):
            raise Exception("Failed to create test video")
        
        # Process video using our Dramatiq app functions
        bucket = "utom-content-bucket"
        key = f'test_videos/bitcoin_video_{timestamp}.mp4'
        metadata = store_video_metadata(video_path, bucket, key)
        
        logger.info("=== Test completed successfully! ===")
        logger.info(f"Video ID: {metadata['video_id']}")
        logger.info(f"Metadata saved to: test_output/video_metadata_{metadata['video_id']}.json")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    main() 