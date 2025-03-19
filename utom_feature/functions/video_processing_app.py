import os
import sys
import json
import logging
import warnings
from typing import Dict, Any, Optional
import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.results import Results
from dramatiq.results.backends import RedisBackend
from datetime import datetime

from utom_utils import get_mongodb_client, get_rabbitmq_channel
from utom_databases import get_mongodb_collection_names
from utom_feature.processors.video import process_video, cleanup_files
from utom_feature.processors.transcription import transcribe_audio
from utom_feature.processors.action_points import extract_action_points, format_action_points

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress specific warnings
warnings.filterwarnings("ignore", category=UserWarning, module="whisper")
warnings.filterwarnings("ignore", category=FutureWarning, module="pandas")

# Initialize RabbitMQ broker
rabbitmq_broker = RabbitmqBroker(
    host=os.getenv("RABBITMQ_HOST", "localhost"),
    port=int(os.getenv("RABBITMQ_PORT", "5672")),
    credentials=dramatiq.Credentials(
        username=os.getenv("RABBITMQ_USER", "guest"),
        password=os.getenv("RABBITMQ_PASSWORD", "guest")
    )
)

# Add Results middleware
redis_backend = RedisBackend(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    db=0
)
rabbitmq_broker.add_middleware(Results(backend=redis_backend))

dramatiq.set_broker(rabbitmq_broker)

@dramatiq.actor(queue_name="video_processing_queue")
def process_video_task(task_id: str) -> Dict[str, Any]:
    """Process a video task: download video, extract audio, transcribe, and identify action points"""
    try:
        # Get MongoDB client and collection names
        mongodb_client = get_mongodb_client()
        collection_names = get_mongodb_collection_names()
        tasks_collection = mongodb_client[collection_names["tasks"]]
        
        # Get task details
        task = tasks_collection.find_one({"task_id": task_id})
        if not task:
            raise ValueError(f"Task not found: {task_id}")
            
        # Check if task can be processed
        if task.get("status") not in ["pending", "retry"]:
            logger.warning(f"Task {task_id} is not in a processable state")
            return {"success": False, "error": "Task not in processable state"}
            
        # Update task status
        tasks_collection.update_one(
            {"task_id": task_id},
            {"$set": {"status": "processing"}}
        )
        
        # Process video
        video_url = task.get("video_url")
        if not video_url:
            raise ValueError("No video URL provided in task")
            
        video_result = process_video(video_url)
        if not video_result.get("success"):
            raise Exception(video_result.get("error", "Failed to process video"))
            
        video_path = video_result["video_path"]
        audio_path = video_result["audio_path"]
        
        try:
            # Transcribe audio
            transcription_result = transcribe_audio(audio_path)
            if not transcription_result.get("success"):
                raise Exception(transcription_result.get("error", "Failed to transcribe audio"))
                
            # Extract action points
            action_points_result = extract_action_points(transcription_result)
            if not action_points_result.get("success"):
                raise Exception(action_points_result.get("error", "Failed to extract action points"))
                
            # Format results
            formatted_points = format_action_points(action_points_result)
            
            # Update task with results
            tasks_collection.update_one(
                {"task_id": task_id},
                {
                    "$set": {
                        "status": "completed",
                        "results": {
                            "transcription": transcription_result["text"],
                            "action_points": action_points_result["action_points"],
                            "context_points": action_points_result["context_points"],
                            "formatted_output": formatted_points
                        },
                        "completed_at": datetime.utcnow()
                    }
                }
            )
            
            return {
                "success": True,
                "task_id": task_id,
                "results": {
                    "transcription": transcription_result["text"],
                    "action_points": action_points_result["action_points"],
                    "context_points": action_points_result["context_points"],
                    "formatted_output": formatted_points
                }
            }
            
        finally:
            # Clean up temporary files
            cleanup_files(video_path, audio_path)
            
    except Exception as e:
        logger.error(f"Error processing video task {task_id}: {str(e)}")
        
        # Update task status to failed
        if "tasks_collection" in locals():
            tasks_collection.update_one(
                {"task_id": task_id},
                {
                    "$set": {
                        "status": "failed",
                        "error": str(e),
                        "failed_at": datetime.utcnow()
                    }
                }
            )
            
        return {"success": False, "error": str(e)}
        
    finally:
        # Close MongoDB connection
        if "mongodb_client" in locals():
            mongodb_client.close()

"""
Running
dramatiq --processes 2 --threads 1 video_processing_app

The above will spin up 2 single threads processes (essentially just 2 workers)... adjust this as needed based on how many things you want running concurrently
""" 