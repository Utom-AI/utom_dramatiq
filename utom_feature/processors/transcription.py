import os
from openai import OpenAI
import logging
from typing import Dict, Any

# Configure logging to match organization's style
logger = logging.getLogger(__name__)

def transcribe_audio(audio_path: str) -> Dict[str, Any]:
    """
    Transcribe audio using OpenAI Whisper API
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        dict: Contains success status and transcription text
    """
    try:
        # Get OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
            
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Open audio file and transcribe using Whisper API
        logger.info(f"Transcribing audio file: {audio_path}")
        with open(audio_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
        
        # Extract transcription text and metadata
        transcription = {
            "success": True,
            "text": response.text,
            "language": getattr(response, 'language', 'unknown'),
            "duration": getattr(response, 'duration', 0),
            "segments": getattr(response, 'segments', [])
        }
        
        logger.info(f"Successfully transcribed {len(transcription['text'])} characters")
        return transcription
        
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        } 