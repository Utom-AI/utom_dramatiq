import os
import logging
import yt_dlp
import ffmpeg

logger = logging.getLogger(__name__)

def download_video(url: str, output_path: str) -> bool:
    """
    Download video from URL using yt-dlp
    
    Args:
        url: Video URL
        output_path: Path to save the video
        
    Returns:
        bool: Success status
    """
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': output_path,
            'quiet': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        return os.path.exists(output_path)
        
    except Exception as e:
        logger.error(f"Failed to download video: {str(e)}")
        return False

def extract_audio(video_path: str, output_path: str) -> bool:
    """
    Extract audio from video using ffmpeg
    
    Args:
        video_path: Path to video file
        output_path: Path to save the audio
        
    Returns:
        bool: Success status
    """
    try:
        stream = ffmpeg.input(video_path)
        stream = ffmpeg.output(stream, output_path, acodec='pcm_s16le', ac=1, ar='16k')
        ffmpeg.run(stream, capture_stdout=True, capture_stderr=True, overwrite_output=True)
        
        return os.path.exists(output_path)
        
    except Exception as e:
        logger.error(f"Failed to extract audio: {str(e)}")
        return False 