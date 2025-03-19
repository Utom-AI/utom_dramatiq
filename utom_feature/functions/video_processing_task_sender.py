import os
import sys
import json
import time
import uuid
from typing import Dict, Any, Optional
from utom_utils.functions import env_utils
from utom_databases.functions import mongo_utils as mongo
from utom_databases.functions import rabbitmq_utils as rabbit_mq

def send_video_processing_task(video_url: str, webhook_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Send a video processing task to the queue
    
    Args:
        video_url (str): URL of the video to process
        webhook_url (Optional[str]): URL to send results to when complete
        
    Returns:
        dict: Contains task_id and status
    """
    try:
        # Load environment variables
        env_utils.load_in_env_vars()
        
        # Initialize MongoDB client
        mongo_client = mongo.initialise_mongo_cloud_db_client()
        
        # Generate task ID and timestamp
        task_id = str(uuid.uuid4())
        task_send_time = int(time.time())
        
        # Prepare task message
        task_message = {
            "task_id": task_id,
            "task_send_time": task_send_time,
            "video_url": video_url,
            "webhook_url": webhook_url
        }
        
        # Convert to JSON string
        task_message_json = json.dumps(task_message)
        
        # Get MongoDB collection names
        task_log_service_mongo_db_name = 'utom_video_processing_db'
        task_logs_collection_name = 'video_task_logs'
        
        # Create task log entry
        task_log = {
            "task_id": task_id,
            "task_send_time": task_send_time,
            "task_status": "sent",
            "video_url": video_url,
            "webhook_url": webhook_url
        }
        
        # Insert task log into MongoDB
        mongo.insert_document_into_mongo(mongo_client, task_log_service_mongo_db_name, task_logs_collection_name, task_log)
        
        # Initialize RabbitMQ channel
        channel = rabbit_mq.initialize_rabbitmq_client_and_create_channel()
        
        # Send task to queue
        channel.basic_publish(
            exchange='',
            routing_key="utom_video_processing_task_queue",
            body=task_message_json
        )
        
        # Update task status to sent
        mongo.update_document_in_mongo_by_document_id_str(
            mongo_client,
            task_log_service_mongo_db_name,
            task_logs_collection_name,
            "task_id",
            task_id,
            {"task_status": "sent"}
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "status": "sent"
        }
        
    except Exception as e:
        print(f"Error sending video processing task: {str(e)}")
        
        # Update task status to failed if MongoDB is available
        if "mongo_client" in locals():
            try:
                mongo.update_document_in_mongo_by_document_id_str(
                    mongo_client,
                    task_log_service_mongo_db_name,
                    task_logs_collection_name,
                    "task_id",
                    task_id,
                    {
                        "task_status": "failed",
                        "error": str(e)
                    }
                )
            except:
                pass
                
        return {
            "success": False,
            "error": str(e)
        }
        
    finally:
        # Close connections
        if "mongo_client" in locals():
            mongo_client.close()
        if "channel" in locals():
            channel.close() 