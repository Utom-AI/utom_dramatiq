import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.results import Results
from dramatiq.results.backends import RedisBackend
import os
import logging
from sqlalchemy.orm import Session
from database import SessionLocal
from models import ProcessingJob
import requests
from dotenv import load_dotenv
from datetime import datetime
import json
import httpx
from typing import Dict, Any
from processors.video import VideoProcessor
from processors.transcription import transcribe_audio
from processors.action_points import extract_action_points
from dramatiq.middleware.time_limit import TimeLimitExceeded

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Redis backend for results
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
result_backend = RedisBackend(url=redis_url)

# Configure RabbitMQ broker with Results middleware
rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672")
rabbitmq_broker = RabbitmqBroker(url=rabbitmq_url)
rabbitmq_broker.add_middleware(Results(backend=result_backend))
dramatiq.set_broker(rabbitmq_broker)

# Initialize video processor
video_processor = VideoProcessor()

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

@dramatiq.actor(
    queue_name="video_processing",
    max_retries=3,
    time_limit=1800000,  # 30 minutes
    min_backoff=1000,    # 1 second
    max_backoff=30000,   # 30 seconds
    retry_when=lambda exc: isinstance(exc, TimeLimitExceeded)
)
def process_video(job_id: int, video_url: str, webhook_url: str = None) -> Dict[str, Any]:
    """Process a video and send results via webhook if URL is provided."""
    logger.info(f"Starting video processing for job {job_id}")
    logger.info(f"Processing video for job {job_id}: {video_url}")
    
    video_path = None
    audio_path = None
    
    try:
        # Update job status to processing
        with SessionLocal() as db:
            job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            if job:
                job.status = "processing"
                db.commit()
        
        # Process video using VideoProcessor
        video_result = video_processor.process_video(video_url)
        if not video_result.get("success", False):
            raise Exception(video_result.get("error", "Failed to process video"))
        
        video_path = video_result["video_path"]
        audio_path = video_result["audio_path"]
        
        # Transcribe audio
        logger.info(f"Step 3: Transcribing audio with Whisper...")
        transcription = transcribe_audio(audio_path)
        
        # Extract action points
        logger.info("Step 4: Extracting action points from transcription...")
        action_points = extract_action_points(transcription)
        
        # Prepare results
        results = {
            "transcription": transcription,
            "action_points": action_points
        }
        
        # Update job status and results
        with SessionLocal() as db:
            job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            if job:
                job.status = "completed"
                job.transcription = transcription
                job.action_points = json.dumps(action_points)
                db.commit()
        
        # Send webhook if URL is provided
        if webhook_url:
            try:
                with httpx.Client() as client:
                    response = client.post(
                        webhook_url,
                        json={
                            "job_id": job_id,
                            "status": "completed",
                            "results": results
                        },
                        timeout=30.0
                    )
                    response.raise_for_status()
                    logger.info(f"Successfully sent webhook for job {job_id}")
            except Exception as e:
                logger.error(f"Failed to send webhook for job {job_id}: {str(e)}")
        
        logger.info(f"Job {job_id} completed successfully")
        return results
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        
        # Update job status to failed
        with SessionLocal() as db:
            job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.error_message = str(e)
                db.commit()
        
        # Send webhook with error if URL is provided
        if webhook_url:
            try:
                with httpx.Client() as client:
                    response = client.post(
                        webhook_url,
                        json={
                            "job_id": job_id,
                            "status": "failed",
                            "error": str(e)
                        },
                        timeout=30.0
                    )
                    response.raise_for_status()
            except Exception as webhook_error:
                logger.error(f"Failed to send error webhook for job {job_id}: {str(webhook_error)}")
        
        raise
    finally:
        # Only clean up files if we have both paths and the job was successful
        if video_path and audio_path and job and job.status == "completed":
            try:
                video_processor.cleanup(video_path, audio_path)
                logger.info(f"Successfully cleaned up temporary files for job {job_id}")
            except Exception as e:
                logger.error(f"Failed to clean up temporary files for job {job_id}: {str(e)}") 