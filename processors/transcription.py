import whisper
import logging
import torch
import os
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the model once as a global variable since it's expensive to load
device = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device: {device}")

try:
    model = whisper.load_model("base", device=device)
    logger.info("Initialized Whisper model (base)")
except Exception as e:
    logger.error(f"Failed to load Whisper model: {str(e)}")
    raise

def transcribe_audio(audio_path: str) -> Optional[str]:
    """Transcribe audio file and return transcription text"""
    try:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
        file_size = os.path.getsize(audio_path)
        if file_size == 0:
            raise ValueError("Audio file is empty")
            
        logger.info(f"Starting transcription of audio file: {audio_path} ({file_size} bytes)")
        
        # Transcribe with error handling
        try:
            result = model.transcribe(
                audio_path,
                language="en",
                fp16=False,
                task="transcribe",
                verbose=False
            )
        except Exception as e:
            logger.error(f"Whisper transcription failed: {str(e)}")
            raise
        
        # Validate and clean transcription
        if not result or "text" not in result:
            raise ValueError("Transcription result is invalid")
            
        transcription = result["text"].strip()
        if not transcription:
            raise ValueError("Transcription is empty")
            
        # Log success with character count and preview
        char_count = len(transcription)
        preview = transcription[:100] + "..." if len(transcription) > 100 else transcription
        logger.info(f"Transcription completed: {char_count} characters")
        logger.info(f"Preview: {preview}")
        
        return transcription
        
    except Exception as e:
        logger.error(f"Error during transcription: {str(e)}")
        # Return None instead of raising to allow the process to continue
        return None 