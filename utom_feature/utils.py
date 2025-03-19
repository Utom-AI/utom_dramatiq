import os
from typing import Dict, Any, Optional
from utom_databases.functions.mongo_utils import (
    initialise_mongo_cloud_db_client,
    get_documents_by_filter_criteria,
    update_document_in_mongo_by_document_id_str
)
from utom_databases.functions.rabbitmq_utils import (
    initialize_rabbitmq_client_and_create_channel,
    publish_dict_to_rabbitmq_queue
)

def get_mongodb_client():
    """Get MongoDB client using organization's utilities"""
    return initialise_mongo_cloud_db_client()

def get_rabbitmq_channel():
    """Get RabbitMQ channel using organization's utilities"""
    return initialize_rabbitmq_client_and_create_channel()

def get_mongodb_collection_names() -> Dict[str, str]:
    """Get MongoDB collection names from environment variables"""
    return {
        "tasks": os.getenv("TASK_LOGS_COLLECTION_NAME", "task_logs"),
        "database": os.getenv("TASK_LOG_SERVICE_MONGO_DB_NAME", "task_log_service")
    }

def get_task_by_id(task_id: str) -> Optional[Dict[str, Any]]:
    """Get task details from MongoDB by task ID"""
    client = get_mongodb_client()
    collection_names = get_mongodb_collection_names()
    
    try:
        filter_criteria = {"task_id": task_id}
        tasks = get_documents_by_filter_criteria(
            client,
            collection_names["database"],
            collection_names["tasks"],
            filter_criteria
        )
        return tasks[0] if tasks else None
    finally:
        client.close()

def update_task_status(task_id: str, status: str, **kwargs):
    """Update task status in MongoDB"""
    client = get_mongodb_client()
    collection_names = get_mongodb_collection_names()
    
    try:
        update_data = {"status": status, **kwargs}
        update_document_in_mongo_by_document_id_str(
            client,
            collection_names["database"],
            collection_names["tasks"],
            "task_id",
            task_id,
            update_data
        )
    finally:
        client.close()

def send_task_to_queue(queue_name: str, task_data: Dict[str, Any]):
    """Send a task to RabbitMQ queue"""
    channel = get_rabbitmq_channel()
    try:
        publish_dict_to_rabbitmq_queue(channel, queue_name, task_data)
    finally:
        channel.close() 