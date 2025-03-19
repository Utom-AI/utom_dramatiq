import os
from pytube import YouTube
from moviepy.editor import VideoFileClip
import tempfile
import whisper
import openai
from dotenv import load_dotenv
import dramatiq
import boto3

# Load environment variables
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

# Initialize Whisper model
print("Loading Whisper model (base)...")
model = whisper.load_model("base", device="cpu")
print("Initialized Whisper model (base)")

def download_video(url: str, output_path: str = None) -> str:
    """Download video from URL"""
    if not output_path:
        output_path = tempfile.mkdtemp()
    yt = YouTube(url)
    video = yt.streams.filter(progressive=True, file_extension="mp4").first()
    return video.download(output_path)

def extract_audio(video_path: str, output_path: str = None) -> str:
    """Extract audio from video file"""
    if not output_path:
        output_path = os.path.join(os.path.dirname(video_path), "audio.wav")
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(output_path)
    video.close()
    return output_path

def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio using Whisper"""
    print(f"Transcribing audio file: {audio_path}")
    try:
        result = model.transcribe(audio_path, language="en")
        return result["text"]
    except Exception as e:
        print(f"Error during transcription: {str(e)}")
        raise

def extract_action_points(transcription: str) -> list:
    """Extract action points using OpenAI"""
    prompt = f"""
    Based on the following transcription, identify and list the key action points.
    Each action point should be something that needs to be done or followed up on.
    Format each point with:
    - The action to be taken
    - Context around why it's important
    - Priority level (High/Medium/Low)

    Transcription:
    {transcription}

    Please provide the action points in a clear, structured format.
    """
    
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an expert at analyzing transcripts and identifying actionable items."},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content

def process_video(video_input: str, is_url: bool = True) -> dict:
    """Main function to process video and extract action points"""
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Step 1: Get video file
        if is_url:
            print(f"Downloading video from {video_input}")
            video_path = download_video(video_input, temp_dir)
        else:
            video_path = video_input
            
        # Step 2: Extract audio
        print("Extracting audio from video")
        audio_path = extract_audio(video_path, os.path.join(temp_dir, "audio.wav"))
        
        # Step 3: Transcribe audio
        print("Transcribing audio")
        transcription = transcribe_audio(audio_path)
        
        # Step 4: Extract action points
        print("Extracting action points")
        action_points = extract_action_points(transcription)
        
        # Clean up temporary files
        try:
            os.remove(audio_path)
            if is_url:
                os.remove(video_path)
            os.rmdir(temp_dir)
        except:
            pass
        
        return {
            "transcription": transcription,
            "action_points": action_points
        }
        
    except Exception as e:
        print(f"Error processing video: {str(e)}")
        raise

def process_from_metadata_api(metadata_url: str = None):
    """Process video from metadata API"""
    if not metadata_url:
        metadata_url = os.getenv('METADATA_API_ENDPOINT')
    
    # Here you would add the integration with your existing metadata LLM
    # For now, this is a placeholder for that integration
    pass

@dramatiq.actor(queue_name="video_processing")
def process_video_task(video_id: str):
    """Dramatiq actor for processing videos"""
    try:
        from mongodb_utils import get_mongodb_client
        
        print(f"Starting processing for video {video_id}")
        
        # Get video metadata from MongoDB
        client = get_mongodb_client()
        db = client['video_processor']
        collection = db['video_metadata']
        
        video_metadata = collection.find_one({"video_id": video_id})
        if not video_metadata:
            raise Exception(f"No metadata found for video_id: {video_id}")
            
        # Download video from S3
        print("Downloading video from S3...")
        s3_client = boto3.client('s3',
            aws_access_key_id=os.getenv('s3_access_key'),
            aws_secret_access_key=os.getenv('s3_secret_key'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        temp_dir = tempfile.mkdtemp()
        video_path = os.path.join(temp_dir, video_metadata['filename'])
        s3_client.download_file(video_metadata['bucket'], video_metadata['key'], video_path)
        
        # Extract audio
        print("Extracting audio...")
        audio_path = extract_audio(video_path)
        
        # Transcribe audio
        print("Transcribing audio...")
        transcription = transcribe_audio(audio_path)
        print("\nTranscription result:")
        print(transcription)
        
        # Extract action points
        print("\nGenerating action points...")
        action_points = extract_action_points(transcription)
        print("\nAction points:")
        print(action_points)
        
        # Update metadata with results
        print("\nUpdating metadata in MongoDB...")
        collection.update_one(
            {"video_id": video_id},
            {
                "$set": {
                    "features.transcription": transcription,
                    "features.action_points": action_points,
                    "status": "processed"
                }
            }
        )
        
        # Clean up
        try:
            os.remove(audio_path)
            os.remove(video_path)
            os.rmdir(temp_dir)
        except:
            pass
            
        print(f"\nProcessing completed successfully for video {video_id}")
        return {"success": True, "video_id": video_id}
        
    except Exception as e:
        print(f"Error processing video task: {str(e)}")
        if 'collection' in locals():
            collection.update_one(
                {"video_id": video_id},
                {"$set": {"status": "error", "error": str(e)}}
            )
        raise
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    # Example usage - using a short TED-Ed video
    video_url = "https://www.youtube.com/watch?v=hVimVzgtD6w"  # "What would happen if you didn't sleep?" (3 mins)
    print("Processing video...")
    result = process_video(video_url)
    print("\nTranscription:")
    print(result["transcription"])
    print("\nAction Points:")
    print(result["action_points"]) 